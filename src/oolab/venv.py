import re
import tempfile
from pathlib import Path

from rich.console import Console

from oolab.config import WorkspaceConfig, get_venv_python
from oolab.utils import run_cmd

console = Console()

BINARY_ALTERNATIVES = {
    "psycopg2": "psycopg2-binary",
}


def setup_venv(workspace_path: Path, venv_name: str, python_version: str) -> bool:
    venv_path = workspace_path / venv_name
    if venv_path.exists():
        console.print(f"  [green]✓[/green] {venv_name} ya existe, reutilizando")
        return True

    with console.status(
        f"  Creando {venv_name} (Python {python_version})...", spinner="dots"
    ):
        result = run_cmd(
            ["uv", "venv", "--python", python_version, str(venv_path)],
            cwd=str(workspace_path),
        )
    if result.returncode == 0:
        console.print(
            f"  [green]✓[/green] {venv_name} creado (Python {python_version})"
        )
        return True
    else:
        console.print(f"  [red]✗[/red] Error creando venv: {result.stderr.strip()}")
        return False


def _make_patched_requirements(requirements: Path) -> Path:
    content = requirements.read_text(encoding="utf-8")
    for src, binary in BINARY_ALTERNATIVES.items():
        content = re.sub(
            rf"^{re.escape(src)}(\s*[>=<~!].*)?$",
            lambda m, b=binary: f"{b}{m.group(1) or ''}",
            content,
            flags=re.MULTILINE,
        )
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
    tmp.write(content)
    tmp.close()
    return Path(tmp.name)


def _pip_install(requirements: Path, python_bin: Path, label: str) -> bool:
    result = run_cmd(
        ["uv", "pip", "install", "-r", str(requirements), "--python", str(python_bin)],
        timeout=600,
    )
    if result.returncode == 0:
        return True

    console.print(f"  [yellow]⚠[/yellow] Reintentando {label} con paquetes binarios...")
    patched = _make_patched_requirements(requirements)
    try:
        result = run_cmd(
            ["uv", "pip", "install", "-r", str(patched), "--python", str(python_bin)],
            timeout=600,
        )
        if result.returncode == 0:
            return True
    finally:
        patched.unlink(missing_ok=True)

    console.print(f"  [yellow]⚠[/yellow] Instalando {label} paquete por paquete...")
    req_content = requirements.read_text()
    failed = []
    seen = set()

    for line in req_content.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue

        pkg_part = line.split(";")[0].split("#")[0].strip()
        pkg_name = re.split(r"[>=<!\[~]", pkg_part)[0].strip()
        if not pkg_name:
            continue

        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
        tmp.write(line + "\n")
        tmp.close()
        tmp_path = Path(tmp.name)

        try:
            r = run_cmd(
                ["uv", "pip", "install", "-r", str(tmp_path), "--python", str(python_bin)],
                timeout=120,
            )
            if r.returncode != 0:
                if pkg_name in BINARY_ALTERNATIVES:
                    alt_line = line.replace(pkg_name, BINARY_ALTERNATIVES[pkg_name])
                    tmp_path.write_text(alt_line + "\n", encoding="utf-8")
                    r2 = run_cmd(
                        ["uv", "pip", "install", "-r", str(tmp_path), "--python", str(python_bin)],
                        timeout=120,
                    )
                    if r2.returncode == 0:
                        continue
                if pkg_name not in seen:
                    failed.append(pkg_name)
                    seen.add(pkg_name)
        finally:
            tmp_path.unlink(missing_ok=True)

    if failed:
        console.print(
            f"  [yellow]⚠[/yellow] Paquetes no instalados: {', '.join(failed)}"
        )
        console.print(
            "  [dim]  Puede que necesites dependencias del sistema (libpq-dev, libldap2-dev, libsasl2-dev)[/dim]"
        )
        return False

    return True


def install_requirements(
    workspace_path: Path, venv_name: str, config: WorkspaceConfig
) -> bool:
    python_bin = get_venv_python(workspace_path, venv_name)

    run_cmd(
        ["uv", "pip", "install", "setuptools<81", "--python", str(python_bin)],
        timeout=60,
    )

    req_sources: list[tuple[Path, str]] = []

    odoo_req = workspace_path / "odoo" / "requirements.txt"
    if odoo_req.exists():
        req_sources.append((odoo_req, "Odoo framework"))

    if config.enterprise_enabled:
        ent_req = workspace_path / "enterprise" / "requirements.txt"
        if ent_req.exists():
            req_sources.append((ent_req, "Enterprise"))

    for tenant in config.tenants:
        tenant_req = workspace_path / "tenants" / tenant.name / "requirements.txt"
        if tenant_req.exists():
            req_sources.append((tenant_req, tenant.display_name))

    if not req_sources:
        console.print("  [yellow]⚠[/yellow] No se encontraron requirements.txt")
        return True

    all_ok = True
    for req_file, label in req_sources:
        with console.status(f"  Instalando dependencias de {label}...", spinner="dots"):
            ok = _pip_install(req_file, python_bin, label)
        if ok:
            console.print(f"  [green]✓[/green] Dependencias de {label} instaladas")
        else:
            all_ok = False

    return all_ok
