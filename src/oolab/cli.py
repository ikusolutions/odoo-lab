"""
odoo-lab (oolab) - CLI scaffolder for multi-project Odoo development workspaces.
Copyright (c) 2026 IKU Solutions SAS - https://www.iku.solutions
"""

import typer
from rich.console import Console

from oolab import __author__, __company__, __email__, __version__, __website__

BANNER = r"""
          [bold cyan] ██████   ██████  ██       █████  ██████[/bold cyan]
          [bold cyan]██    ██ ██    ██ ██      ██   ██ ██   ██[/bold cyan]
          [bold cyan]██    ██ ██    ██ ██      ███████ ██████[/bold cyan]
          [bold cyan]██    ██ ██    ██ ██      ██   ██ ██   ██[/bold cyan]
          [bold cyan] ██████   ██████  ███████ ██   ██ ██████[/bold cyan]
"""

EPILOG = f"[dim]{__company__}  |  {__website__}  |  {__author__} <{__email__}>[/dim]"

app = typer.Typer(
    name="oolab",
    help="CLI scaffolder for multi-project Odoo development workspaces.",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
    rich_markup_mode="rich",
    epilog=EPILOG,
)
console = Console()


def print_banner():
    console.print(BANNER)
    console.print(f"  [dim]v{__version__}  |  {__company__}  |  {__website__}[/dim]\n")


def version_callback(value: bool):
    if value:
        print_banner()
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
):
    """Odoo Lab - CLI scaffolder for multi-project Odoo development workspaces by IKU Solutions."""


# Import and register commands
from oolab.commands import add as _add  # noqa: E402, F401
from oolab.commands import doctor as _doctor  # noqa: E402, F401
from oolab.commands import generate as _generate  # noqa: E402, F401
from oolab.commands import init as _init  # noqa: E402, F401
from oolab.commands import list as _list  # noqa: E402, F401
from oolab.commands import remove as _remove  # noqa: E402, F401
