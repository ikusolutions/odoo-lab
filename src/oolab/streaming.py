"""
odoo-lab (oolab) - Copyright (c) 2026 IKU Solutions SAS

stream_subprocess: ejecuta un comando externo y muestra una vista en vivo con:
  - barra de progreso (si se conoce el total) o spinner (si no)
  - línea transitoria con la última salida del proceso
  - logs persistentes para líneas marcadas como WARNING/ERROR

Auto-fallback a subprocess.run sin Live cuando stdout no es un TTY.
"""

import subprocess
import threading
from collections.abc import Callable
from dataclasses import dataclass
from queue import Empty, Queue
from typing import IO

from rich.console import Group
from rich.live import Live
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
from rich.text import Text

from oolab.console import console


@dataclass
class StreamUpdate:
    """Resultado de parsear una línea del subproceso.

    Cualquier campo en None significa "no actualizar". El campo `log`,
    cuando se setea, persiste la línea (sale del área transitoria).
    """

    completed: int | None = None
    total: int | None = None
    description: str | None = None
    log: tuple[str, str] | None = None  # (style, text)


ParserFn = Callable[[str], StreamUpdate | None]


def _make_progress(with_count: bool) -> Progress:
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
    return Progress(*columns, console=console, expand=True)


def _reader(stream: IO[str], queue: Queue) -> None:
    try:
        for line in stream:
            queue.put(line)
    finally:
        queue.put(None)


def stream_subprocess(
    cmd: list[str],
    label: str,
    *,
    cwd: str | None = None,
    timeout: int | None = None,
    parser: ParserFn | None = None,
    total: int | None = None,
    stdin_input: str | None = None,
) -> tuple[int, list[str]]:
    """Ejecuta `cmd` en streaming con barra Live + línea transitoria.

    Args:
        cmd: comando a ejecutar.
        label: descripción inicial del task.
        cwd: directorio de trabajo.
        timeout: segundos máximos para wait().
        parser: opcional, función que recibe cada línea cruda y devuelve
            StreamUpdate o None.
        total: si se conoce de antemano, fija el total inicial de la barra.
        stdin_input: opcional, texto a pasar por stdin.

    Returns:
        (returncode, todas_las_lineas_capturadas)
    """
    captured: list[str] = []

    if not console.is_terminal:
        # Fallback CI/no-TTY: corre el comando, captura, y al final imprime
        # un resumen sucinto. Sin animaciones.
        proc = subprocess.run(
            cmd,
            input=stdin_input,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if proc.stdout:
            captured.extend(proc.stdout.splitlines(keepends=True))
        if proc.stderr:
            captured.extend(proc.stderr.splitlines(keepends=True))
        return proc.returncode, captured

    progress = _make_progress(with_count=total is not None)
    transient_text = Text("", style="muted", overflow="ellipsis", no_wrap=True)
    group = Group(progress, transient_text)

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE if stdin_input is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=cwd,
        text=True,
        bufsize=1,
    )

    if stdin_input is not None and proc.stdin is not None:
        proc.stdin.write(stdin_input)
        proc.stdin.close()

    queue: Queue = Queue()
    assert proc.stdout is not None
    reader_thread = threading.Thread(
        target=_reader, args=(proc.stdout, queue), daemon=True
    )
    reader_thread.start()

    with Live(group, console=console, refresh_per_second=12, transient=True) as live:
        task_id = progress.add_task(label, total=total)
        current = 0
        finished_reader = False
        while True:
            try:
                line = queue.get(timeout=0.2)
            except Empty:
                if proc.poll() is not None and finished_reader:
                    break
                continue

            if line is None:
                finished_reader = True
                if proc.poll() is not None:
                    break
                continue

            captured.append(line)
            stripped = line.rstrip()
            transient_text.plain = stripped[-200:]

            if parser is not None:
                update = parser(line)
                if update is not None:
                    if update.total is not None:
                        progress.update(task_id, total=update.total)
                    if update.completed is not None:
                        current = update.completed
                        progress.update(task_id, completed=current)
                    if update.description is not None:
                        progress.update(task_id, description=update.description)
                    if update.log is not None:
                        style, text = update.log
                        live.console.print(f"  [{style}]{text}[/{style}]")
            live.update(group)

        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            raise

        # Marca completo si la barra tenía total
        if total is not None or progress.tasks[0].total is not None:
            total_final = progress.tasks[0].total
            progress.update(task_id, completed=total_final)

    return proc.returncode, captured


def tail_subprocess(
    cmd: list[str],
    *,
    formatter: Callable[[str], str] | None = None,
    cwd: str | None = None,
) -> int:
    """Ejecuta `cmd` y reimprime cada línea aplicando opcionalmente `formatter`.

    Pensado para procesos potencialmente infinitos (`--follow`). No usa Live ni
    Progress. Maneja Ctrl+C devolviendo 130. El formatter recibe la línea cruda
    y devuelve el texto a imprimir (puede incluir markup Rich).
    """
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=cwd,
        text=True,
        bufsize=1,
    )
    assert proc.stdout is not None

    try:
        for line in proc.stdout:
            text = line.rstrip("\n")
            if formatter is not None:
                text = formatter(text)
            console.print(text, highlight=False, markup=True)
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        return 130

    return proc.returncode
