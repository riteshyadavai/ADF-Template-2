"""Project block from config/app.yaml (written by init)."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel

from config.settings import PROJECT_ROOT


class ProjectConfig(BaseModel):
    domain: str | None = None
    workflow: str | None = None
    plan: str | None = None
    template_package: str = "66degrees-factory"
    template_version: str | None = None


def app_yaml_path(root: Path | None = None) -> Path:
    return (root or PROJECT_ROOT) / "config" / "app.yaml"


def load_project_config(root: Path | None = None) -> ProjectConfig | None:
    path = app_yaml_path(root)
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    if not isinstance(raw, dict):
        return None
    project = raw.get("project") or {}
    template = raw.get("template") or {}
    if not project.get("domain") and not project.get("workflow"):
        return None
    return ProjectConfig(
        domain=project.get("domain"),
        workflow=project.get("workflow"),
        plan=project.get("plan"),
        template_package=template.get("package") or "66degrees-factory",
        template_version=template.get("version"),
    )


def workflow_dir(root: Path, config: ProjectConfig) -> Path | None:
    if not config.domain or not config.workflow:
        return None
    path = root / "domains" / config.domain / "workflows" / config.workflow
    return path if path.is_dir() else None
