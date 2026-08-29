"""Load catalogs/factories.yaml for CLI prompts and extras."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from cli.template_root import template_root


class FactoryBackendSpec(BaseModel):
    id: str
    status: str = "implemented"
    extra: str | None = None
    group: str | None = None


class FactoryCapabilitySpec(BaseModel):
    id: str
    prompt: str
    setting: str | None = None
    backends: list[FactoryBackendSpec] = Field(default_factory=list)


class FactoryCatalog(BaseModel):
    capabilities: list[FactoryCapabilitySpec]


def factory_catalog_path(root: Path | None = None) -> Path:
    return (root or template_root()) / "catalogs" / "factories.yaml"


def load_factory_catalog(root: Path | None = None) -> FactoryCatalog:
    path = factory_catalog_path(root)
    with path.open(encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    return FactoryCatalog.model_validate(raw)


def get_capability(capability_id: str, root: Path | None = None) -> FactoryCapabilitySpec:
    catalog = load_factory_catalog(root)
    for cap in catalog.capabilities:
        if cap.id == capability_id:
            return cap
    known = ", ".join(c.id for c in catalog.capabilities)
    raise ValueError(f"Unknown factory capability '{capability_id}'. Known: {known}")


def get_backend(
    capability_id: str,
    backend_id: str,
    root: Path | None = None,
) -> FactoryBackendSpec:
    cap = get_capability(capability_id, root)
    for backend in cap.backends:
        if backend.id == backend_id:
            return backend
    known = ", ".join(b.id for b in cap.backends)
    raise ValueError(f"Unknown backend '{backend_id}' for {capability_id}. Known: {known}")


def labeled_backend_choices(capability_id: str, root: Path | None = None) -> list[str]:
    cap = get_capability(capability_id, root)
    return [f"{b.id} ({b.status})" for b in cap.backends]


def backend_id_from_label(label: str) -> str:
    return label.split(" (", 1)[0]


def assert_backend_allowed(
    capability_id: str,
    backend_id: str,
    *,
    force_planned: bool = False,
    root: Path | None = None,
) -> None:
    backend = get_backend(capability_id, backend_id, root)
    if backend.status == "planned" and not force_planned:
        raise ValueError(
            f"{capability_id} backend '{backend_id}' is planned. "
            "Pick an implemented backend or pass --force-planned."
        )


def extras_for_choices(
    *,
    gateway: str,
    cache: str,
    vector: str,
    parser: str,
    guardrails: str,
    eval_backend: str,
    langfuse: bool,
    logfire: bool,
    root: Path | None = None,
) -> list[str]:
    hints = ["uv sync"]
    extras: set[str] = set()
    groups: set[str] = set()

    def add(capability: str, backend: str) -> None:
        spec = get_backend(capability, backend, root)
        if spec.extra:
            extras.add(spec.extra)
        if spec.group:
            groups.add(spec.group)

    add("gateway", gateway)
    add("cache", cache)
    add("vector", vector)
    add("parser", parser)
    add("guardrails", guardrails)
    add("eval", eval_backend)
    if langfuse:
        add("observability", "langfuse")
    if logfire:
        add("observability", "logfire")

    for extra in sorted(extras):
        hints.append(f"uv sync --extra {extra}")
    for group in sorted(groups):
        hints.append(f"uv sync --group {group}")
    return hints
