import subprocess

import typer
from rich.panel import Panel
from rich.table import Table

from oolab.cli import app
from oolab.console import console
from oolab.utils import run_cmd

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
        result = run_cmd(dep["cmd"], timeout=10)
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
    """Verifica dependencias del sistema: git, Docker, uv y Python. Ofrece instalar uv si no está disponible."""
    console.print("\n  [heading]Verificando dependencias del sistema...[/heading]\n")

    table = Table(show_header=True, header_style="heading", box=None, pad_edge=False)
    table.add_column("Dependencia", style="accent", width=16)
    table.add_column("Estado", width=8, justify="center")
    table.add_column("Detalle", style="muted")

    all_ok = True
    uv_missing = False

    for dep in DEPENDENCIES:
        ok, version = check_dependency(dep)
        if ok:
            table.add_row(dep["name"], "[success]✓[/success]", version)
        elif dep["name"] == "uv":
            uv_missing = True
            table.add_row(dep["name"], "[warn]⚠[/warn]", "No encontrado")
        elif dep["required"]:
            all_ok = False
            table.add_row(dep["name"], "[error]✗[/error]", dep["hint"])
        else:
            table.add_row(dep["name"], "[warn]⚠[/warn]", dep["hint"])

    console.print(table)

    if uv_missing:
        console.print()
        installed = offer_install_uv()
        if not installed:
            all_ok = False
            console.print("\n  [warn]uv es necesario. Instálalo manualmente:[/warn]")
            console.print("  curl -LsSf https://astral.sh/uv/install.sh | sh\n")

    console.print()
    if all_ok:
        console.print(
            Panel(
                "[success]Todas las dependencias están disponibles[/success]",
                border_style="success",
                padding=(0, 2),
            )
        )
    else:
        console.print(
            Panel(
                "[error]Faltan dependencias requeridas[/error]",
                border_style="error",
                padding=(0, 2),
            )
        )
        raise typer.Exit(1)
