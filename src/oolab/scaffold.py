"""OCA-style scaffold for new empty tenant repositories."""

from pathlib import Path

from oolab.versions import normalize_version

LICENSE_LGPL3 = """\
GNU LESSER GENERAL PUBLIC LICENSE
Version 3, 29 June 2007

https://www.gnu.org/licenses/lgpl-3.0.en.html
"""

EDITORCONFIG = """\
root = true

[*]
charset = utf-8
end_of_line = lf
indent_size = 4
indent_style = space
insert_final_newline = true
trim_trailing_whitespace = true

[*.{xml,html,yml,yaml,json,css,scss,js}]
indent_size = 2

[*.md]
trim_trailing_whitespace = false

[Makefile]
indent_style = tab
"""

GITIGNORE_OCA = """\
# Byte-compiled
__pycache__/
*.py[cod]
*$py.class
*.so

# Distribution
*.egg-info/
*.egg
dist/
build/

# IDE
.idea/
.vscode/
*.sw?

# OS
.DS_Store
Thumbs.db

# Testing
.tox/
.coverage
htmlcov/
.pytest_cache/

# Odoo
*.pyc
filestore/
"""

GITATTRIBUTES = """\
# Auto detect text files and perform LF normalization
* text=auto

# Explicitly declare text files
*.py text diff=python
*.xml text
*.csv text
*.js text
*.css text
*.html text
*.md text
*.txt text
*.yml text
*.yaml text

# Declare binary files
*.png binary
*.jpg binary
*.gif binary
*.ico binary
*.pdf binary
"""


def _pre_commit_config(odoo_major: int) -> str:
    """Generate .pre-commit-config.yaml based on Odoo version."""
    if odoo_major >= 17:
        return """\
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-case-conflict
      - id: check-docstring-first
      - id: check-merge-conflict
      - id: check-xml
      - id: debug-statements
      - id: end-of-file-fixer
      - id: fix-encoding-pragma
        args: ["--remove"]
      - id: mixed-line-ending
        args: ["--fix=lf"]
      - id: trailing-whitespace

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.8
    hooks:
      - id: ruff
        args: [--exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.3.3
    hooks:
      - id: prettier
        types_or: [css, xml]
"""
    else:
        return """\
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-case-conflict
      - id: check-docstring-first
      - id: check-merge-conflict
      - id: check-xml
      - id: debug-statements
      - id: end-of-file-fixer
      - id: fix-encoding-pragma
        args: ["--remove"]
      - id: mixed-line-ending
        args: ["--fix=lf"]
      - id: trailing-whitespace

  - repo: https://github.com/psf/black
    rev: "23.9.1"
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: "5.12.0"
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: "6.1.0"
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v2.7.1
    hooks:
      - id: prettier
        types_or: [css, xml]
"""


def _ruff_toml(odoo_major: int) -> str:
    target = "py310" if odoo_major <= 17 else "py311"
    return f"""\
line-length = 88

[lint]
select = ["E", "F", "W", "I", "B", "C4", "UP"]

[lint.isort]
known-first-party = ["odoo", "odoo.addons"]

[format]
target-version = "{target}"
"""


def _pylintrc() -> str:
    return """\
[MASTER]
load-plugins=pylint_odoo

[FORMAT]
max-line-length=88

[MESSAGES CONTROL]
disable=C0114,C0115,C0116
"""


def _readme(tenant_name: str, odoo_branch: str) -> str:
    return f"""\
# {tenant_name}

Custom Odoo addons for Odoo {odoo_branch}.

## Usage

Place your custom modules in this directory. Each module should have its own
subdirectory with the standard Odoo module structure:

```
my_module/
├── __init__.py
├── __manifest__.py
├── models/
├── views/
├── security/
├── data/
└── static/
```

## Development

Install pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```
"""


def scaffold_tenant(tenant_path: Path, tenant_name: str, odoo_version: str):
    """Create OCA-style scaffold files in a new empty tenant directory."""
    odoo_major = int(normalize_version(odoo_version))
    odoo_branch = f"{odoo_major}.0"

    tenant_path.mkdir(parents=True, exist_ok=True)

    # Core files
    (tenant_path / ".editorconfig").write_text(EDITORCONFIG)
    (tenant_path / ".gitignore").write_text(GITIGNORE_OCA)
    (tenant_path / ".gitattributes").write_text(GITATTRIBUTES)
    (tenant_path / "LICENSE").write_text(LICENSE_LGPL3)
    (tenant_path / "README.md").write_text(_readme(tenant_name, odoo_branch))
    (tenant_path / "requirements.txt").write_text("")

    # Quality tools
    (tenant_path / ".pre-commit-config.yaml").write_text(_pre_commit_config(odoo_major))
    (tenant_path / ".pylintrc").write_text(_pylintrc())

    # Ruff for 17.0+
    if odoo_major >= 17:
        (tenant_path / ".ruff.toml").write_text(_ruff_toml(odoo_major))
