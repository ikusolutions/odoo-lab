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


def clone_repo(
    url: str, dest: Path, branch: str, label: str, fallback_to_default: bool = False
) -> bool:
    with console.status(f"  Clonando {label}...", spinner="dots"):
        result = run_cmd(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--no-single-branch",
                "--branch",
                branch,
                url,
                str(dest),
            ],
            timeout=300,
        )
    if result.returncode == 0:
        console.print(f"  [green]✓[/green] {label} clonado correctamente")
        return True

    if fallback_to_default and "not found" in result.stderr:
        console.print(
            f"  [yellow]⚠[/yellow] Branch '{branch}' no encontrado, clonando rama por defecto..."
        )
        with console.status(
            f"  Clonando {label} (rama por defecto)...", spinner="dots"
        ):
            result = run_cmd(
                ["git", "clone", "--depth", "1", "--no-single-branch", url, str(dest)],
                timeout=300,
            )
        if result.returncode == 0:
            console.print(f"  [green]✓[/green] {label} clonado (rama por defecto)")
            return True

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


def detect_addon_dirs(path: Path) -> list[Path]:
    """Find all directories that are valid Odoo addons containers under path.

    A valid addons container directly contains at least one Odoo module
    (a directory with __manifest__.py or __openerp__.py).

    Scans up to 3 levels deep to handle structures like:
      path/src/module/__manifest__.py        → src
      path/vendor/OCA/module/__manifest__.py → vendor/OCA
      path/module/__manifest__.py            → path itself
    """
    if not path.exists() or not path.is_dir():
        return []

    MANIFEST_FILES = {"__manifest__.py", "__openerp__.py"}
    found: set[Path] = set()

    def _has_module(directory: Path) -> bool:
        """True if directory directly contains at least one Odoo module."""
        try:
            for child in directory.iterdir():
                if child.is_dir():
                    for mf in MANIFEST_FILES:
                        if (child / mf).exists():
                            return True
        except PermissionError:
            pass
        return False

    def _subdirs(d: Path) -> list[Path]:
        try:
            return [c for c in d.iterdir() if c.is_dir() and not c.name.startswith(".")]
        except PermissionError:
            return []

    # Depth 0, 1, 2 relative to path
    for d0 in [path] + _subdirs(path):
        if _has_module(d0):
            found.add(d0)
        if d0 != path:
            for d1 in _subdirs(d0):
                if _has_module(d1):
                    found.add(d1)

    return sorted(found)


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
