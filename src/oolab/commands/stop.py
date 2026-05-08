import typer

from oolab.cli import app
from oolab.config import find_workspace
from oolab.console import ERR, OK, console
from oolab.streaming import stream_subprocess


@app.command()
def stop():
    """Detiene los servicios Docker del workspace (PostgreSQL, Nginx)."""
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

    rc, captured = stream_subprocess(
        ["docker", "compose", "-f", compose_file, "down"],
        "Deteniendo servicios",
        timeout=120,
    )

    if rc == 0:
        console.print(f"  {OK} Servicios detenidos correctamente")
    else:
        console.print(f"  {ERR} Error deteniendo servicios:")
        for line in captured[-20:]:
            console.print(f"  [muted]{line.rstrip()}[/muted]")
        raise typer.Exit(1) from None
