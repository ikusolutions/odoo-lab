import json

import typer
from rich.console import Console
from rich.table import Table

from oolab.cli import app
from oolab.config import WorkspaceConfig, find_workspace
from oolab.utils import get_current_branch, run_cmd

console = Console()


@app.command()
def status():
    """Mostrar el estado del workspace: servicios Docker, ramas y tenants."""
    try:
        workspace_path = find_workspace()
    except FileNotFoundError as e:
        console.print(f"\n  [red]✗ {e}[/red]\n")
        raise typer.Exit(1) from None

    config = WorkspaceConfig.load(workspace_path)
    compose_file = str(workspace_path / "docker" / "docker-compose.yaml")
    edition = "Community + Enterprise" if config.enterprise_enabled else "Community"

    console.print(f"\n  [bold]{config.name}[/bold] — Odoo {config.odoo_version}.0 ({edition})\n")

    # Docker services
    docker_table = Table(title="Servicios Docker", show_header=True, header_style="bold")
    docker_table.add_column("Servicio", style="cyan", width=16)
    docker_table.add_column("Estado", width=14)
    docker_table.add_column("Puerto", style="dim")

    if (workspace_path / "docker" / "docker-compose.yaml").exists():
        result = run_cmd(
            ["docker", "compose", "-f", compose_file, "ps", "--format", "json"],
            timeout=15,
        )
        if result.returncode == 0 and result.stdout.strip():
            try:
                containers = json.loads(result.stdout)
                if isinstance(containers, dict):
                    containers = [containers]
                for c in containers:
                    name = c.get("Service", c.get("Name", "?"))
                    state = c.get("State", "unknown")
                    status_str = "[green]corriendo[/green]" if state == "running" else f"[red]{state}[/red]"
                    publishers = c.get("Publishers", [])
                    ports = ", ".join(
                        f"{p['PublishedPort']}" for p in publishers
                        if p.get("PublishedPort", 0) > 0
                    ) if publishers else "-"
                    docker_table.add_row(name, status_str, ports)
            except (json.JSONDecodeError, TypeError):
                docker_table.add_row("-", "[yellow]no se pudo leer[/yellow]", "-")
        else:
            docker_table.add_row("-", "[dim]detenido[/dim]", "-")
    else:
        docker_table.add_row("-", "[red]sin configurar[/red]", "-")

    console.print(docker_table)

    # Git branches
    console.print("\n  [bold]Repositorios:[/bold]")
    odoo_path = workspace_path / "odoo"
    if odoo_path.exists():
        branch = get_current_branch(odoo_path)
        console.print(f"    odoo/          → [cyan]{branch or '?'}[/cyan]")

    if config.enterprise_enabled:
        ent_path = workspace_path / "enterprise"
        if ent_path.exists():
            branch = get_current_branch(ent_path)
            console.print(f"    enterprise/    → [cyan]{branch or '?'}[/cyan]")

    # Tenants
    if config.tenants:
        tenant_table = Table(title="Tenants", show_header=True, header_style="bold")
        tenant_table.add_column("Nombre", style="cyan")
        tenant_table.add_column("Branch", style="dim")
        tenant_table.add_column("Enterprise")
        tenant_table.add_column("Estado")

        for tenant in config.tenants:
            tenant_path = workspace_path / "tenants" / tenant.name
            exists = tenant_path.exists()
            estado = "[green]✓[/green]" if exists else "[red]✗ faltante[/red]"
            ent = "[magenta]sí[/magenta]" if tenant.enterprise else "no"
            branch = ""
            if exists and (tenant_path / ".git").exists():
                branch = get_current_branch(tenant_path) or tenant.branch
            else:
                branch = tenant.branch
            tenant_table.add_row(tenant.name, branch, ent, estado)

        console.print()
        console.print(tenant_table)

    console.print()
