import subprocess

import typer

from oolab.cli import app
from oolab.commands._resolver import assert_modules_exist, resolve_odoo_context
from oolab.console import ERR, OK, WARN, console
from oolab.parsers import odoo_module_parser
from oolab.streaming import stream_subprocess


@app.command(name="module-update")
def module_update(
    db_arg: str | None = typer.Argument(None, help="Nombre de la base de datos"),
    modules_arg: str | None = typer.Argument(
        None, help="Módulos coma-separados o 'all'"
    ),
    db: str | None = typer.Option(
        None, "--db", "-d", help="Nombre de la base de datos"
    ),
    modules: str | None = typer.Option(
        None, "--modules", "-m", help="Módulos coma-separados o 'all'"
    ),
    timeout: int = typer.Option(
        1800, "--timeout", "-t", help="Timeout en segundos (default 1800)"
    ),
):
    """Actualizar módulos en una DB. Uso: module-update DB sale,purchase | all. Atajos: -d/--db, -m/--modules, -t/--timeout."""
    db = db or db_arg
    raw_modules = modules or modules_arg

    if not db:
        console.print(f"\n  {ERR} Falta el argumento DB\n")
        raise typer.Exit(1)
    if not raw_modules:
        console.print(f"\n  {ERR} Falta el argumento MODULES\n")
        raise typer.Exit(1)

    mods = [m.strip() for m in raw_modules.split(",") if m.strip()]
    if not mods:
        console.print(f"\n  {ERR} Lista de módulos vacía\n")
        raise typer.Exit(1)

    ctx = resolve_odoo_context(db)
    assert_modules_exist(ctx, mods)

    cmd = [
        str(ctx.python_bin),
        str(ctx.odoo_bin),
        "-c",
        str(ctx.odoo_conf),
        f"--addons-path={ctx.addons_path}",
        "-d",
        ctx.db,
        "-u",
        ",".join(mods),
        "--stop-after-init",
        "--no-http",
    ]

    console.print(
        f"\n  [heading]Actualizando {', '.join(mods)} en DB '{ctx.db}'...[/heading]\n"
    )

    try:
        rc, _captured = stream_subprocess(
            cmd,
            f"Actualizando {', '.join(mods)}",
            cwd=str(ctx.workspace_path),
            timeout=timeout,
            parser=odoo_module_parser(),
        )
    except subprocess.TimeoutExpired:
        console.print(
            f"\n  {ERR} Timeout tras {timeout}s. "
            "Aumenta --timeout o revisa que PostgreSQL esté corriendo.\n"
        )
        raise typer.Exit(1) from None
    except KeyboardInterrupt:
        console.print(f"\n  {WARN} Interrumpido por el usuario.\n")
        raise typer.Exit(130) from None

    if rc == 0:
        console.print(f"\n  {OK} Módulos actualizados: {', '.join(mods)}\n")
    else:
        console.print(f"\n  {ERR} odoo-bin terminó con código {rc}\n")
        raise typer.Exit(rc)
