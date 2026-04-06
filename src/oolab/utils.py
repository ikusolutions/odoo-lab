import re
import shutil
import subprocess
import unicodedata
from pathlib import Path

from rich.console import Console

console = Console()


def run_cmd(
    cmd: list[str], cwd: str | None = None, timeout: int = 120
) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")


def clone_repo(url: str, dest: Path, branch: str, label: str) -> bool:
    with console.status(f"  Clonando {label}...", spinner="dots"):
        result = run_cmd(
            ["git", "clone", "--depth", "1", "--no-single-branch", "--branch", branch, url, str(dest)],
            timeout=300,
        )
    if result.returncode == 0:
        console.print(f"  [green]✓[/green] {label} clonado correctamente")
        return True
    else:
        console.print(f"  [red]✗[/red] Error clonando {label}: {result.stderr.strip()}")
        return False


def copy_local(src: str, dest: Path, label: str) -> bool:
    src_path = Path(src).expanduser().resolve()
    if not src_path.exists():
        console.print(f"  [red]✗[/red] Path no existe: {src_path}")
        return False
    with console.status(f"  Copiando {label}...", spinner="dots"):
        shutil.copytree(src_path, dest, dirs_exist_ok=True)
    console.print(f"  [green]✓[/green] {label} copiado")
    return True


def get_current_branch(repo_path: Path) -> str:
    result = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(repo_path))
    return result.stdout.strip() if result.returncode == 0 else ""


def ensure_branch(repo_path: Path, target_branch: str, label: str):
    current = get_current_branch(repo_path)
    if current == target_branch:
        console.print(f"  [green]✓[/green] {label} en branch {target_branch}")
        return

    console.print(
        f"  [blue]ℹ[/blue] {label} en branch [yellow]{current}[/yellow], cambiando a [cyan]{target_branch}[/cyan]..."
    )

    with console.status(f"  Cambiando {label} a {target_branch}...", spinner="dots"):
        run_cmd(
            ["git", "fetch", "--depth", "1", "origin", target_branch],
            cwd=str(repo_path),
            timeout=300,
        )
        result = run_cmd(["git", "checkout", target_branch], cwd=str(repo_path))

        if result.returncode != 0:
            result = run_cmd(
                ["git", "checkout", "-b", target_branch, f"origin/{target_branch}"],
                cwd=str(repo_path),
            )

    if result.returncode == 0:
        console.print(f"  [green]✓[/green] {label} cambiado a branch {target_branch}")
    else:
        console.print(
            f"  [red]✗[/red] No se pudo cambiar {label} a branch {target_branch}"
        )
        console.print(f"  [dim]  {result.stderr.strip()}[/dim]")
