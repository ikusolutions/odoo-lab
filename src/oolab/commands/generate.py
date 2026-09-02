import platform
import sys
from pathlib import Path

import typer
from jinja2 import Environment, PackageLoader, select_autoescape

from oolab import __version__ as oolab_version
from oolab.cli import app
from oolab.config import WorkspaceConfig, find_workspace
from oolab.console import ERR, OK, console
from oolab.utils import detect_addon_dirs


def get_platform_arch() -> str:
    """Detect platform architecture for Docker images."""
    machine = platform.machine().lower()
    if machine in ("arm64", "aarch64"):
        return "arm64"
    return "amd64"


# Archivos JSON de VSCode cuyos paths deben usar el separador del SO.
WINDOWS_PATH_TEMPLATES = {"launch.json.j2", "settings.json.j2"}


def _to_win_paths(content: str) -> str:
    """En Windows, VSCode y odoo-bin necesitan `\\\\` en los paths. Todos los `/`
    de estos JSON son separadores de ruta, así que se convierten a doble
    backslash (JSON válido = un backslash real)."""
    return content.replace("/", "\\\\")


def get_template_env() -> Environment:
    return Environment(
        loader=PackageLoader("oolab", "templates"),
        autoescape=select_autoescape([]),
        keep_trailing_newline=True,
    )


def render_and_write(
    env: Environment,
    template_name: str,
    output_path: Path,
    context: dict,
    is_windows: bool = False,
):
    """Render a template and write to the output path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    template = env.get_template(template_name)
    content = template.render(**context)
    if is_windows and template_name in WINDOWS_PATH_TEMPLATES:
        content = _to_win_paths(content)
    output_path.write_text(content, encoding="utf-8")


def generate_all(workspace_path: Path, config: WorkspaceConfig):
    """Generate all config files from templates."""
    env = get_template_env()

    has_enterprise = config.enterprise_enabled or any(
        t.enterprise for t in config.tenants
    )

    is_windows = sys.platform == "win32"

    context = {
        "name": config.name,
        "odoo_version": config.odoo_version,
        "enterprise_enabled": config.enterprise_enabled,
        "has_enterprise": has_enterprise,
        "enterprise_path": config.enterprise_path,
        "python_version": config.python_version,
        "venv_name": config.venv_name,
        "postgres_version": config.postgres_version,
        "postgres_port": config.postgres_port,
        "postgres_user": config.postgres_user,
        "postgres_password": config.postgres_password,
        "nginx_enabled": config.nginx_enabled,
        "nginx_http_port": config.nginx_http_port,
        "tenants": [
            {
                **t.to_dict(),
                "addon_paths": [
                    p.relative_to(workspace_path).as_posix()
                    for p in detect_addon_dirs(workspace_path / "tenants" / t.name)
                ],
            }
            for t in config.tenants
        ],
        "platform": get_platform_arch(),
        "is_windows": is_windows,
        "oolab_version": oolab_version,
    }

    files = [
        ("odoo.conf.j2", workspace_path / "config" / "odoo" / "odoo.conf"),
        ("launch.json.j2", workspace_path / ".vscode" / "launch.json"),
        ("settings.json.j2", workspace_path / ".vscode" / "settings.json"),
        ("tasks.json.j2", workspace_path / ".vscode" / "tasks.json"),
        ("extensions.json.j2", workspace_path / ".vscode" / "extensions.json"),
        ("docker-compose.yaml.j2", workspace_path / "docker" / "docker-compose.yaml"),
        ("nginx.conf.j2", workspace_path / "config" / "nginx" / "nginx.conf"),
        ("env.j2", workspace_path / ".env"),
        ("README.md.j2", workspace_path / "README.md"),
    ]

    for template_name, output_path in files:
        render_and_write(env, template_name, output_path, context, is_windows)
        rel_path = output_path.relative_to(workspace_path)
        console.print(f"  {OK} {rel_path}")


@app.command()
def generate():
    """Regenera odoo.conf, docker-compose, launch.json y demás configs a partir de oolab.yaml."""
    try:
        workspace_path = find_workspace()
    except FileNotFoundError as e:
        console.print(f"\n  {ERR} {e}\n")
        raise typer.Exit(1) from None

    config = WorkspaceConfig.load(workspace_path)

    console.print("\n  [heading]Generando configuraciones...[/heading]\n")
    generate_all(workspace_path, config)
    console.print("\n  [success]Configuraciones generadas correctamente.[/success]\n")
