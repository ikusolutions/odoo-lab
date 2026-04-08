"""
odoo-lab (oolab) - Copyright (c) 2026 IKU Solutions SAS
"""

from pathlib import Path

import typer
from rich.console import Console

from oolab.cli import app, print_banner
from oolab.config import WorkspaceConfig, find_workspace, get_venv_python
from oolab.utils import run_cmd
from oolab.venv import (
    CORE_PACKAGES,
    CRITICAL_IMPORTS,
    install_requirements,
)
from oolab.versions import get_venv_name, get_version_from_venv_name, normalize_version

console = Console()


def _get_all_venvs(workspace_path: Path, config: WorkspaceConfig) -> dict[str, Path]:
    """Return all venvs used in this workspace: {venv_name: python_bin}."""
    venvs: dict[str, Path] = {}

    # Workspace default venv
    default_venv = config.venv_name
    python_bin = get_venv_python(workspace_path, default_venv)
    if (workspace_path / default_venv).exists():
        venvs[default_venv] = python_bin

    # Per-tenant venvs (multi-version)
    for tenant in config.tenants:
        if tenant.odoo_version:
            venv_name = get_venv_name(normalize_version(tenant.odoo_version))
        elif tenant.branch:
            venv_name = get_venv_name(normalize_version(tenant.branch))
        else:
            continue
        venv_path = workspace_path / venv_name
        if venv_path.exists() and venv_name not in venvs:
            venvs[venv_name] = get_venv_python(workspace_path, venv_name)

    return venvs


def _repair_venv(
    venv_name: str,
    python_bin: Path,
    workspace_path: Path,
    config: WorkspaceConfig,
    full: bool,
) -> bool:
    console.print(f"\n  [bold blue]── {venv_name}[/bold blue]")

    if not python_bin.exists():
        console.print(f"  [red]✗[/red] Python no encontrado: {python_bin}")
        return False

    # 1. Core packages
    with console.status(
        f"  Instalando core packages ({', '.join(CORE_PACKAGES)})...", spinner="dots"
    ):
        result = run_cmd(
            ["uv", "pip", "install", *CORE_PACKAGES, "--python", str(python_bin)],
            timeout=120,
        )
    if result.returncode == 0:
        console.print("  [green]✓[/green] Core packages instalados")
    else:
        console.print(f"  [red]✗[/red] Error: {result.stderr.strip()[:300]}")

    # 2. Full requirements reinstall if requested
    # Pass the venv's Odoo version so install_requirements reads the correct
    # branch from git (via git show) instead of the current checkout.
    if full:
        odoo_version = get_version_from_venv_name(venv_name)
        console.print("  Reinstalando requirements.txt completos...")
        install_requirements(
            workspace_path, venv_name, config, odoo_version=odoo_version
        )

    # 3. Verify critical imports
    missing = []
    for import_name, pip_name in CRITICAL_IMPORTS.items():
        r = run_cmd([str(python_bin), "-c", f"import {import_name}"])
        if r.returncode != 0:
            missing.append(pip_name)

    if not missing:
        console.print("  [green]✓[/green] Todos los módulos críticos disponibles")
        return True

    console.print(f"  [red]✗[/red] Módulos faltantes: {', '.join(missing)}")
    console.print("  Instalando...")

    result = run_cmd(
        ["uv", "pip", "install", *missing, "--python", str(python_bin)],
        timeout=120,
    )
    if result.returncode == 0:
        console.print(f"  [green]✓[/green] Reparado: {', '.join(missing)}")
        return True
    else:
        console.print(f"  [red]✗[/red] No se pudo instalar {', '.join(missing)}")
        console.print(f"  [dim red]{result.stderr.strip()[:300]}[/dim red]")
        return False


@app.command()
def repair(
    full: bool = typer.Option(
        False,
        "--full",
        "-f",
        help="Reinstalar todos los requirements.txt además de los paquetes core.",
    ),
):
    """Repara el workspace reinstalando paquetes core (psycopg2, lxml, Pillow). Con --full reinstala todos los requirements.txt."""
    print_banner()

    try:
        workspace_path = find_workspace()
    except FileNotFoundError as e:
        console.print(f"  [red]✗ {e}[/red]\n")
        raise typer.Exit(1) from None

    config = WorkspaceConfig.load(workspace_path)
    console.print(f"  Workspace: [cyan]{workspace_path}[/cyan]")

    venvs = _get_all_venvs(workspace_path, config)

    if not venvs:
        console.print("  [yellow]⚠[/yellow] No se encontraron entornos virtuales.")
        console.print(
            "  Corre [cyan]oolab init[/cyan] o [cyan]oolab add[/cyan] primero.\n"
        )
        raise typer.Exit(1)

    all_ok = True
    for venv_name, python_bin in venvs.items():
        ok = _repair_venv(venv_name, python_bin, workspace_path, config, full)
        if not ok:
            all_ok = False

    console.print()
    if all_ok:
        console.print(
            "  [bold green]✓ Workspace reparado correctamente.[/bold green]\n"
        )
    else:
        console.print(
            "  [bold yellow]⚠ Algunos problemas no se pudieron resolver.[/bold yellow]"
        )
        console.print("  [dim]Puede que necesites dependencias del sistema:[/dim]")
        console.print("  [dim]  macOS:  brew install postgresql libxml2 libxslt[/dim]")
        console.print(
            "  [dim]  Linux:  apt install libpq-dev libxml2-dev libxslt1-dev libldap2-dev libsasl2-dev[/dim]\n"
        )
        raise typer.Exit(1)
