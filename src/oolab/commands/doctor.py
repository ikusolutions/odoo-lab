import subprocess

import typer
from rich.console import Console
from rich.table import Table

from oolab.cli import app

console = Console()

DEPENDENCIES = [
    {
        "name": "git",
        "cmd": ["git", "--version"],
        "required": True,
        "hint": "Install git: https://git-scm.com/downloads",
    },
    {
        "name": "docker",
        "cmd": ["docker", "--version"],
        "required": True,
        "hint": "Install Docker: https://docs.docker.com/get-docker/",
    },
    {
        "name": "docker compose",
        "cmd": ["docker", "compose", "version"],
        "required": True,
        "hint": "Docker Compose v2 comes with Docker Desktop. Update Docker.",
    },
    {
        "name": "uv",
        "cmd": ["uv", "--version"],
        "required": True,
        "hint": "Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh",
    },
    {
        "name": "python3",
        "cmd": ["python3", "--version"],
        "required": True,
        "hint": "Install Python 3: https://www.python.org/downloads/",
    },
]


def check_dependency(dep: dict) -> tuple[bool, str]:
    """Check if a dependency is available. Returns (ok, version_string)."""
    try:
        result = subprocess.run(dep["cmd"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version = result.stdout.strip() or result.stderr.strip()
            return True, version
        return False, ""
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, ""


def offer_install_uv() -> bool:
    """Offer to install uv automatically."""
    install = typer.confirm(
        "  uv no encontrado. ¿Instalar automáticamente?", default=True
    )
    if not install:
        return False
    console.print("  Instalando uv...", style="blue")
    try:
        result = subprocess.run(
            "curl -LsSf https://astral.sh/uv/install.sh | sh",
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            console.print("  ✓ uv instalado correctamente", style="green")
            return True
        else:
            console.print(f"  ✗ Error instalando uv: {result.stderr}", style="red")
            return False
    except subprocess.TimeoutExpired:
        console.print("  ✗ Timeout instalando uv", style="red")
        return False


@app.command()
def doctor():
    """Verify system dependencies for Odoo development."""
    console.print("\n  Verificando dependencias del sistema...\n", style="bold blue")

    table = Table(show_header=True, header_style="bold")
    table.add_column("Dependencia", style="cyan", width=16)
    table.add_column("Estado", width=10)
    table.add_column("Detalle", style="dim")

    all_ok = True
    uv_missing = False

    for dep in DEPENDENCIES:
        ok, version = check_dependency(dep)
        if ok:
            table.add_row(dep["name"], "[green]✓[/green]", version)
        else:
            if dep["name"] == "uv":
                uv_missing = True
                table.add_row(dep["name"], "[yellow]⚠[/yellow]", "No encontrado")
            elif dep["required"]:
                all_ok = False
                table.add_row(dep["name"], "[red]✗[/red]", dep["hint"])
            else:
                table.add_row(dep["name"], "[yellow]⚠[/yellow]", dep["hint"])

    console.print(table)

    if uv_missing:
        console.print()
        installed = offer_install_uv()
        if not installed:
            all_ok = False
            console.print(
                "\n  [yellow]uv es necesario. Instálalo manualmente:[/yellow]"
            )
            console.print("  curl -LsSf https://astral.sh/uv/install.sh | sh\n")

    if all_ok:
        console.print(
            "\n  [bold green]Todas las dependencias están disponibles.[/bold green]\n"
        )
    else:
        console.print("\n  [bold red]Faltan dependencias requeridas.[/bold red]\n")
        raise typer.Exit(1)
