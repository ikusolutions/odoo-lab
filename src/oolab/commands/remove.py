import shutil

import typer
from rich.prompt import Confirm

from oolab.cli import app
from oolab.commands.generate import generate_all
from oolab.config import WorkspaceConfig, find_workspace
from oolab.console import ERR, OK, console


@app.command()
def remove(
    name: str = typer.Argument(help="Nombre del proyecto a eliminar"),
):
    """Elimina un proyecto del workspace: borra el directorio y lo quita de oolab.yaml."""
    try:
        workspace_path = find_workspace()
    except FileNotFoundError as e:
        console.print(f"\n  {ERR} {e}\n")
        raise typer.Exit(1) from None

    config = WorkspaceConfig.load(workspace_path)

    # Find tenant
    tenant = next((t for t in config.tenants if t.name == name), None)
    if not tenant:
        console.print(f"\n  {ERR} Proyecto '{name}' no encontrado.\n")
        console.print("  Proyectos disponibles:")
        for t in config.tenants:
            console.print(f"    - {t.name}")
        console.print()
        raise typer.Exit(1) from None

    # Confirm
    console.print(
        f"\n  Eliminando proyecto: [bold]{tenant.display_name}[/bold] ({name})"
    )

    tenant_path = workspace_path / "tenants" / name
    if tenant_path.exists():
        delete_files = Confirm.ask(
            f"  ¿Eliminar también el directorio tenants/{name}/?",
            default=False,
        )
        if delete_files:
            shutil.rmtree(tenant_path)
            console.print(f"  {OK} Directorio tenants/{name}/ eliminado")
        else:
            console.print(f"  [muted]  Directorio tenants/{name}/ conservado[/muted]")

    # Update config
    config.tenants = [t for t in config.tenants if t.name != name]
    config.save(workspace_path)
    console.print(f"  {OK} Proyecto eliminado de oolab.yaml")

    # Regenerate configs
    console.print("\n  [heading]Regenerando configuraciones...[/heading]\n")
    generate_all(workspace_path, config)
    console.print(
        f"\n  [success]Proyecto '{name}' eliminado correctamente.[/success]\n"
    )
