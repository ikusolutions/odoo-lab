"""
odoo-lab (oolab) - Copyright (c) 2026 IKU Solutions SAS
"""

import re
import shutil
import subprocess
import unicodedata
from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt

from oolab.cli import app, print_banner
from oolab.commands.generate import generate_all
from oolab.commands.init import (
    _pip_install,
    clone_repo,
    install_requirements,
    setup_venv,
)
from oolab.config import Tenant, WorkspaceConfig, find_workspace
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


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")


def _run(
    cmd: str, cwd: str | None = None, timeout: int = 120
) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout
    )


def get_current_branch(repo_path: Path) -> str:
    """Get the current git branch of a repo."""
    result = _run("git rev-parse --abbrev-ref HEAD", cwd=str(repo_path))
    return result.stdout.strip() if result.returncode == 0 else ""


def ensure_branch(repo_path: Path, target_branch: str, label: str):
    """Ensure a git repo is on the correct branch. Fetch and checkout if needed."""
    current = get_current_branch(repo_path)
    if current == target_branch:
        console.print(f"  [green]✓[/green] {label} en branch {target_branch}")
        return

    console.print(
        f"  [blue]ℹ[/blue] {label} en branch [yellow]{current}[/yellow], cambiando a [cyan]{target_branch}[/cyan]..."
    )

    with console.status(f"  Cambiando {label} a {target_branch}...", spinner="dots"):
        # Fetch only the target branch (shallow to keep it fast)
        _run(
            f"git remote set-branches origin {target_branch}",
            cwd=str(repo_path),
            timeout=30,
        )
        _run(
            f"git fetch --depth 1 origin {target_branch}",
            cwd=str(repo_path),
            timeout=300,
        )
        result = _run(f"git checkout {target_branch}", cwd=str(repo_path))

        if result.returncode != 0:
            # Try creating local tracking branch
            result = _run(
                f"git checkout -b {target_branch} origin/{target_branch}",
                cwd=str(repo_path),
            )

    if result.returncode == 0:
        console.print(f"  [green]✓[/green] {label} cambiado a branch {target_branch}")
    else:
        console.print(
            f"  [red]✗[/red] No se pudo cambiar {label} a branch {target_branch}"
        )
        console.print(f"  [dim]  {result.stderr.strip()}[/dim]")


def ensure_enterprise(workspace_path: Path, config: WorkspaceConfig, branch: str):
    """Ensure enterprise addons are available, clone/copy if not."""
    ent_path = workspace_path / "enterprise"
    if ent_path.exists() and any(ent_path.iterdir()):
        console.print("  [green]✓[/green] Enterprise ya disponible")
        return

    console.print("\n  [blue]ℹ[/blue] Enterprise no está configurado aún.")

    source = Prompt.ask(
        "  ¿Cómo obtener Enterprise?",
        choices=["git", "local"],
        default="git",
    )

    if source == "git":
        ent_url = Prompt.ask(
            "  URL del repositorio Enterprise",
            default="git@github.com:odoo/enterprise.git",
        )
        clone_repo(ent_url, ent_path, branch, "Enterprise")
        config.enterprise_enabled = True
        config.enterprise_source = "git"
        config.enterprise_url = ent_url
    else:
        local_path = Prompt.ask("  Path local de Enterprise")
        src = Path(local_path).expanduser().resolve()
        if not src.exists():
            console.print(f"  [red]✗[/red] Path no existe: {src}")
            return
        with console.status("  Copiando Enterprise...", spinner="dots"):
            shutil.copytree(src, ent_path, dirs_exist_ok=True)
        console.print("  [green]✓[/green] Enterprise copiado")
        config.enterprise_enabled = True
        config.enterprise_source = "local"

    # Install enterprise requirements
    ent_req = ent_path / "requirements.txt"
    if ent_req.exists():
        python_bin = workspace_path / config.venv_name / "bin" / "python"
        if python_bin.exists():
            with console.status(
                "  Instalando dependencias de Enterprise...", spinner="dots"
            ):
                _pip_install(ent_req, python_bin, "Enterprise")
            console.print("  [green]✓[/green] Dependencias de Enterprise instaladas")

    config.save(workspace_path)


@app.command()
def add(
    name: str | None = typer.Argument(
        None, help="Slug del proyecto (se genera del nombre si se omite)"
    ),
    url: str | None = typer.Option(None, "--url", "-u", help="URL del repositorio git"),
    branch: str | None = typer.Option(None, "--branch", "-b", help="Branch a clonar"),
    display_name: str | None = typer.Option(
        None, "--display-name", "-d", help="Nombre para mostrar en launch.json"
    ),
    new: bool = typer.Option(
        False, "--new", "-n", help="Crear proyecto vacío (sin clonar)"
    ),
):
    """Add a tenant project to the workspace."""
    print_banner()
    try:
        workspace_path = find_workspace()
    except FileNotFoundError as e:
        console.print(f"  [red]✗ {e}[/red]\n")
        raise typer.Exit(1) from None

    config = WorkspaceConfig.load(workspace_path)

    # Interactive: ask project name, auto-derive slug
    if not display_name:
        display_name = Prompt.ask("\n  Nombre del proyecto")

    if not name:
        name = slugify(display_name)
        console.print(f"  [dim]→ Slug: {name}[/dim]")

    # Check if tenant already exists
    if any(t.name == name for t in config.tenants):
        console.print(
            f"\n  [red]✗[/red] El proyecto '{name}' ya existe en este workspace.\n"
        )
        raise typer.Exit(1) from None

    # Ask Odoo version for this tenant
    versions = available_versions()
    versions_str = " / ".join(versions)
    default_ver = config.odoo_version
    while True:
        raw = Prompt.ask(f"  Versión de Odoo [{versions_str}]", default=default_ver)
        normalized = normalize_version(raw)
        if is_valid_version(normalized):
            console.print(f"  [dim]→ Odoo {normalized}.0[/dim]")
            break
        console.print(f"  [red]Versión no soportada. Opciones: {versions_str}[/red]")

    # Ask if enterprise
    is_enterprise = Confirm.ask("  ¿Es un proyecto Enterprise?", default=False)

    # Ask clone or empty
    if not url and not new:
        clone = Confirm.ask("  ¿Clonar desde un repositorio existente?", default=True)
        if clone:
            url = Prompt.ask("  URL del repositorio")
        else:
            new = True

    if not branch:
        branch = get_branch_name(normalized)

    # Ensure Odoo framework exists and is on the correct branch
    odoo_path = workspace_path / "odoo"
    if not odoo_path.exists() or not any(odoo_path.iterdir()):
        console.print("\n  [blue]ℹ[/blue] Odoo framework no encontrado. Clonando...")
        clone_repo(
            config.community_url,
            odoo_path,
            branch,
            f"Odoo Community {branch}",
        )
    else:
        ensure_branch(odoo_path, branch, "Odoo Community")

    # Ensure enterprise is available and on the correct branch
    if is_enterprise:
        ensure_enterprise(workspace_path, config, branch)
        ent_path = workspace_path / "enterprise"
        if ent_path.exists() and (ent_path / ".git").exists():
            ensure_branch(ent_path, branch, "Enterprise")

    # Ensure venv exists for this Odoo version, AFTER checkouts
    venv_name = get_venv_name(normalized)
    python_version = get_python_version(normalized)
    venv_path = workspace_path / venv_name
    if not venv_path.exists():
        setup_venv(workspace_path, venv_name, python_version)
        # Install requirements from the correct branch
        install_requirements(workspace_path, venv_name, config)
    else:
        console.print(f"  [green]✓[/green] Entorno {venv_name} disponible")

    tenant = Tenant(
        name=name,
        display_name=display_name,
        url=url or "",
        branch=branch,
        db_filter=name,
        enterprise=is_enterprise,
    )

    tenant_path = workspace_path / "tenants" / name

    if url:
        with console.status(f"  Clonando {name}...", spinner="dots"):
            result = subprocess.run(
                f"git clone --depth 1 --branch {branch} {url} {tenant_path}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=300,
            )
        if result.returncode == 0:
            console.print(f"  [green]✓[/green] {name} clonado en tenants/{name}/")
        else:
            console.print(f"  [red]✗[/red] Error clonando: {result.stderr.strip()}")
            raise typer.Exit(1) from None

        # Install tenant requirements if present
        tenant_req = tenant_path / "requirements.txt"
        if tenant_req.exists():
            python_bin = workspace_path / config.venv_name / "bin" / "python"
            if python_bin.exists():
                with console.status(
                    f"  Instalando dependencias de {display_name}...", spinner="dots"
                ):
                    ok = _pip_install(tenant_req, python_bin, display_name)
                if ok:
                    console.print(
                        f"  [green]✓[/green] Dependencias de {display_name} instaladas"
                    )
                else:
                    console.print(
                        f"  [yellow]⚠[/yellow] Algunas dependencias de {display_name} no se instalaron"
                    )
    else:
        scaffold_tenant(tenant_path, display_name, normalized)
        console.print(
            f"  [green]✓[/green] Proyecto tenants/{name}/ creado con estructura OCA"
        )

    # Update config
    config.tenants.append(tenant)
    config.save(workspace_path)
    console.print("  [green]✓[/green] Proyecto agregado a oolab.yaml")

    # Regenerate configs
    console.print("\n  [bold blue]Regenerando configuraciones...[/bold blue]\n")
    generate_all(workspace_path, config)

    edition = "Enterprise" if is_enterprise else "Community"
    ent_tag = " [magenta](Enterprise)[/magenta]" if is_enterprise else ""

    console.print(
        f"\n  [bold green]✓ Proyecto '{display_name}' ({edition}) agregado correctamente.[/bold green]\n"
    )

    console.print("  [bold cyan]Cómo ejecutar:[/bold cyan]\n")
    console.print("  [bold]1.[/bold] En VSCode, presiona [bold]F5[/bold] y selecciona:")
    console.print(f"     [green]▸[/green] [bold]{display_name}[/bold]{ent_tag}")
    console.print(f"\n  [bold]2.[/bold] Base de datos (db-filter): [cyan]{name}[/cyan]")
    console.print("     Odoo creará o usará una BD con este filtro al arrancar.")
    console.print(
        "     Puedes crearla desde [cyan]http://localhost:8069/web/database/manager[/cyan]"
    )
    console.print(
        f"\n  [bold]3.[/bold] Addons del proyecto en: [cyan]tenants/{name}/[/cyan]"
    )
    console.print("     Coloca tus módulos ahí con la estructura estándar de Odoo.\n")
    console.print(
        "  [dim]Más info: README.md | oolab list | oolab -h | https://github.com/ikusolutions/odoo-lab[/dim]\n"
    )
