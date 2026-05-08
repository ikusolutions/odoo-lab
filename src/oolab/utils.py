import re
import shutil
import subprocess
import unicodedata
from pathlib import Path

from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from oolab.console import ERR, OK, WARN, console
from oolab.progress import step_spinner


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


_GIT_PROGRESS_RE = re.compile(
    r"(?P<phase>Receiving objects|Resolving deltas|Counting objects|Compressing objects):\s+(?P<percent>\d+)%"
)


def _git_clone_with_progress(
    cmd: list[str], label: str, timeout: int = 300
) -> tuple[int, str]:
    """Ejecuta git clone con --progress y muestra una barra Rich basada en el output.

    Returns: (returncode, stderr_text)
    """
    full_cmd = cmd + ["--progress"]

    if not console.is_terminal:
        result = subprocess.run(
            full_cmd, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode, result.stderr

    columns = [
        SpinnerColumn(style="accent"),
        TextColumn(f"[bold]Clonando {label}[/bold]"),
        TextColumn("[muted]·[/muted]"),
        TextColumn("[accent]{task.fields[phase]}[/accent]"),
        BarColumn(bar_width=None, complete_style="accent", finished_style="success"),
        TaskProgressColumn(),
        TextColumn("[muted]·[/muted]"),
        TimeElapsedColumn(),
    ]

    stderr_buf: list[str] = []
    with Progress(*columns, console=console, transient=True, expand=True) as progress:
        task = progress.add_task("clone", total=100, phase="iniciando")
        proc = subprocess.Popen(
            full_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        assert proc.stderr is not None
        for line in proc.stderr:
            stderr_buf.append(line)
            match = _GIT_PROGRESS_RE.search(line)
            if match:
                progress.update(
                    task,
                    completed=int(match.group("percent")),
                    phase=match.group("phase"),
                )
        proc.wait(timeout=timeout)
        progress.update(
            task, completed=100, phase="listo" if proc.returncode == 0 else "error"
        )

    return proc.returncode, "".join(stderr_buf)


def clone_repo(
    url: str, dest: Path, branch: str, label: str, fallback_to_default: bool = False
) -> bool:
    base_cmd = [
        "git",
        "clone",
        "--depth",
        "1",
        "--no-single-branch",
        "--branch",
        branch,
        url,
        str(dest),
    ]
    rc, stderr = _git_clone_with_progress(base_cmd, label)
    if rc == 0:
        console.print(f"  {OK} {label} clonado correctamente")
        return True

    if fallback_to_default and "not found" in stderr:
        console.print(
            f"  {WARN} Branch '{branch}' no encontrado, clonando rama por defecto..."
        )
        fallback_cmd = [
            "git",
            "clone",
            "--depth",
            "1",
            "--no-single-branch",
            url,
            str(dest),
        ]
        rc, stderr = _git_clone_with_progress(fallback_cmd, f"{label} (default)")
        if rc == 0:
            console.print(f"  {OK} {label} clonado (rama por defecto)")
            return True

    console.print(f"  {ERR} Error clonando {label}: {stderr.strip()[:300]}")
    return False


def copy_local(src: str, dest: Path, label: str) -> bool:
    src_path = Path(src).expanduser().resolve()
    if not src_path.exists():
        console.print(f"  {ERR} Path no existe: {src_path}")
        return False
    with step_spinner(f"Copiando {label}..."):
        shutil.copytree(src_path, dest, dirs_exist_ok=True)
    console.print(f"  {OK} {label} copiado")
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
        console.print(f"  {OK} {label} en branch {target_branch}")
        return

    console.print(
        f"  [info_mark]ℹ[/info_mark] {label} en branch [warn]{current}[/warn], cambiando a [accent]{target_branch}[/accent]..."
    )

    with step_spinner(f"Cambiando {label} a {target_branch}..."):
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
        console.print(f"  {OK} {label} cambiado a branch {target_branch}")
    else:
        console.print(f"  {ERR} No se pudo cambiar {label} a branch {target_branch}")
        console.print(f"  [muted]  {result.stderr.strip()}[/muted]")
