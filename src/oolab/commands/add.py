"""
odoo-lab (oolab) - Copyright (c) 2026 IKU Solutions SAS
"""

from pathlib import Path

import typer
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from oolab.cli import app, print_banner
from oolab.commands.generate import generate_all
from oolab.config import Tenant, WorkspaceConfig, find_workspace, get_venv_python
from oolab.console import ERR, INFO, OK, WARN, console
from oolab.progress import step_spinner
from oolab.scaffold import scaffold_tenant
from oolab.utils import clone_repo, copy_local, ensure_branch, run_cmd, slugify
from oolab.venv import _pip_install, install_requirements, setup_venv
from oolab.versions import (
    available_versions,
    get_branch_name,
    get_python_version,
    get_venv_name,
    is_valid_version,
    normalize_version,
)


def ensure_enterprise(
    workspace_path: Path, config: WorkspaceConfig, branch: str, odoo_version: str
):
    """Ensure enterprise addons are available, clone/copy if not."""
    ent_path = workspace_path / "enterprise"
    if ent_path.exists() and any(ent_path.iterdir()):
        console.print(f"  {OK} Enterprise ya disponible")
        return

    console.print(f"\n  {INFO} Enterprise no está configurado aún.")

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
        if not copy_local(local_path, ent_path, "Enterprise"):
            return
        config.enterprise_enabled = True
        config.enterprise_source = "local"

    # Install enterprise requirements
    ent_req = ent_path / "requirements.txt"
    if ent_req.exists():
        python_bin = get_venv_python(workspace_path, config.venv_name)
        if python_bin.exists():
            with step_spinner("Instalando dependencias de Enterprise..."):
                _pip_install(ent_req, python_bin, "Enterprise", odoo_version)
            console.print(f"  {OK} Dependencias de Enterprise instaladas")

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
    """Agrega un proyecto de cliente al workspace: clona un repositorio existente o crea uno nuevo con scaffold OCA. Atajos: -u/--url, -b/--branch, -d/--display-name, -n/--new."""
    print_banner()
    try:
        workspace_path = find_workspace()
    except FileNotFoundError as e:
        console.print(f"  {ERR} {e}\n")
        raise typer.Exit(1) from None

    config = WorkspaceConfig.load(workspace_path)

    # Interactive: ask project name, auto-derive slug
    if not display_name:
        if name:
            display_name = name
        else:
            display_name = Prompt.ask("\n  Nombre del proyecto")

    if not name:
        name = slugify(display_name)
        console.print(f"  [muted]→ Slug: {name}[/muted]")

    # Check if tenant already exists
    if any(t.name == name for t in config.tenants):
        console.print(f"\n  {ERR} El proyecto '{name}' ya existe en este workspace.\n")
        raise typer.Exit(1) from None

    # Ask Odoo version for this tenant
    versions = available_versions()
    versions_str = " / ".join(versions)
    default_ver = config.odoo_version
    while True:
        raw = Prompt.ask(f"  Versión de Odoo [{versions_str}]", default=default_ver)
        normalized = normalize_version(raw)
        if is_valid_version(normalized):
            console.print(f"  [muted]→ Odoo {normalized}.0[/muted]")
            break
        console.print(
            f"  [error]Versión no soportada. Opciones: {versions_str}[/error]"
        )

    # Ask if enterprise
    is_enterprise = Confirm.ask("  ¿Es un proyecto Enterprise?", default=False)

    # Ask clone or empty
    if not url and not new:
        clone = Confirm.ask("  ¿Clonar desde un repositorio existente?", default=True)
        if clone:
            url = Prompt.ask("  URL del repositorio")
        else:
            new = True

    branch_explicit = branch is not None
    if not branch:
        branch = get_branch_name(normalized)

    # Ensure Odoo framework exists and is on the correct branch
    odoo_path = workspace_path / "odoo"
    if not odoo_path.exists() or not any(odoo_path.iterdir()):
        console.print(f"\n  {INFO} Odoo framework no encontrado. Clonando...")
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
        ensure_enterprise(workspace_path, config, branch, normalized)
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
        console.print(f"  {OK} Entorno {venv_name} disponible")

    tenant = Tenant(
        name=name,
        display_name=display_name,
        url=url or "",
        branch=branch,
        db_filter=f"{name}-testdb",
        enterprise=is_enterprise,
        odoo_version=normalized,
    )

    tenant_path = workspace_path / "tenants" / name

    if url:
        if not clone_repo(
            url, tenant_path, branch, name, fallback_to_default=not branch_explicit
        ):
            raise typer.Exit(1) from None

        # Install pre-commit hooks if config is present
        precommit_cfg = tenant_path / ".pre-commit-config.yaml"
        if precommit_cfg.exists():
            with step_spinner("Instalando pre-commit hooks..."):
                result = run_cmd(["pre-commit", "install"], cwd=str(tenant_path))
            if result.returncode == 0:
                console.print(f"  {OK} pre-commit hooks instalados")
            else:
                console.print(
                    f"  {WARN} pre-commit no disponible o falló: {result.stderr.strip()[:200]}"
                )

        # Install tenant requirements if present
        tenant_req = tenant_path / "requirements.txt"
        if tenant_req.exists():
            python_bin = get_venv_python(workspace_path, venv_name)
            if python_bin.exists():
                with step_spinner(f"Instalando dependencias de {display_name}..."):
                    ok = _pip_install(tenant_req, python_bin, display_name, normalized)
                if ok:
                    console.print(f"  {OK} Dependencias de {display_name} instaladas")
                else:
                    console.print(
                        f"  {WARN} Algunas dependencias de {display_name} no se instalaron"
                    )
    else:
        scaffold_tenant(tenant_path, display_name, normalized)
        console.print(f"  {OK} Proyecto tenants/{name}/ creado con estructura OCA")

    # Update config
    config.tenants.append(tenant)
    config.save(workspace_path)
    console.print(f"  {OK} Proyecto agregado a oolab.yaml")

    # Regenerate configs
    console.print("\n  [heading]Regenerando configuraciones...[/heading]\n")
    generate_all(workspace_path, config)

    edition = "Enterprise" if is_enterprise else "Community"
    ent_tag = " [warn](Enterprise)[/warn]" if is_enterprise else ""

    summary = (
        f"  [bold]Proyecto:[/bold]   {display_name}{ent_tag}\n"
        f"  [bold]Versión:[/bold]    Odoo {normalized}.0 ({edition})\n"
        f"  [bold]Slug:[/bold]       [accent]{name}[/accent]\n"
        f"  [bold]DB filter:[/bold]  [accent]{tenant.db_filter}[/accent]\n"
        f"  [bold]Addons:[/bold]     tenants/{name}/"
    )
    console.print()
    console.print(
        Panel(
            summary,
            title="[success]Proyecto agregado[/success]",
            border_style="success",
        )
    )

    console.print("\n  [brand]Cómo ejecutar:[/brand]\n")
    console.print(
        f"  [bold]1.[/bold] VSCode  →  [bold]F5[/bold]  →  [accent]{display_name}[/accent]{ent_tag}"
    )
    console.print(
        f"  [bold]2.[/bold] Base de datos: crea una con el filtro [accent]{tenant.db_filter}[/accent]"
    )
    console.print(
        "     desde [accent]http://localhost:8069/web/database/manager[/accent]"
    )
    console.print(
        f"  [bold]3.[/bold] Coloca módulos en [accent]tenants/{name}/[/accent]\n"
    )
    console.print(
        "  [muted]Más info: oolab list | oolab -h | https://github.com/ikusolutions/odoo-lab[/muted]\n"
    )
