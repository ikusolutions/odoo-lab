ODOO_VERSIONS = {
    "16": {"python": "3.10", "postgres_min": "16"},
    "17": {"python": "3.10", "postgres_min": "16"},
    "18": {"python": "3.11", "postgres_min": "16"},
    "19": {"python": "3.11", "postgres_min": "16"},
}


def normalize_version(version: str) -> str:
    """Normalize version input: '19', '19.0' -> '19'."""
    return version.split(".")[0]


def is_valid_version(version: str) -> bool:
    """Check if a version (normalized or not) is supported."""
    return normalize_version(version) in ODOO_VERSIONS


def get_python_version(odoo_version: str) -> str:
    return ODOO_VERSIONS[normalize_version(odoo_version)]["python"]


def get_postgres_min(odoo_version: str) -> str:
    return ODOO_VERSIONS[normalize_version(odoo_version)]["postgres_min"]


def get_venv_name(odoo_version: str) -> str:
    """Get the venv directory name. E.g. '.venv-v19'."""
    return f".venv-v{normalize_version(odoo_version)}"


def get_branch_name(odoo_version: str) -> str:
    """Get the git branch name. E.g. '19.0'."""
    return f"{normalize_version(odoo_version)}.0"


def available_versions() -> list[str]:
    """Return list of supported Odoo versions (major only)."""
    return sorted(ODOO_VERSIONS.keys(), key=int)
