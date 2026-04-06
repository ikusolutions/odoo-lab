import typer
from rich.console import Console

from oolab.cli import app
from oolab.config import find_workspace
from oolab.utils import run_cmd

console = Console()


@app.command()
def stop():
    """Detener los servicios Docker del workspace."""
    try:
        workspace_path = find_workspace()
    except FileNotFoundError as e:
        console.print(f"\n  [red]✗ {e}[/red]\n")
        raise typer.Exit(1) from None

    compose_file = str(workspace_path / "docker" / "docker-compose.yaml")

    if not (workspace_path / "docker" / "docker-compose.yaml").exists():
        console.print("\n  [red]✗[/red] docker-compose.yaml no encontrado.")
        console.print("  Ejecuta [cyan]oolab generate[/cyan] primero.\n")
        raise typer.Exit(1) from None

    with console.status("  Deteniendo servicios...", spinner="dots"):
        result = run_cmd(["docker", "compose", "-f", compose_file, "down"], timeout=60)

    if result.returncode == 0:
        console.print("  [green]✓[/green] Servicios detenidos correctamente")
    else:
        console.print(f"  [red]✗[/red] Error deteniendo servicios: {result.stderr.strip()}")
        raise typer.Exit(1) from None
