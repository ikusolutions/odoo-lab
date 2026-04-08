import typer
from rich.console import Console
from rich.table import Table

from oolab.cli import app
from oolab.config import WorkspaceConfig, find_workspace

console = Console()


@app.command(name="list")
def list_tenants():
    """Lista los proyectos configurados en el workspace con su versión de Odoo, branch y estado."""
    try:
        workspace_path = find_workspace()
    except FileNotFoundError as e:
        console.print(f"\n  [red]✗ {e}[/red]\n")
        raise typer.Exit(1) from None

    config = WorkspaceConfig.load(workspace_path)

    console.print(f"\n  [bold]Workspace:[/bold] {workspace_path.name}")
    console.print(f"  [bold]Odoo:[/bold] {config.odoo_version}")
    edition = "Community + Enterprise" if config.enterprise_enabled else "Community"
    console.print(f"  [bold]Edición:[/bold] {edition}")
    console.print(
        f"  [bold]Python:[/bold] {config.python_version} ({config.venv_name})\n"
    )

    if not config.tenants:
        console.print("  No hay proyectos configurados.")
        console.print("  Usa [cyan]oolab add <nombre>[/cyan] para agregar uno.\n")
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("Nombre", style="cyan")
    table.add_column("Display Name")
    table.add_column("Branch")
    table.add_column("DB Filter")
    table.add_column("Estado")

    for tenant in config.tenants:
        tenant_path = workspace_path / "tenants" / tenant.name
        if tenant_path.exists():
            status = "[green]✓ clonado[/green]"
        else:
            status = "[red]✗ faltante[/red]"

        table.add_row(
            tenant.name,
            tenant.display_name,
            tenant.branch,
            tenant.db_filter,
            status,
        )

    console.print(table)
    console.print()
