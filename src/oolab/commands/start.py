import typer

from oolab.cli import app
from oolab.config import find_workspace
from oolab.console import ERR, OK, console
from oolab.streaming import stream_subprocess
from oolab.utils import run_cmd


@app.command()
def start(
    build: bool = typer.Option(
        False, "--build", help="Reconstruir imágenes antes de iniciar"
    ),
):
    """Levanta los servicios Docker del workspace (PostgreSQL, Nginx). Usa --build para reconstruir imágenes."""
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

    cmd = ["docker", "compose", "-f", compose_file, "up", "-d"]
    if build:
        cmd.append("--build")

    rc, captured = stream_subprocess(cmd, "Levantando servicios", timeout=300)

    if rc == 0:
        console.print(f"  {OK} Servicios levantados correctamente")
        ps_result = run_cmd(
            ["docker", "compose", "-f", compose_file, "ps", "--format", "table"],
            timeout=30,
        )
        if ps_result.returncode == 0 and ps_result.stdout.strip():
            console.print(f"\n{ps_result.stdout.strip()}\n")
    else:
        console.print(f"  {ERR} Error levantando servicios:")
        for line in captured[-20:]:
            console.print(f"  [muted]{line.rstrip()}[/muted]")
        raise typer.Exit(1) from None
