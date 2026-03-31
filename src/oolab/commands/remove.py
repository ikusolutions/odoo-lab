import shutil

import typer
from rich.console import Console
from rich.prompt import Confirm

from oolab.cli import app
from oolab.commands.generate import generate_all
from oolab.config import WorkspaceConfig, find_workspace

console = Console()


@app.command()
def remove(
    name: str = typer.Argument(help="Nombre del proyecto a eliminar"),
):
    """Remove a tenant project from the workspace."""
    try:
        workspace_path = find_workspace()
    except FileNotFoundError as e:
        console.print(f"\n  [red]✗ {e}[/red]\n")
        raise typer.Exit(1) from None

    config = WorkspaceConfig.load(workspace_path)

    # Find tenant
    tenant = next((t for t in config.tenants if t.name == name), None)
    if not tenant:
        console.print(f"\n  [red]✗[/red] Proyecto '{name}' no encontrado.\n")
        console.print("  Proyectos disponibles:")
        for t in config.tenants:
            console.print(f"    - {t.name}")
        console.print()
        raise typer.Exit(1) from None

    # Confirm
    console.print(
        f"\n  Eliminando proyecto: [bold]{tenant.display_name}[/bold] ({name})"
    )

    tenant_path = workspace_path / "tenants" / name
    if tenant_path.exists():
        delete_files = Confirm.ask(
            f"  ¿Eliminar también el directorio tenants/{name}/?",
            default=False,
        )
        if delete_files:
            shutil.rmtree(tenant_path)
            console.print(f"  [green]✓[/green] Directorio tenants/{name}/ eliminado")
        else:
            console.print(f"  [dim]  Directorio tenants/{name}/ conservado[/dim]")

    # Update config
    config.tenants = [t for t in config.tenants if t.name != name]
    config.save(workspace_path)
    console.print("  [green]✓[/green] Proyecto eliminado de oolab.yaml")

    # Regenerate configs
    console.print("\n  [bold blue]Regenerando configuraciones...[/bold blue]\n")
    generate_all(workspace_path, config)
    console.print(
        f"\n  [bold green]Proyecto '{name}' eliminado correctamente.[/bold green]\n"
    )
