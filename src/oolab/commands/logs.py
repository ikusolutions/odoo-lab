import subprocess

import typer
from rich.console import Console

from oolab.cli import app
from oolab.config import find_workspace

console = Console()


@app.command()
def logs(
    service: str = typer.Argument(None, help="Servicio específico (db, nginx)"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Seguir logs en tiempo real"),
    tail: int = typer.Option(50, "--tail", "-n", help="Número de líneas a mostrar"),
):
    """Muestra logs de los servicios Docker (PostgreSQL, Nginx). Usa -f para seguir en tiempo real."""
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

    cmd = ["docker", "compose", "-f", compose_file, "logs", "--tail", str(tail)]
    if follow:
        cmd.append("--follow")
    if service:
        cmd.append(service)

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        pass
