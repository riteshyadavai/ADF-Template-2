"""Load and validate domain/workflow catalogs."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field, model_validator

from cli.template_root import template_root


class CatalogAgent(BaseModel):
    name: str
    description: str
    allowed_tools: list[str] = Field(default_factory=list)
    prompt_stub: str
    inputs: list[str] = Field(default_factory=lambda: ["query", "session_id"])
    outputs: list[str] = Field(default_factory=lambda: ["summary"])
    version: str = "1.0.0"
    prompt_version: str = "1.0.0"


class CatalogGraphNode(BaseModel):
    id: str
    agent_name: str | None = None
    requires_hitl: bool = False
    next: list[str] = Field(default_factory=list)


class CatalogGraph(BaseModel):
    entry: str
    nodes: list[CatalogGraphNode]

    @model_validator(mode="after")
    def entry_exists(self) -> CatalogGraph:
        ids = {n.id for n in self.nodes}
        if self.entry not in ids:
            raise ValueError(f"graph.entry '{self.entry}' is not in nodes")
        return self


class CatalogWorkflow(BaseModel):
    id: str
    name: str
    description: str
    agents: list[CatalogAgent]
    graph: CatalogGraph

    @model_validator(mode="after")
    def agents_present(self) -> CatalogWorkflow:
        if not self.agents:
            raise ValueError(f"workflow '{self.id}' needs at least one agent")
        names = [a.name for a in self.agents]
        if len(names) != len(set(names)):
            raise ValueError(f"duplicate agent names in workflow '{self.id}'")
        return self


class CatalogDomain(BaseModel):
    id: str
    name: str
    description: str = ""
    workflows: list[CatalogWorkflow]

    @model_validator(mode="after")
    def unique_workflows(self) -> CatalogDomain:
        ids = [w.id for w in self.workflows]
        if len(ids) != len(set(ids)):
            raise ValueError(f"duplicate workflow ids in domain '{self.id}'")
        if not ids:
            raise ValueError(f"domain '{self.id}' needs at least one workflow")
        return self


def catalogs_dir(root: Path | None = None) -> Path:
    return (root or template_root()) / "catalogs" / "domains"


def load_domains(root: Path | None = None) -> list[CatalogDomain]:
    directory = catalogs_dir(root)
    if not directory.is_dir():
        raise FileNotFoundError(f"Catalog directory missing: {directory}")
    domains: list[CatalogDomain] = []
    for path in sorted(directory.glob("*.yaml")):
        with path.open(encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}
        domains.append(CatalogDomain.model_validate(raw))
    if not domains:
        raise ValueError(f"No domain catalogs in {directory}")
    return domains


def get_domain(domain_id: str, root: Path | None = None) -> CatalogDomain:
    for domain in load_domains(root):
        if domain.id == domain_id:
            return domain
    known = ", ".join(d.id for d in load_domains(root))
    raise ValueError(f"Unknown domain '{domain_id}'. Known: {known}")


def get_workflow(domain_id: str, workflow_id: str, root: Path | None = None) -> CatalogWorkflow:
    domain = get_domain(domain_id, root)
    for workflow in domain.workflows:
        if workflow.id == workflow_id:
            return workflow
    known = ", ".join(w.id for w in domain.workflows)
    raise ValueError(f"Unknown workflow '{workflow_id}' in {domain_id}. Known: {known}")


def materialize_workflow(
    dest_root: Path,
    domain_id: str,
    workflow_id: str,
    *,
    mcp_examples: bool,
    catalog_root: Path | None = None,
) -> Path:
    workflow = get_workflow(domain_id, workflow_id, catalog_root)
    base = dest_root / "domains" / domain_id / "workflows" / workflow_id
    agents_dir = base / "agents"
    prompts_dir = base / "prompts"
    agents_dir.mkdir(parents=True, exist_ok=True)
    prompts_dir.mkdir(parents=True, exist_ok=True)

    graph_payload = {
        "entry": workflow.graph.entry,
        "nodes": [
            {
                "id": node.id,
                "agent_name": node.agent_name,
                "requires_hitl": node.requires_hitl,
                "next": node.next,
            }
            for node in workflow.graph.nodes
        ],
    }
    (base / "graph.yaml").write_text(
        yaml.safe_dump(graph_payload, sort_keys=False),
        encoding="utf-8",
    )

    for agent in workflow.agents:
        manifest = {
            "name": agent.name,
            "version": agent.version,
            "description": agent.description,
            "inputs": agent.inputs,
            "outputs": agent.outputs,
            "side_effects": [],
            "allowed_tools": agent.allowed_tools,
            "cost_ceiling_usd": 0.5,
            "timeout_seconds": 60,
            "prompt_version": agent.prompt_version,
        }
        (agents_dir / f"{agent.name}.yaml").write_text(
            yaml.safe_dump(manifest, sort_keys=False),
            encoding="utf-8",
        )
        prompt_name = f"{agent.name}_{agent.prompt_version}.md"
        (prompts_dir / prompt_name).write_text(agent.prompt_stub.strip() + "\n", encoding="utf-8")

    if mcp_examples:
        mcp = {
            "stdio": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-everything"]},
            "http": {"url": "http://127.0.0.1:8001/mcp"},
        }
        (base / "mcp.yaml").write_text(yaml.safe_dump(mcp, sort_keys=False), encoding="utf-8")

    return base
