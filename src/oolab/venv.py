import re
import tempfile
from pathlib import Path

from rich.console import Console

from oolab.config import WorkspaceConfig, get_venv_python
from oolab.utils import run_cmd
from oolab.versions import get_branch_name

console = Console()

# Packages that must always be installed regardless of requirements.txt
# psycopg2-binary bundles libpq — no system headers needed
CORE_PACKAGES = [
    "psycopg2-binary",
    "wheel",
    "lxml-html-clean",  # required by lxml>=5.0; harmless on lxml<5
]

# Packages that, if present in requirements.txt as source builds,
# should be replaced with their binary equivalent
BINARY_ALTERNATIVES = {
    "psycopg2": "psycopg2-binary",
}

# Full version overrides: replaces ALL lines for a package (any version/marker)
# with a single compatible spec. Needed because Odoo's requirements.txt pins
# versions that target Ubuntu Linux and don't have wheels for macOS/arm64.
#
# Rules:
# - cryptography==2.6.1 has no wheel on macOS → use >=41,<42
#   (42.0.0 removed cryptography.hazmat.backends.openssl.x509 used by urllib3==1.26)
# - pyopenssl==19.0.0 + cryptography>=37 breaks → use >=23.2.0
# - gevent/greenlet/lxml/Pillow/reportlab/psycopg2: old pins have no arm64 wheel
VERSION_FIXES: dict[str, str] = {
    "cryptography": "cryptography>=41.0.0,<42.0.0",
    "pyopenssl": "pyOpenSSL>=23.2.0",
    # urllib3 1.x uses cryptography.hazmat.backends.openssl.x509._Certificate (removed in >=38)
    # urllib3 2.x rewrote the pyopenssl integration — no longer uses the private API
    "urllib3": "urllib3>=2.0.0",
    "requests": "requests>=2.28.0",  # compatible with urllib3>=2.0
    "gevent": "gevent>=22.10.2",
    "greenlet": "greenlet>=2.0.0",
    "lxml": "lxml>=4.9.0,<5.0",  # 5.0 removed lxml.html.clean (Odoo 15/16/17 need it)
    "Pillow": "Pillow>=9.5.0",
    "reportlab": "reportlab>=3.6.12",
    "psycopg2": "psycopg2-binary",
}

# Critical imports to verify after install — maps import name to pip package
CRITICAL_IMPORTS = {
    "psycopg2": "psycopg2-binary",
    "PIL": "Pillow",
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

    # Replace source-build packages with binary equivalents (keep version constraint)
    for src, binary in BINARY_ALTERNATIVES.items():
        content = re.sub(
            rf"^{re.escape(src)}(\s*[>=<~!].*)?$",
            lambda m, b=binary: f"{b}{m.group(1) or ''}",
            content,
            flags=re.MULTILINE,
        )

    # Replace all lines for a package with a fixed spec (ignores original version/markers)
    for pkg, replacement in VERSION_FIXES.items():
        content = re.sub(
            rf"^{re.escape(pkg)}[^\n]*$",
            replacement,
            content,
            flags=re.MULTILINE | re.IGNORECASE,
        )
        # If the package wasn't in requirements.txt at all, add it at the end
        if not re.search(
            rf"^{re.escape(replacement.split('>=')[0].split('==')[0])}",
            content,
            re.MULTILINE | re.IGNORECASE,
        ):
            content += f"\n{replacement}\n"

    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
    tmp.write(content)
    tmp.close()
    return Path(tmp.name)


def _pip_install(requirements: Path, python_bin: Path, label: str) -> bool:
    patched = _make_patched_requirements(requirements)
    try:
        result = run_cmd(
            ["uv", "pip", "install", "-r", str(patched), "--python", str(python_bin)],
            timeout=600,
        )
        if result.returncode == 0:
            return True
        if result.stderr.strip():
            console.print(f"  [dim red]  {result.stderr.strip()[:300]}[/dim red]")
    finally:
        patched.unlink(missing_ok=True)

    console.print(f"  [yellow]⚠[/yellow] Instalando {label} paquete por paquete...")
    # Use patched content (VERSION_FIXES + BINARY_ALTERNATIVES already applied)
    patched2 = _make_patched_requirements(requirements)
    req_content = patched2.read_text()
    patched2.unlink(missing_ok=True)
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
                [
                    "uv",
                    "pip",
                    "install",
                    "-r",
                    str(tmp_path),
                    "--python",
                    str(python_bin),
                ],
                timeout=120,
            )
            if r.returncode != 0:
                if r.stderr.strip():
                    console.print(
                        f"  [dim red]  {pkg_name}: {r.stderr.strip()[:200]}[/dim red]"
                    )
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


def _install_core_packages(python_bin: Path) -> None:
    """Install critical packages explicitly — never rely on requirements.txt for these."""
    with console.status(
        "  Instalando paquetes core (psycopg2-binary, wheel)...", spinner="dots"
    ):
        result = run_cmd(
            ["uv", "pip", "install", *CORE_PACKAGES, "--python", str(python_bin)],
            timeout=120,
        )
    if result.returncode == 0:
        console.print("  [green]✓[/green] Paquetes core instalados")
    else:
        console.print(
            f"  [red]✗[/red] Error instalando paquetes core: {result.stderr.strip()[:300]}"
        )


def _verify_critical_packages(python_bin: Path) -> list[str]:
    """Check that critical modules can be imported. Returns list of missing ones."""
    missing = []
    for import_name, pip_name in CRITICAL_IMPORTS.items():
        result = run_cmd(
            [str(python_bin), "-c", f"import {import_name}"],
        )
        if result.returncode != 0:
            missing.append(pip_name)
    return missing


def _get_odoo_req_for_branch(odoo_path: Path, branch: str) -> Path | None:
    """Read odoo/requirements.txt for a specific branch via git show (no checkout needed).
    Returns a temp file path or None if the branch/file is not available."""
    result = run_cmd(
        ["git", "show", f"{branch}:requirements.txt"],
        cwd=str(odoo_path),
    )
    if result.returncode != 0:
        return None
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, prefix=f"odoo-req-{branch}-"
    )
    tmp.write(result.stdout)
    tmp.close()
    return Path(tmp.name)


def install_requirements(
    workspace_path: Path,
    venv_name: str,
    config: WorkspaceConfig,
    odoo_version: str | None = None,
) -> bool:
    python_bin = get_venv_python(workspace_path, venv_name)

    # 1. setuptools (needed by some legacy Odoo addons)
    run_cmd(
        ["uv", "pip", "install", "setuptools<81", "--python", str(python_bin)],
        timeout=60,
    )

    # 2. Core packages always installed explicitly — no silent failures
    _install_core_packages(python_bin)

    # 3. requirements.txt sources
    req_sources: list[tuple[Path, str]] = []
    _temp_files: list[Path] = []

    odoo_path = workspace_path / "odoo"
    if odoo_path.exists():
        if odoo_version:
            branch = get_branch_name(odoo_version)
            tmp_req = _get_odoo_req_for_branch(odoo_path, branch)
            if tmp_req:
                req_sources.append((tmp_req, f"Odoo framework ({branch})"))
                _temp_files.append(tmp_req)
            else:
                # Branch not available locally, fall back to current checkout
                odoo_req = odoo_path / "requirements.txt"
                if odoo_req.exists():
                    req_sources.append((odoo_req, "Odoo framework (checkout actual)"))
        else:
            odoo_req = odoo_path / "requirements.txt"
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

    # 4. Post-install verification — catch missing critical modules early
    missing = _verify_critical_packages(python_bin)
    if missing:
        console.print(
            f"\n  [red]✗ Módulos críticos faltantes después de instalar: {', '.join(missing)}[/red]"
        )
        console.print("  Intentando reinstalar...")
        result = run_cmd(
            ["uv", "pip", "install", *missing, "--python", str(python_bin)],
            timeout=120,
        )
        if result.returncode == 0:
            console.print(
                "  [green]✓[/green] Módulos críticos reinstalados correctamente"
            )
        else:
            console.print(
                f"  [red]✗[/red] No se pudo instalar: {', '.join(missing)}\n"
                f"  {result.stderr.strip()[:300]}"
            )
            all_ok = False

    # Cleanup temp requirement files created via git show
    for tmp in _temp_files:
        tmp.unlink(missing_ok=True)

    return all_ok
