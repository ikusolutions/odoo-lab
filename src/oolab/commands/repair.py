"""
odoo-lab (oolab) - Copyright (c) 2026 IKU Solutions SAS
"""

from pathlib import Path

import typer

from oolab.cli import app, print_banner
from oolab.config import WorkspaceConfig, find_workspace, get_venv_python
from oolab.console import ERR, OK, WARN, console
from oolab.progress import step_spinner
from oolab.utils import run_cmd
from oolab.venv import (
    CORE_PACKAGES,
    CRITICAL_IMPORTS,
    install_requirements,
)
from oolab.versions import get_venv_name, get_version_from_venv_name, normalize_version


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
    index: int,
    total: int,
) -> bool:
    console.print(f"\n  [heading]── [{index}/{total}] {venv_name}[/heading]")

    if not python_bin.exists():
        console.print(f"  {ERR} Python no encontrado: {python_bin}")
        return False

    # 1. Core packages
    with step_spinner(f"Instalando core packages ({', '.join(CORE_PACKAGES)})..."):
        result = run_cmd(
            ["uv", "pip", "install", *CORE_PACKAGES, "--python", str(python_bin)],
            timeout=120,
        )
    if result.returncode == 0:
        console.print(f"  {OK} Core packages instalados")
    else:
        console.print(f"  {ERR} Error: {result.stderr.strip()[:300]}")

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
    with step_spinner("Verificando módulos críticos..."):
        for import_name, pip_name in CRITICAL_IMPORTS.items():
            r = run_cmd([str(python_bin), "-c", f"import {import_name}"])
            if r.returncode != 0:
                missing.append(pip_name)

    if not missing:
        console.print(f"  {OK} Todos los módulos críticos disponibles")
        return True

    console.print(f"  {ERR} Módulos faltantes: {', '.join(missing)}")
    with step_spinner(f"Instalando {', '.join(missing)}..."):
        result = run_cmd(
            ["uv", "pip", "install", *missing, "--python", str(python_bin)],
            timeout=120,
        )
    if result.returncode == 0:
        console.print(f"  {OK} Reparado: {', '.join(missing)}")
        return True
    else:
        console.print(f"  {ERR} No se pudo instalar {', '.join(missing)}")
        console.print(f"  [muted]{result.stderr.strip()[:300]}[/muted]")
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
    """Repara el workspace reinstalando paquetes core (psycopg2, lxml, Pillow). Atajos: -f/--full reinstala también todos los requirements.txt."""
    print_banner()

    try:
        workspace_path = find_workspace()
    except FileNotFoundError as e:
        console.print(f"  {ERR} {e}\n")
        raise typer.Exit(1) from None

    config = WorkspaceConfig.load(workspace_path)
    console.print(f"  Workspace: [accent]{workspace_path}[/accent]")

    venvs = _get_all_venvs(workspace_path, config)

    if not venvs:
        console.print(f"  {WARN} No se encontraron entornos virtuales.")
        console.print(
            "  Corre [accent]oolab init[/accent] o [accent]oolab add[/accent] primero.\n"
        )
        raise typer.Exit(1)

    total = len(venvs)
    console.print(f"  [muted]Reparando {total} entorno(s) virtual(es)[/muted]")

    all_ok = True
    for index, (venv_name, python_bin) in enumerate(venvs.items(), start=1):
        ok = _repair_venv(
            venv_name, python_bin, workspace_path, config, full, index, total
        )
        if not ok:
            all_ok = False

    console.print()
    if all_ok:
        console.print("  [success]✓ Workspace reparado correctamente.[/success]\n")
    else:
        console.print("  [warn]⚠ Algunos problemas no se pudieron resolver.[/warn]")
        console.print("  [muted]Puede que necesites dependencias del sistema:[/muted]")
        console.print(
            "  [muted]  macOS:  brew install postgresql libxml2 libxslt[/muted]"
        )
        console.print(
            "  [muted]  Linux:  apt install libpq-dev libxml2-dev libxslt1-dev libldap2-dev libsasl2-dev[/muted]\n"
        )
        raise typer.Exit(1)
