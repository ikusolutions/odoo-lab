from dataclasses import dataclass
from pathlib import Path

import typer

from oolab.config import Tenant, WorkspaceConfig, find_workspace, get_venv_python
from oolab.console import ERR, console
from oolab.utils import detect_addon_dirs
from oolab.versions import get_venv_name


@dataclass
class OdooContext:
    workspace_path: Path
    config: WorkspaceConfig
    tenant: Tenant | None
    db: str
    python_bin: Path
    odoo_bin: Path
    odoo_conf: Path
    addons_path: str
    addon_dirs: list[Path]


def resolve_odoo_context(db: str) -> OdooContext:
    try:
        workspace_path = find_workspace()
    except FileNotFoundError as e:
        console.print(f"\n  {ERR} {e}\n")
        raise typer.Exit(1) from None

    config = WorkspaceConfig.load(workspace_path)

    tenant = next(
        (t for t in config.tenants if t.db_filter == db or t.name == db),
        None,
    )
    venv_name = (
        get_venv_name(tenant.odoo_version) if tenant and tenant.odoo_version else None
    ) or config.venv_name

    python_bin = get_venv_python(workspace_path, venv_name)
    odoo_bin = workspace_path / "odoo" / "odoo-bin"
    odoo_conf = workspace_path / "config" / "odoo" / "odoo.conf"

    if not python_bin.exists():
        console.print(f"\n  {ERR} Python del venv no encontrado: {python_bin}")
        console.print("  Ejecuta [accent]oolab init[/accent] primero.\n")
        raise typer.Exit(1)

    if not odoo_bin.exists():
        console.print(f"\n  {ERR} odoo-bin no encontrado: {odoo_bin}")
        console.print("  Verifica que Odoo esté clonado en el workspace.\n")
        raise typer.Exit(1)

    if not odoo_conf.exists():
        console.print(f"\n  {ERR} odoo.conf no encontrado: {odoo_conf}")
        console.print("  Ejecuta [accent]oolab generate[/accent] primero.\n")
        raise typer.Exit(1)

    addon_dirs: list[Path] = [workspace_path / "odoo" / "addons"]
    if config.enterprise_enabled:
        enterprise_path = workspace_path / "enterprise"
        if enterprise_path.exists():
            addon_dirs.append(enterprise_path)
    for t in config.tenants:
        tenant_path = workspace_path / "tenants" / t.name
        detected = detect_addon_dirs(tenant_path)
        if detected:
            addon_dirs.extend(detected)
        elif tenant_path.exists():
            addon_dirs.append(tenant_path)

    addons_path = ",".join(str(p) for p in addon_dirs)

    return OdooContext(
        workspace_path=workspace_path,
        config=config,
        tenant=tenant,
        db=db,
        python_bin=python_bin,
        odoo_bin=odoo_bin,
        odoo_conf=odoo_conf,
        addons_path=addons_path,
        addon_dirs=addon_dirs,
    )


def assert_modules_exist(ctx: OdooContext, modules: list[str]) -> None:
    """Verifica que cada módulo exista como carpeta con manifiesto en algún addon dir.

    'all' bypassa la validación. Aborta con Exit(1) listando los faltantes
    y los addons-path consultados.
    """
    if not modules:
        console.print(f"\n  {ERR} No se especificaron módulos\n")
        raise typer.Exit(1)

    if any(m == "all" for m in modules):
        return

    manifest_files = ("__manifest__.py", "__openerp__.py")
    available: set[str] = set()
    for addon_dir in ctx.addon_dirs:
        if not addon_dir.is_dir():
            continue
        try:
            for child in addon_dir.iterdir():
                if not child.is_dir():
                    continue
                if any((child / mf).exists() for mf in manifest_files):
                    available.add(child.name)
        except PermissionError:
            continue

    missing = [m for m in modules if m not in available]
    if missing:
        console.print(
            f"\n  {ERR} Módulo(s) no encontrado(s) en addons-path: "
            f"[warn]{', '.join(missing)}[/warn]"
        )
        console.print("\n  [muted]addons-path consultado:[/muted]")
        for d in ctx.addon_dirs:
            console.print(f"  [muted]  - {d}[/muted]")
        console.print()
        raise typer.Exit(1)
