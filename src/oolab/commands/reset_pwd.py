import subprocess

import typer
from rich.console import Console

from oolab.cli import app
from oolab.config import WorkspaceConfig, find_workspace, get_venv_python
from oolab.utils import detect_addon_dirs
from oolab.versions import get_venv_name

console = Console()


@app.command(name="reset-pwd")
def reset_pwd(
    db_arg: str | None = typer.Argument(None, help="Nombre de la base de datos"),
    password_arg: str | None = typer.Argument(None, help="Nueva contraseña"),
    db: str | None = typer.Option(None, "--db", help="Nombre de la base de datos"),
    password: str | None = typer.Option(None, "--password", help="Nueva contraseña"),
    login: str = typer.Option(
        "admin", "--login", help="Login del usuario (default: admin)"
    ),
):
    """Resetear la contraseña. Uso: reset-pwd DB PASSWORD  o  reset-pwd --db DB --password PASSWORD"""
    db = db or db_arg
    password = password or password_arg
    if not db:
        console.print("\n  [red]✗[/red] Falta el argumento DB\n")
        raise typer.Exit(1)
    if not password:
        console.print("\n  [red]✗[/red] Falta el argumento PASSWORD\n")
        raise typer.Exit(1)
    try:
        workspace_path = find_workspace()
    except FileNotFoundError as e:
        console.print(f"\n  [red]✗ {e}[/red]\n")
        raise typer.Exit(1) from None

    config = WorkspaceConfig.load(workspace_path)

    # Resolve venv from the matching tenant (by db_filter or name), fallback to workspace venv
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
        console.print(f"\n  [red]✗[/red] Python del venv no encontrado: {python_bin}")
        console.print("  Ejecuta [cyan]oolab init[/cyan] primero.\n")
        raise typer.Exit(1)

    if not odoo_bin.exists():
        console.print(f"\n  [red]✗[/red] odoo-bin no encontrado: {odoo_bin}")
        console.print("  Verifica que Odoo esté clonado en el workspace.\n")
        raise typer.Exit(1)

    if not odoo_conf.exists():
        console.print(f"\n  [red]✗[/red] odoo.conf no encontrado: {odoo_conf}")
        console.print("  Ejecuta [cyan]oolab generate[/cyan] primero.\n")
        raise typer.Exit(1)

    # Construir addons-path detectando módulos automáticamente
    addons_parts = [str(workspace_path / "odoo" / "addons")]
    if config.enterprise_enabled:
        enterprise_path = workspace_path / "enterprise"
        if enterprise_path.exists():
            addons_parts.append(str(enterprise_path))
    for t in config.tenants:
        tenant_path = workspace_path / "tenants" / t.name
        detected = detect_addon_dirs(tenant_path)
        if detected:
            addons_parts.extend(str(p) for p in detected)
        elif tenant_path.exists():
            addons_parts.append(str(tenant_path))
    addons_path = ",".join(addons_parts)

    # Script ORM para Odoo shell
    escaped_password = password.replace("\\", "\\\\").replace("'", "\\'")
    escaped_login = login.replace("\\", "\\\\").replace("'", "\\'")

    write_dict = f"{{'password': '{escaped_password}'}}"
    if login != "admin":
        write_dict = f"{{'login': '{escaped_login}', 'password': '{escaped_password}'}}"

    script = (
        "user = env['res.users'].browse(2)\n"
        "if not user.exists():\n"
        "    print('OOLAB_ERROR: res.users ID=2 not found')\n"
        "else:\n"
        f"    user.write({write_dict})\n"
        "    env.cr.commit()\n"
        "    print('OOLAB_OK: password updated')\n"
    )

    cmd = [
        str(python_bin),
        str(odoo_bin),
        "shell",
        "-d",
        db,
        f"--config={odoo_conf}",
        f"--addons-path={addons_path}",
        "--no-http",
    ]

    console.print(f"\n  [bold blue]Reseteando contraseña en DB '{db}'...[/bold blue]")
    console.print(f"  [dim]Usuario: res.users ID=2 (login: {login})[/dim]\n")

    try:
        with console.status("  Ejecutando Odoo shell...", spinner="dots"):
            result = subprocess.run(
                cmd,
                input=script,
                cwd=str(workspace_path),
                capture_output=True,
                text=True,
                timeout=120,
            )
    except subprocess.TimeoutExpired:
        console.print("  [red]✗[/red] Timeout: Odoo tardó demasiado en responder.")
        console.print(
            "  Verifica que PostgreSQL esté corriendo ([cyan]docker compose -f docker/docker-compose.yaml up -d[/cyan]).\n"
        )
        raise typer.Exit(1) from None

    output = result.stdout + result.stderr

    if "OOLAB_OK: password updated" in result.stdout:
        console.print("  [green]✓[/green] Contraseña actualizada correctamente.")
        console.print(f"  [dim]DB: {db} | Login: {login}[/dim]\n")
    elif "OOLAB_ERROR: res.users ID=2 not found" in output:
        console.print("  [red]✗[/red] Usuario res.users ID=2 no encontrado en la DB.")
        console.print("  Verifica que la base de datos tiene datos de Odoo.\n")
        raise typer.Exit(1)
    else:
        console.print("  [red]✗[/red] Error ejecutando Odoo shell.\n")
        if result.stderr:
            error_lines = [
                line
                for line in result.stderr.strip().splitlines()
                if "fatal" in line.lower() or "error" in line.lower()
            ]
            if error_lines:
                for line in error_lines[-5:]:
                    console.print(f"  [dim]{line.strip()}[/dim]")
            else:
                console.print(f"  [dim]{result.stderr.strip()[-500:]}[/dim]")
        console.print()
        raise typer.Exit(1)
