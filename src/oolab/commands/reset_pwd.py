import subprocess

import typer

from oolab.cli import app
from oolab.commands._resolver import resolve_odoo_context
from oolab.console import ERR, OK, console
from oolab.progress import step_spinner


@app.command(name="reset-pwd")
def reset_pwd(
    db_arg: str | None = typer.Argument(None, help="Nombre de la base de datos"),
    password_arg: str | None = typer.Argument(None, help="Nueva contraseña"),
    db: str | None = typer.Option(
        None, "--db", "-d", help="Nombre de la base de datos"
    ),
    password: str | None = typer.Option(
        None, "--password", "-p", help="Nueva contraseña"
    ),
    login: str = typer.Option(
        "admin", "--login", "-l", help="Nuevo login del usuario admin (default: admin)"
    ),
):
    """Resetear contraseña del admin. Uso: reset-pwd DB PASS. Atajos: -d/--db, -p/--password, -l/--login."""
    db = db or db_arg
    password = password or password_arg
    if not db:
        console.print(f"\n  {ERR} Falta el argumento DB\n")
        raise typer.Exit(1)
    if not password:
        console.print(f"\n  {ERR} Falta el argumento PASSWORD\n")
        raise typer.Exit(1)

    ctx = resolve_odoo_context(db)

    escaped_password = password.replace("\\", "\\\\").replace("'", "\\'")
    escaped_login = login.replace("\\", "\\\\").replace("'", "\\'")
    write_vals = f"{{'login': '{escaped_login}', 'password': '{escaped_password}'}}"

    script = (
        "user = env.ref('base.user_admin', raise_if_not_found=False) or env['res.users'].browse(2)\n"
        "if not user.exists():\n"
        "    print('OOLAB_ERROR: admin user not found')\n"
        "else:\n"
        f"    user.write({write_vals})\n"
        "    if hasattr(user, 'flush_recordset'):\n"
        "        user.flush_recordset()\n"
        "    else:\n"
        "        user.flush()\n"
        "    env.cr.commit()\n"
        "    print('OOLAB_OK: password updated')\n"
    )

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

    console.print(f"\n  [heading]Reseteando contraseña en DB '{ctx.db}'...[/heading]")
    console.print(f"  [muted]Usuario: base.user_admin → login: {login}[/muted]\n")

    try:
        with step_spinner("Ejecutando Odoo shell..."):
            result = subprocess.run(
                cmd,
                input=script,
                cwd=str(ctx.workspace_path),
                capture_output=True,
                text=True,
                timeout=120,
            )
    except subprocess.TimeoutExpired:
        console.print(f"  {ERR} Timeout: Odoo tardó demasiado en responder.")
        console.print(
            "  Verifica que PostgreSQL esté corriendo ([accent]docker compose -f docker/docker-compose.yaml up -d[/accent]).\n"
        )
        raise typer.Exit(1) from None

    output = result.stdout + result.stderr

    if "OOLAB_OK: password updated" in result.stdout:
        console.print(f"  {OK} Credenciales actualizadas correctamente.")
        console.print(
            f"  [muted]DB: {ctx.db} | Login: {login} | Password: {password}[/muted]\n"
        )
    elif "OOLAB_ERROR: admin user not found" in output:
        console.print(
            f"  {ERR} Usuario admin (base.user_admin) no encontrado en la DB."
        )
        console.print("  Verifica que la base de datos tiene datos de Odoo.\n")
        raise typer.Exit(1)
    else:
        console.print(f"  {ERR} Error ejecutando Odoo shell.\n")
        if result.stdout.strip():
            console.print("  [muted]--- stdout ---[/muted]")
            console.print(f"  [muted]{result.stdout.strip()[-1000:]}[/muted]")
        if result.stderr.strip():
            console.print("  [muted]--- stderr ---[/muted]")
            console.print(f"  [muted]{result.stderr.strip()[-1000:]}[/muted]")
        console.print()
        raise typer.Exit(1)
