"""Project and workflow snapshot from config/app.yaml (written by init)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from config.settings import PROJECT_ROOT


class ProjectConfig(BaseModel):
    name: str | None = None
    domain: str | None = None
    workflow: str | None = None
    workflow_name: str | None = None
    plan: str | None = None
    aliases: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    template_package: str = "66degrees-factory"
    template_version: str | None = None


class WorkflowEval(BaseModel):
    id: str
    query: str


class WorkflowProfile(BaseModel):
    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    agents: list[dict[str, Any]] = Field(default_factory=list)
    graph: dict[str, Any] = Field(default_factory=dict)


def app_yaml_path(root: Path | None = None) -> Path:
    return (root or PROJECT_ROOT) / "config" / "app.yaml"


def _raw_app_yaml(root: Path | None = None) -> dict[str, Any] | None:
    path = app_yaml_path(root)
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    return raw if isinstance(raw, dict) else None


def load_project_config(root: Path | None = None) -> ProjectConfig | None:
    raw = _raw_app_yaml(root)
    if raw is None:
        return None
    project = raw.get("project") or {}
    template = raw.get("template") or {}
    if not project.get("domain") and not project.get("workflow"):
        return None
    return ProjectConfig(
        name=project.get("name"),
        domain=project.get("domain"),
        workflow=project.get("workflow"),
        workflow_name=project.get("workflow_name"),
        plan=project.get("plan"),
        aliases=list(project.get("aliases") or []),
        skills=list(project.get("skills") or []),
        template_package=template.get("package") or "66degrees-factory",
        template_version=template.get("version"),
    )


def load_workflow_profile(root: Path | None = None) -> WorkflowProfile | None:
    raw = _raw_app_yaml(root)
    if raw is None:
        return None
    body = raw.get("workflow")
    if not isinstance(body, dict):
        return None
    return WorkflowProfile.model_validate(body)


def load_workflow_evals(root: Path | None = None) -> list[WorkflowEval]:
    raw = _raw_app_yaml(root)
    if raw is None:
        return []
    items = raw.get("evals") or []
    return [WorkflowEval.model_validate(item) for item in items if isinstance(item, dict)]


def load_mcp_servers(root: Path | None = None) -> list[dict[str, Any]]:
    raw = _raw_app_yaml(root)
    if raw is None:
        return []
    mcp = raw.get("mcp") or {}
    servers = mcp.get("servers") or []
    return [item for item in servers if isinstance(item, dict)]


def workflow_dir(root: Path, config: ProjectConfig) -> Path | None:
    if not config.domain or not config.workflow:
        return None
    path = root / "domains" / config.domain / "workflows" / config.workflow
    return path if path.is_dir() else None
