import subprocess

import typer

from oolab.cli import app
from oolab.commands._resolver import resolve_odoo_context
from oolab.console import ERR, console


@app.command(name="open-shell")
def open_shell(
    db_arg: str | None = typer.Argument(None, help="Nombre de la base de datos"),
    db: str | None = typer.Option(
        None, "--db", "-d", help="Nombre de la base de datos"
    ),
):
    """Abrir Odoo shell interactiva contra una DB. Uso: open-shell DB. Atajos: -d/--db."""
    db = db or db_arg
    if not db:
        console.print(f"\n  {ERR} Falta el argumento DB\n")
        raise typer.Exit(1)

    ctx = resolve_odoo_context(db)

    cmd = [
        str(ctx.python_bin),
        str(ctx.odoo_bin),
        "shell",
        "-d",
        ctx.db,
        f"--config={ctx.odoo_conf}",
        f"--addons-path={ctx.addons_path}",
        "--no-http",
    ]

    console.print(f"\n  [heading]Abriendo shell en DB '{ctx.db}'...[/heading]")
    console.print("  [muted]Ctrl+D o exit() para salir.[/muted]\n")

    try:
        result = subprocess.run(cmd, cwd=str(ctx.workspace_path))
    except KeyboardInterrupt:
        console.print()
        return

    if result.returncode not in (0, 130):
        raise typer.Exit(result.returncode)
