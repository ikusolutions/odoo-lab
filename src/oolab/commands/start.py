import typer
from rich.console import Console

from oolab.cli import app
from oolab.config import find_workspace
from oolab.utils import run_cmd

console = Console()


@app.command()
def start(
    build: bool = typer.Option(False, "--build", help="Reconstruir imágenes antes de iniciar"),
):
    """Levantar los servicios Docker del workspace (PostgreSQL, Nginx)."""
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

    cmd = ["docker", "compose", "-f", compose_file, "up", "-d"]
    if build:
        cmd.append("--build")

    with console.status("  Levantando servicios...", spinner="dots"):
        result = run_cmd(cmd, timeout=120)

    if result.returncode == 0:
        console.print("  [green]✓[/green] Servicios levantados correctamente")
        ps_result = run_cmd(["docker", "compose", "-f", compose_file, "ps", "--format", "table"], timeout=30)
        if ps_result.returncode == 0 and ps_result.stdout.strip():
            console.print(f"\n{ps_result.stdout.strip()}\n")
    else:
        console.print(f"  [red]✗[/red] Error levantando servicios: {result.stderr.strip()}")
        raise typer.Exit(1) from None
