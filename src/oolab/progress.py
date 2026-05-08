"""
odoo-lab (oolab) - Copyright (c) 2026 IKU Solutions SAS

Helpers de progreso enterprise: barras con ETA, tiempo transcurrido y contador.
Auto-detección de TTY: en pipes/CI se reduce a una línea por evento.
"""

from contextlib import contextmanager

from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from oolab.console import console


def make_progress(*, transient: bool = False, with_count: bool = True) -> Progress:
    """Progress configurado con columnas enterprise (bar + % + count + elapsed + ETA).

    Args:
        transient: si True, la barra desaparece al cerrar.
        with_count: si True, muestra `N/total` (útil para iterar listas).
    """
    columns: list = [
        SpinnerColumn(style="accent"),
        TextColumn("[bold]{task.description}[/bold]"),
        BarColumn(bar_width=None, complete_style="accent", finished_style="success"),
        TaskProgressColumn(),
    ]
    if with_count:
        columns.append(MofNCompleteColumn())
    columns.extend(
        [
            TextColumn("[muted]·[/muted]"),
            TimeElapsedColumn(),
            TextColumn("[muted]ETA[/muted]"),
            TimeRemainingColumn(),
        ]
    )

    return Progress(
        *columns,
        console=console,
        transient=transient,
        expand=True,
        disable=not console.is_terminal,
    )


@contextmanager
def step_spinner(description: str):
    """Spinner único con tiempo transcurrido. Drop-in para console.status pero con elapsed."""
    progress = Progress(
        SpinnerColumn(style="accent"),
        TextColumn("[bold]{task.description}[/bold]"),
        TextColumn("[muted]·[/muted]"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
        disable=not console.is_terminal,
    )
    with progress:
        progress.add_task(description, total=None)
        yield
