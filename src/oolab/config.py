from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from oolab.versions import (
    get_branch_name,
    get_postgres_min,
    get_python_version,
    get_venv_name,
    normalize_version,
)

CONFIG_FILENAME = "oolab.yaml"


@dataclass
class Tenant:
    name: str
    display_name: str
    url: str = ""
    branch: str = ""
    db_filter: str = ""
    enterprise: bool = False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "url": self.url,
            "branch": self.branch,
            "db_filter": self.db_filter,
            "enterprise": self.enterprise,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Tenant:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class WorkspaceConfig:
    name: str = "odoo-launchpad"
    config_version: str = "1"
    odoo_version: str = "19.0"
    community_url: str = "https://github.com/odoo/odoo.git"
    enterprise_enabled: bool = False
    enterprise_source: str = "git"  # "git" | "local"
    enterprise_url: str = ""
    enterprise_path: str = "./enterprise"
    python_version: str = ""
    venv_name: str = ""
    postgres_version: str = ""
    postgres_port: int = 5432
    postgres_user: str = "odoo"
    postgres_password: str = "myodoo"
    nginx_enabled: bool = True
    nginx_http_port: int = 80
    tenants: list[Tenant] = field(default_factory=list)

    def __post_init__(self):
        if not self.python_version:
            self.python_version = get_python_version(self.odoo_version)
        if not self.venv_name:
            self.venv_name = get_venv_name(self.odoo_version)
        if not self.postgres_version:
            self.postgres_version = get_postgres_min(self.odoo_version)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.config_version,
            "odoo": {
                "version": get_branch_name(self.odoo_version),
                "community_url": self.community_url,
                "enterprise": {
                    "enabled": self.enterprise_enabled,
                    "source": self.enterprise_source,
                    "url": self.enterprise_url,
                    "path": self.enterprise_path,
                },
            },
            "python": {
                "version": self.python_version,
                "venv": self.venv_name,
            },
            "docker": {
                "postgres": {
                    "version": self.postgres_version,
                    "port": self.postgres_port,
                    "user": self.postgres_user,
                    "password": self.postgres_password,
                },
                "nginx": {
                    "enabled": self.nginx_enabled,
                    "http_port": self.nginx_http_port,
                },
            },
            "tenants": [t.to_dict() for t in self.tenants],
        }

    @classmethod
    def from_dict(cls, data: dict) -> WorkspaceConfig:
        odoo = data.get("odoo", {})
        enterprise = odoo.get("enterprise", {})
        python_cfg = data.get("python", {})
        docker = data.get("docker", {})
        postgres = docker.get("postgres", {})
        nginx = docker.get("nginx", {})
        tenants_data = data.get("tenants", [])

        return cls(
            name=data.get("name", "odoo-launchpad"),
            config_version=data.get("version", "1"),
            odoo_version=normalize_version(odoo.get("version", "19.0")),
            community_url=odoo.get("community_url", "https://github.com/odoo/odoo.git"),
            enterprise_enabled=enterprise.get("enabled", False),
            enterprise_source=enterprise.get("source", "git"),
            enterprise_url=enterprise.get("url", ""),
            enterprise_path=enterprise.get("path", "./enterprise"),
            python_version=python_cfg.get("version", ""),
            venv_name=python_cfg.get("venv", ""),
            postgres_version=postgres.get("version", ""),
            postgres_port=postgres.get("port", 5432),
            postgres_user=postgres.get("user", "odoo"),
            postgres_password=postgres.get("password", "myodoo"),
            nginx_enabled=nginx.get("enabled", True),
            nginx_http_port=nginx.get("http_port", 80),
            tenants=[Tenant.from_dict(t) for t in tenants_data],
        )

    def save(self, workspace_path: Path):
        config_path = workspace_path / CONFIG_FILENAME
        with open(config_path, "w") as f:
            yaml.dump(
                self.to_dict(),
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )

    @classmethod
    def load(cls, workspace_path: Path) -> WorkspaceConfig:
        config_path = workspace_path / CONFIG_FILENAME
        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")
        with open(config_path) as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)


def find_workspace() -> Path:
    """Find the workspace root by looking for oolab.yaml in current or parent dirs."""
    current = Path.cwd()
    while current != current.parent:
        if (current / CONFIG_FILENAME).exists():
            return current
        current = current.parent
    raise FileNotFoundError(
        f"No {CONFIG_FILENAME} found. Are you inside an odoo-launchpad workspace?"
    )
