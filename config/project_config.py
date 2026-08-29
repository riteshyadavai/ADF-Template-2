"""Optional project.yaml written by `66degrees-factory init`."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel

from config.settings import PROJECT_ROOT


class ProjectConfig(BaseModel):
    domain: str | None = None
    workflow: str | None = None
    template_package: str = "66degrees-factory"
    template_version: str | None = None


def project_yaml_path(root: Path | None = None) -> Path:
    return (root or PROJECT_ROOT) / "config" / "project.yaml"


def load_project_config(root: Path | None = None) -> ProjectConfig | None:
    path = project_yaml_path(root)
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    return ProjectConfig.model_validate(raw)


def workflow_dir(root: Path, config: ProjectConfig) -> Path | None:
    if not config.domain or not config.workflow:
        return None
    path = root / "domains" / config.domain / "workflows" / config.workflow
    return path if path.is_dir() else None


def dump_project_config(config: ProjectConfig) -> str:
    payload = {
        "domain": config.domain,
        "workflow": config.workflow,
        "template_package": config.template_package,
        "template_version": config.template_version,
    }
    return yaml.safe_dump(payload, sort_keys=False)
