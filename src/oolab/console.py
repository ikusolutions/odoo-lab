"""
odoo-lab (oolab) - Copyright (c) 2026 IKU Solutions SAS

Centralised Rich console with a consistent theme and pretty tracebacks.
Importar `console` desde aquí en lugar de instanciar Console() en cada módulo.
"""

from rich.console import Console
from rich.theme import Theme
from rich.traceback import install as install_rich_traceback

OOLAB_THEME = Theme(
    {
        "success": "bold green",
        "error": "bold red",
        "warn": "yellow",
        "info": "blue",
        "accent": "cyan",
        "muted": "dim",
        "brand": "bold cyan",
        "heading": "bold blue",
        "ok_mark": "green",
        "err_mark": "red",
        "warn_mark": "yellow",
        "info_mark": "blue",
    }
)

console = Console(theme=OOLAB_THEME, highlight=False)

install_rich_traceback(console=console, show_locals=False, suppress=["typer", "click"])


OK = "[ok_mark]✓[/ok_mark]"
ERR = "[err_mark]✗[/err_mark]"
WARN = "[warn_mark]⚠[/warn_mark]"
INFO = "[info_mark]ℹ[/info_mark]"


def is_interactive() -> bool:
    """True si el output es un TTY interactivo (no redirigido a archivo/CI)."""
    return console.is_terminal and not console.is_jupyter
