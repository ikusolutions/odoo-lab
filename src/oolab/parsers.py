"""
odoo-lab (oolab) - Copyright (c) 2026 IKU Solutions SAS

Parsers para stream_subprocess: extraen progreso, descripción y logs
relevantes de la salida cruda de comandos externos.
"""

import re

from oolab.streaming import StreamUpdate

# 2026-01-15 10:23:45,123 12345 INFO testdb odoo.modules.loading: msg
_ODOO_LOG_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}\s+[\d:,]+\s+\d+\s+(?P<level>\w+)\s+(?P<db>\S+)\s+(?P<logger>[\w\.]+):\s+(?P<msg>.*)$"
)
_ODOO_LOADING_N = re.compile(r"loading\s+(\d+)\s+modules?", re.IGNORECASE)
_ODOO_LOADED_N = re.compile(r"^(\d+)\s+modules?\s+loaded", re.IGNORECASE)
_ODOO_MODULE_OP = re.compile(
    r"module\s+(?P<mod>[\w\.]+):\s*(?P<action>creating or updating database tables|loading|loaded)",
    re.IGNORECASE,
)


def odoo_module_parser() -> "callable":
    """Devuelve un parser stateful para `odoo-bin -i/-u`.

    Detecta:
      - "loading N modules" → fija total
      - "module xxx: ..." → descripción transitoria + avanza contador
      - WARNING/ERROR/CRITICAL → log persistente coloreado
    """
    state = {"loaded_modules": set()}

    def parse(line: str) -> StreamUpdate | None:
        match = _ODOO_LOG_RE.match(line)
        if not match:
            return None

        level = match.group("level")
        msg = match.group("msg")
        update = StreamUpdate()

        # Total inicial
        n_match = _ODOO_LOADING_N.search(msg)
        if n_match:
            update.total = int(n_match.group(1))

        # Avance por módulo
        mod_match = _ODOO_MODULE_OP.search(msg)
        if mod_match:
            mod = mod_match.group("mod")
            action = mod_match.group("action").lower()
            if action == "loaded" and mod not in state["loaded_modules"]:
                state["loaded_modules"].add(mod)
                update.completed = len(state["loaded_modules"])
            update.description = f"módulo: [accent]{mod}[/accent]"

        # Logs relevantes
        if level == "WARNING":
            update.log = ("warn", line.rstrip())
        elif level in ("ERROR", "CRITICAL"):
            update.log = ("error", line.rstrip())

        return (
            update
            if any(
                v is not None
                for v in (
                    update.total,
                    update.completed,
                    update.description,
                    update.log,
                )
            )
            else None
        )

    return parse


_DOCKER_STEP_RE = re.compile(r"^\s*(?:Step|=>|\[\+\])\s+(.*)$")


def docker_compose_parser(line: str) -> StreamUpdate | None:
    """Parser ligero para docker compose: usa la línea cruda como descripción."""
    stripped = line.rstrip()
    if not stripped:
        return None
    return StreamUpdate(description=stripped[-120:])


# docker compose logs prefix: "service-1  | rest of line"
_COMPOSE_PREFIX_RE = re.compile(r"^(?P<svc>[\w\-]+)(?:[\-_]\d+)?\s*\|\s?(?P<rest>.*)$")
_PG_LEVEL_RE = re.compile(
    r"\b(LOG|HINT|DETAIL|STATEMENT|NOTICE|WARNING|ERROR|FATAL|PANIC):"
)
_NGINX_LEVEL_RE = re.compile(r"\[(error|warn|crit|alert|emerg)\]", re.IGNORECASE)
_ODOO_LINE_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}[,.]?\d*\s+\d+\s+(?P<level>\w+)\s+"
)


def _level_style(level: str) -> str:
    level = level.upper()
    if level in ("FATAL", "PANIC", "CRITICAL", "ERROR", "EMERG", "ALERT", "CRIT"):
        return "error"
    if level in ("WARNING", "WARN"):
        return "warn"
    if level in ("NOTICE", "INFO"):
        return "info"
    if level in ("LOG", "DETAIL", "HINT", "STATEMENT", "DEBUG"):
        return "muted"
    return ""


def _service_style(svc: str) -> str:
    palette = ["accent", "info", "warn", "brand", "success"]
    return palette[hash(svc) % len(palette)]


def docker_logs_formatter(line: str) -> str:
    """Formatea una línea de `docker compose logs`.

    Colorea el prefijo de servicio y resalta niveles PG / Odoo / Nginx.
    """
    if not line.strip():
        return line

    match = _COMPOSE_PREFIX_RE.match(line)
    if match:
        svc = match.group("svc")
        rest = match.group("rest")
        prefix = f"[{_service_style(svc)}]{svc:<10}[/]│ "
    else:
        rest = line
        prefix = ""

    pg_match = _PG_LEVEL_RE.search(rest)
    if pg_match:
        level = pg_match.group(1)
        style = _level_style(level)
        if style:
            rest = rest.replace(f"{level}:", f"[{style}]{level}:[/{style}]", 1)
        return prefix + rest

    nginx_match = _NGINX_LEVEL_RE.search(rest)
    if nginx_match:
        level = nginx_match.group(1)
        style = _level_style(level)
        if style:
            rest = rest.replace(f"[{level}]", f"[{style}]\\[{level}][/{style}]", 1)
        return prefix + rest

    odoo_match = _ODOO_LINE_RE.match(rest)
    if odoo_match:
        level = odoo_match.group("level")
        style = _level_style(level)
        if style:
            rest = rest.replace(level, f"[{style}]{level}[/{style}]", 1)
        return prefix + rest

    return prefix + rest
