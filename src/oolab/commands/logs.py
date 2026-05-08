import typer

from oolab.cli import app
from oolab.config import find_workspace
from oolab.console import ERR, console
from oolab.parsers import docker_logs_formatter
from oolab.streaming import tail_subprocess


@app.command()
def logs(
    service: str = typer.Argument(None, help="Servicio específico (db, nginx)"),
    follow: bool = typer.Option(
        False, "--follow", "-f", help="Seguir logs en tiempo real"
    ),
    tail: int = typer.Option(50, "--tail", "-n", help="Número de líneas a mostrar"),
):
    """Muestra logs de los servicios Docker (PostgreSQL, Nginx). Atajos: -f/--follow, -n/--tail."""
    try:
        workspace_path = find_workspace()
    except FileNotFoundError as e:
        console.print(f"\n  {ERR} {e}\n")
        raise typer.Exit(1) from None

    compose_file = str(workspace_path / "docker" / "docker-compose.yaml")

    if not (workspace_path / "docker" / "docker-compose.yaml").exists():
        console.print(f"\n  {ERR} docker-compose.yaml no encontrado.")
        console.print("  Ejecuta [accent]oolab generate[/accent] primero.\n")
        raise typer.Exit(1) from None

    cmd = ["docker", "compose", "-f", compose_file, "logs", "--tail", str(tail)]
    if follow:
        cmd.append("--follow")
    if service:
        cmd.append(service)

    rc = tail_subprocess(cmd, formatter=docker_logs_formatter)
    if rc not in (0, 130):
        raise typer.Exit(rc)
