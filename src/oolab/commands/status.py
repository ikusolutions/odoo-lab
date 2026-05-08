import json

import typer
from rich.tree import Tree

from oolab.cli import app
from oolab.config import WorkspaceConfig, find_workspace
from oolab.console import ERR, console
from oolab.utils import get_current_branch, run_cmd


def _docker_status(workspace_path, compose_file: str) -> list[tuple[str, str, str]]:
    """Devuelve [(servicio, estado, puerto), ...] o lista vacía."""
    if not (workspace_path / "docker" / "docker-compose.yaml").exists():
        return []
    result = run_cmd(
        ["docker", "compose", "-f", compose_file, "ps", "--format", "json"],
        timeout=15,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return []
    try:
        containers = json.loads(result.stdout)
    except (json.JSONDecodeError, TypeError):
        return []
    if isinstance(containers, dict):
        containers = [containers]

    rows: list[tuple[str, str, str]] = []
    for c in containers:
        name = c.get("Service", c.get("Name", "?"))
        state = c.get("State", "unknown")
        publishers = c.get("Publishers", []) or []
        ports = (
            ", ".join(
                str(p["PublishedPort"])
                for p in publishers
                if p.get("PublishedPort", 0) > 0
            )
            or "-"
        )
        rows.append((name, state, ports))
    return rows


@app.command()
def status():
    """Muestra el estado completo del workspace: servicios Docker activos, branches de git y tenants configurados."""
    try:
        workspace_path = find_workspace()
    except FileNotFoundError as e:
        console.print(f"\n  {ERR} {e}\n")
        raise typer.Exit(1) from None

    config = WorkspaceConfig.load(workspace_path)
    compose_file = str(workspace_path / "docker" / "docker-compose.yaml")
    edition = "Community + Enterprise" if config.enterprise_enabled else "Community"

    root = Tree(
        f"[brand]{config.name}[/brand]  [muted]·[/muted]  Odoo {config.odoo_version}.0  "
        f"[muted]·[/muted]  {edition}",
        guide_style="muted",
    )

    # Docker
    docker_branch = root.add("[heading]Servicios Docker[/heading]")
    docker_rows = _docker_status(workspace_path, compose_file)
    if not (workspace_path / "docker" / "docker-compose.yaml").exists():
        docker_branch.add("[error]sin configurar[/error]")
    elif not docker_rows:
        docker_branch.add("[muted]detenido[/muted]")
    else:
        for name, state, ports in docker_rows:
            state_str = (
                f"[success]{state}[/success]"
                if state == "running"
                else f"[error]{state}[/error]"
            )
            ports_str = f"  [muted]·  puerto {ports}[/muted]" if ports != "-" else ""
            docker_branch.add(f"[accent]{name}[/accent]  {state_str}{ports_str}")

    # Repos
    repos_branch = root.add("[heading]Repositorios[/heading]")
    odoo_path = workspace_path / "odoo"
    if odoo_path.exists():
        branch = get_current_branch(odoo_path) or "?"
        repos_branch.add(f"odoo/  →  [accent]{branch}[/accent]")
    else:
        repos_branch.add("[muted]odoo/ no clonado[/muted]")

    if config.enterprise_enabled:
        ent_path = workspace_path / "enterprise"
        if ent_path.exists():
            branch = get_current_branch(ent_path) or "?"
            repos_branch.add(f"enterprise/  →  [accent]{branch}[/accent]")
        else:
            repos_branch.add("[muted]enterprise/ no clonado[/muted]")

    # Tenants
    tenants_branch = root.add(
        f"[heading]Tenants[/heading]  [muted]({len(config.tenants)})[/muted]"
    )
    if not config.tenants:
        tenants_branch.add(
            "[muted]sin proyectos · usa [accent]oolab add[/accent][/muted]"
        )
    else:
        for tenant in config.tenants:
            tenant_path = workspace_path / "tenants" / tenant.name
            exists = tenant_path.exists()
            if exists and (tenant_path / ".git").exists():
                branch = get_current_branch(tenant_path) or tenant.branch
            else:
                branch = tenant.branch
            mark = "[success]✓[/success]" if exists else "[error]✗ faltante[/error]"
            ent = "  [warn](Enterprise)[/warn]" if tenant.enterprise else ""
            tenants_branch.add(
                f"{mark}  [accent]{tenant.name}[/accent]  [muted]·  rama {branch}[/muted]{ent}"
            )

    console.print()
    console.print(root)
    console.print()
