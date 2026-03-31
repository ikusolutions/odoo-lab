import re
import shutil
import subprocess
import tempfile
import unicodedata
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from oolab.cli import app, print_banner
from oolab.commands.doctor import DEPENDENCIES, check_dependency, offer_install_uv
from oolab.commands.generate import generate_all
from oolab.config import Tenant, WorkspaceConfig
from oolab.scaffold import scaffold_tenant
from oolab.versions import (
    available_versions,
    get_branch_name,
    get_python_version,
    get_venv_name,
    is_valid_version,
    normalize_version,
)

console = Console()

WORKSPACE_DIR_NAME = "odoo-launchpad"


def run_cmd(
    cmd: str, cwd: str | None = None, timeout: int = 600
) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout
    )


def check_system_deps() -> bool:
    """Check system dependencies, offer to install uv if missing."""
    console.print(
        "\n  [bold blue]Verificando dependencias del sistema...[/bold blue]\n"
    )
    all_ok = True

    for dep in DEPENDENCIES:
        ok, version = check_dependency(dep)
        if ok:
            console.print(
                f"  [green]✓[/green] {dep['name']} encontrado ({version.split()[-1] if version else ''})"
            )
        elif dep["name"] == "uv":
            console.print("  [yellow]⚠[/yellow] uv no encontrado")
            if not offer_install_uv():
                all_ok = False
        else:
            console.print(f"  [red]✗[/red] {dep['name']} no encontrado")
            console.print(f"    {dep['hint']}")
            all_ok = False

    return all_ok


def ask_odoo_version() -> str:
    versions = available_versions()
    versions_str = " / ".join(versions)
    while True:
        raw = Prompt.ask(
            f"\n  Versión de Odoo [{versions_str}]",
            default=versions[-1],
        )
        normalized = normalize_version(raw)
        if is_valid_version(normalized):
            python_ver = get_python_version(normalized)
            console.print(f"  [dim]→ Odoo {normalized}.0 — Python {python_ver}[/dim]")
            return normalized
        console.print(f"  [red]Versión no soportada. Opciones: {versions_str}[/red]")


def ask_enterprise() -> tuple[bool, str, str]:
    """Ask about enterprise. Returns (enabled, source, url_or_path)."""
    enabled = Confirm.ask("\n  ¿Incluir Enterprise?", default=False)
    if not enabled:
        return False, "", ""

    source = Prompt.ask(
        "  ¿Cómo obtener Enterprise?",
        choices=["git", "local"],
        default="git",
    )

    if source == "git":
        url = Prompt.ask(
            "  URL del repositorio Enterprise",
            default="git@github.com:odoo/enterprise.git",
        )
        return True, "git", url
    else:
        path = Prompt.ask("  Path local de Enterprise")
        return True, "local", path


def slugify(text: str) -> str:
    """Convert text to a URL/filesystem-safe slug."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")


def ask_first_tenant(odoo_version: str, enterprise_enabled: bool) -> Tenant | None:
    """Ask if user wants to add a first tenant project."""
    add = Confirm.ask("\n  ¿Agregar un proyecto de cliente ahora?", default=False)
    if not add:
        return None

    branch_default = get_branch_name(odoo_version)

    display_name = Prompt.ask("  Nombre del proyecto")
    name = slugify(display_name)
    console.print(f"  [dim]→ Slug: {name}[/dim]")

    is_enterprise = False
    if enterprise_enabled:
        is_enterprise = Confirm.ask("  ¿Es un proyecto Enterprise?", default=True)
    else:
        is_enterprise = Confirm.ask("  ¿Es un proyecto Enterprise?", default=False)

    clone = Confirm.ask("  ¿Clonar desde un repositorio existente?", default=True)

    if clone:
        url = Prompt.ask("  URL del repositorio")
        branch = Prompt.ask("  Branch", default=branch_default)
        return Tenant(
            name=name,
            display_name=display_name,
            url=url,
            branch=branch,
            db_filter=name,
            enterprise=is_enterprise,
        )
    else:
        return Tenant(
            name=name,
            display_name=display_name,
            url="",
            branch=branch_default,
            db_filter=name,
            enterprise=is_enterprise,
        )


def clone_repo(url: str, dest: Path, branch: str, label: str) -> bool:
    with console.status(f"  Clonando {label}...", spinner="dots"):
        result = run_cmd(
            f"git clone --depth 1 --branch {branch} {url} {dest}",
            timeout=300,
        )
    if result.returncode == 0:
        console.print(f"  [green]✓[/green] {label} clonado correctamente")
        return True
    else:
        console.print(f"  [red]✗[/red] Error clonando {label}: {result.stderr.strip()}")
        return False


def copy_local(src: str, dest: Path, label: str) -> bool:
    src_path = Path(src).expanduser().resolve()
    if not src_path.exists():
        console.print(f"  [red]✗[/red] Path no existe: {src_path}")
        return False
    with console.status(f"  Copiando {label}...", spinner="dots"):
        shutil.copytree(src_path, dest, dirs_exist_ok=True)
    console.print(f"  [green]✓[/green] {label} copiado")
    return True


def setup_venv(workspace_path: Path, venv_name: str, python_version: str) -> bool:
    venv_path = workspace_path / venv_name
    if venv_path.exists():
        console.print(f"  [green]✓[/green] {venv_name} ya existe, reutilizando")
        return True

    with console.status(
        f"  Creando {venv_name} (Python {python_version})...", spinner="dots"
    ):
        result = run_cmd(
            f"uv venv --python {python_version} {venv_path}",
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


# Packages that need C libs and have known binary wheel alternatives
BINARY_ALTERNATIVES = {
    "psycopg2": "psycopg2-binary",
}


def _make_patched_requirements(requirements: Path) -> Path:
    """Create a temp copy of requirements replacing problematic packages with binary alternatives."""
    content = requirements.read_text()
    for src, binary in BINARY_ALTERNATIVES.items():
        # Replace e.g. "psycopg2==2.9.5" with "psycopg2-binary==2.9.5"
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
    """Install a requirements file with multiple fallback strategies."""
    # Attempt 1: uv direct
    result = run_cmd(
        f"uv pip install -r {requirements} --python {python_bin}",
        timeout=600,
    )
    if result.returncode == 0:
        return True

    # Attempt 2: patched requirements (binary alternatives for problematic C packages)
    console.print(f"  [yellow]⚠[/yellow] Reintentando {label} con paquetes binarios...")
    patched = _make_patched_requirements(requirements)
    try:
        result = run_cmd(
            f"uv pip install -r {patched} --python {python_bin}",
            timeout=600,
        )
        if result.returncode == 0:
            return True
    finally:
        patched.unlink(missing_ok=True)

    # Attempt 3: line by line using temp files (avoids shell quoting issues with markers)
    console.print(f"  [yellow]⚠[/yellow] Instalando {label} paquete por paquete...")
    req_content = requirements.read_text()
    failed = []
    seen = set()

    for line in req_content.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue

        # Extract package name for dedup/display
        pkg_part = line.split(";")[0].split("#")[0].strip()
        pkg_name = re.split(r"[>=<!\[~]", pkg_part)[0].strip()
        if not pkg_name:
            continue

        # Write single line to temp file to avoid shell quoting issues
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
        tmp.write(line + "\n")
        tmp.close()
        tmp_path = Path(tmp.name)

        try:
            r = run_cmd(
                f"uv pip install -r {tmp_path} --python {python_bin}", timeout=120
            )
            if r.returncode != 0:
                # Try binary alternative
                if pkg_name in BINARY_ALTERNATIVES:
                    alt_line = line.replace(pkg_name, BINARY_ALTERNATIVES[pkg_name])
                    tmp_path.write_text(alt_line + "\n")
                    r2 = run_cmd(
                        f"uv pip install -r {tmp_path} --python {python_bin}",
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
    """Install requirements from framework, enterprise, and tenants."""
    python_bin = workspace_path / venv_name / "bin" / "python"

    # Collect all requirements files
    req_sources: list[tuple[Path, str]] = []

    # 1. Odoo framework
    odoo_req = workspace_path / "odoo" / "requirements.txt"
    if odoo_req.exists():
        req_sources.append((odoo_req, "Odoo framework"))

    # 2. Enterprise
    if config.enterprise_enabled:
        ent_req = workspace_path / "enterprise" / "requirements.txt"
        if ent_req.exists():
            req_sources.append((ent_req, "Enterprise"))

    # 3. Tenants
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


@app.command()
def init():
    """Create a new odoo-launchpad workspace in the current directory."""
    cwd = Path.cwd()
    workspace_path = cwd / WORKSPACE_DIR_NAME

    print_banner()

    # Check not inside an existing workspace
    check = cwd
    while check != check.parent:
        if (check / "oolab.yaml").exists():
            console.print(
                f"  [red]✗[/red] Ya estás dentro de un workspace odoo-launchpad: {check}"
            )
            console.print("  No se puede crear un workspace anidado.\n")
            raise typer.Exit(1)
        check = check.parent

    if workspace_path.exists():
        console.print(
            f"  [red]✗[/red] El directorio '{WORKSPACE_DIR_NAME}' ya existe en {cwd}"
        )
        console.print("  Elimínalo o navega a otro directorio.\n")
        raise typer.Exit(1)

    # 1. Check dependencies
    if not check_system_deps():
        console.print(
            "\n  [red]Corrige las dependencias faltantes antes de continuar.[/red]\n"
        )
        raise typer.Exit(1)

    # 2. Ask configuration
    odoo_version = ask_odoo_version()
    enterprise_enabled, enterprise_source, enterprise_value = ask_enterprise()
    tenant = ask_first_tenant(odoo_version, enterprise_enabled)

    # 3. Build config
    venv_name = get_venv_name(odoo_version)
    config = WorkspaceConfig(
        odoo_version=odoo_version,
        enterprise_enabled=enterprise_enabled,
        enterprise_source=enterprise_source,
        enterprise_url=enterprise_value if enterprise_source == "git" else "",
        enterprise_path="./enterprise",
    )
    if tenant:
        config.tenants.append(tenant)

    # 4. Create workspace structure
    console.print(f"\n  [blue]ℹ[/blue] Creando workspace en {workspace_path}...")
    workspace_path.mkdir(parents=True)
    (workspace_path / "tenants").mkdir()
    (workspace_path / "config" / "odoo").mkdir(parents=True)
    (workspace_path / "config" / "nginx").mkdir(parents=True)
    (workspace_path / "docker").mkdir()
    (workspace_path / ".vscode").mkdir()
    console.print("  [green]✓[/green] Estructura de directorios creada")

    # 5. Clone Odoo Community
    branch = get_branch_name(odoo_version)
    ok = clone_repo(
        config.community_url,
        workspace_path / "odoo",
        branch,
        f"Odoo Community {branch}",
    )
    if not ok:
        console.print("\n  [red]No se pudo clonar Odoo. Abortando.[/red]\n")
        raise typer.Exit(1)

    # 6. Enterprise
    if enterprise_enabled:
        if enterprise_source == "git":
            clone_repo(
                enterprise_value,
                workspace_path / "enterprise",
                branch,
                f"Enterprise {branch}",
            )
        else:
            copy_local(
                enterprise_value,
                workspace_path / "enterprise",
                "Enterprise",
            )

    # 7. Clone tenant if provided
    if tenant and tenant.url:
        clone_repo(
            tenant.url,
            workspace_path / "tenants" / tenant.name,
            tenant.branch,
            tenant.name,
        )
    elif tenant:
        tenant_path = workspace_path / "tenants" / tenant.name
        scaffold_tenant(tenant_path, tenant.display_name, odoo_version)
        console.print(
            f"\n  [green]✓[/green] Proyecto {tenant.name} creado con estructura OCA"
        )

    # 8. Save config & generate files
    config.save(workspace_path)
    console.print("\n  [bold blue]Generando configuraciones...[/bold blue]\n")
    generate_all(workspace_path, config)

    # 9. Setup venv
    setup_venv(workspace_path, venv_name, config.python_version)
    install_requirements(workspace_path, venv_name, config)

    # 10. Summary
    len(config.tenants)
    edition = "Community + Enterprise" if enterprise_enabled else "Community"

    summary = f"""
  [bold]Path:[/bold]    {workspace_path}
  [bold]Odoo:[/bold]    {get_branch_name(odoo_version)} ({edition})
  [bold]Python:[/bold]  {config.python_version} ({venv_name})
"""
    console.print(Panel(summary, title="Workspace listo", style="bold green"))

    # Next steps
    console.print("  [bold cyan]Próximos pasos:[/bold cyan]\n")
    console.print("  [bold]1.[/bold] Abre el workspace en VSCode:")
    console.print(f"     [cyan]code {workspace_path}[/cyan]\n")
    console.print(
        "  [bold]2.[/bold] Presiona [bold]F5[/bold] (o Run > Start Debugging) y selecciona:"
    )

    if config.tenants:
        for t in config.tenants:
            ent_tag = " [magenta](Enterprise)[/magenta]" if t.enterprise else ""
            console.print(
                f"     [green]▸[/green] [bold]{t.display_name}[/bold]{ent_tag}  →  db-filter: [cyan]{t.db_filter}[/cyan]"
            )
    console.print(
        "     [green]▸[/green] [bold]Odoo - Community[/bold]      →  db-filter: [cyan]community-test[/cyan]"
    )
    console.print(
        "     [green]▸[/green] [bold]Odoo - Shell[/bold]           →  Consola interactiva"
    )
    console.print(
        "     [green]▸[/green] [bold]Odoo - Update module[/bold]  →  Edita [dim]-u module_name[/dim] en launch.json"
    )
    console.print(
        "     [green]▸[/green] [bold]Odoo - Install module[/bold] →  Edita [dim]-i module_name[/dim] en launch.json"
    )

    console.print("\n  [bold]3.[/bold] Odoo estará disponible en:")
    console.print("     [cyan]http://localhost:8069[/cyan]")
    console.print("     Primera vez: crea la BD desde el Database Manager.")

    console.print(
        "\n  [bold]4.[/bold] El [bold]db-filter[/bold] es el nombre de la base de datos que Odoo"
    )
    console.print("     filtra al arrancar. Crea una BD con ese nombre desde:")
    console.print("     [cyan]http://localhost:8069/web/database/manager[/cyan]\n")

    step = 5
    if not config.tenants:
        console.print(f"  [bold]{step}.[/bold] Agrega tu primer proyecto:")
        console.print(f"     [cyan]cd {workspace_path} && oolab add[/cyan]\n")
        step += 1

    console.print(
        f"  [bold]{step}.[/bold] Activar entorno virtual (si necesitas la terminal):"
    )
    console.print(
        f"     [dim]macOS/Linux:[/dim]  [cyan]source {venv_name}/bin/activate[/cyan]"
    )
    console.print(
        f"     [dim]Windows:[/dim]     [cyan]{venv_name}\\Scripts\\activate[/cyan]\n"
    )

    console.print(
        "  [dim]Más info: README.md | oolab -h | https://github.com/ikusolutions/odoo-lab[/dim]\n"
    )
