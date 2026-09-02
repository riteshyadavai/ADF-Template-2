"""Load catalogs/catalog.yaml for domains, workflows, and materialize."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field, model_validator

from cli.template_root import template_root


class RecommendedStack(BaseModel):
    gateway: str = "litellm"
    cache: str = "memory"
    vector: str = "memory"


class CatalogEval(BaseModel):
    id: str
    query: str


class CatalogMcpServer(BaseModel):
    id: str
    enabled: bool = False
    transport: str = "streamable_http"
    url: str = ""
    token_env: str | None = None


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
    summary: str = ""
    description: str = ""
    aliases: list[str] = Field(default_factory=list)
    recommended_stack: RecommendedStack = Field(default_factory=RecommendedStack)
    skills: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    evals: list[CatalogEval] = Field(default_factory=list)
    agents: list[CatalogAgent]
    graph: CatalogGraph

    @model_validator(mode="after")
    def agents_present(self) -> CatalogWorkflow:
        if not self.description and self.summary:
            self.description = self.summary
        if not self.agents:
            raise ValueError(f"workflow '{self.id}' needs at least one agent")
        names = [a.name for a in self.agents]
        if len(names) != len(set(names)):
            raise ValueError(f"duplicate agent names in workflow '{self.id}'")
        extra = list(self.tools)
        for agent in self.agents:
            extra.extend(agent.allowed_tools)
        self.tools = list(dict.fromkeys(extra))
        return self


class CatalogDomain(BaseModel):
    id: str
    name: str
    description: str = ""
    aliases: list[str] = Field(default_factory=list)
    mcp_servers: list[CatalogMcpServer] = Field(default_factory=list)
    workflows: list[CatalogWorkflow]

    @model_validator(mode="after")
    def unique_workflows(self) -> CatalogDomain:
        ids = [w.id for w in self.workflows]
        if len(ids) != len(set(ids)):
            raise ValueError(f"duplicate workflow ids in domain '{self.id}'")
        if not ids:
            raise ValueError(f"domain '{self.id}' needs at least one workflow")
        return self


def catalog_path(root: Path | None = None) -> Path:
    return (root or template_root()) / "catalogs" / "catalog.yaml"


def load_raw_catalog(root: Path | None = None) -> dict:
    path = catalog_path(root)
    with path.open(encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    if not isinstance(raw, dict) or "domains" not in raw:
        raise ValueError(f"Invalid catalog: {path}")
    return raw


def load_domains(root: Path | None = None) -> list[CatalogDomain]:
    raw = load_raw_catalog(root)
    domains: list[CatalogDomain] = []
    for domain_id, body in (raw.get("domains") or {}).items():
        wf_map = body.get("workflows") or {}
        workflows = [
            CatalogWorkflow(id=wf_id, **wf_body)
            for wf_id, wf_body in wf_map.items()
        ]
        servers = [
            CatalogMcpServer.model_validate(item)
            for item in (body.get("mcp_servers") or [])
        ]
        domains.append(
            CatalogDomain(
                id=domain_id,
                name=body.get("name", domain_id),
                description=body.get("description", ""),
                aliases=list(body.get("aliases") or []),
                mcp_servers=servers,
                workflows=workflows,
            )
        )
    if not domains:
        raise ValueError(f"No domains in {catalog_path(root)}")
    return domains


def resolve_domain_id(token: str, root: Path | None = None) -> str:
    needle = token.strip().lower()
    for domain in load_domains(root):
        aliases = {domain.id.lower(), *(a.lower() for a in domain.aliases)}
        if needle in aliases:
            return domain.id
    known = ", ".join(d.id for d in load_domains(root))
    raise ValueError(f"Unknown domain '{token}'. Known: {known}")


def resolve_workflow_id(domain_id: str, token: str, root: Path | None = None) -> str:
    domain = get_domain(domain_id, root)
    needle = token.strip().lower()
    for workflow in domain.workflows:
        aliases = {workflow.id.lower(), *(a.lower() for a in workflow.aliases)}
        if needle in aliases:
            return workflow.id
    known = ", ".join(w.id for w in domain.workflows)
    raise ValueError(f"Unknown workflow '{token}' in {domain.id}. Known: {known}")


def get_domain(domain_id: str, root: Path | None = None) -> CatalogDomain:
    resolved = resolve_domain_id(domain_id, root)
    for domain in load_domains(root):
        if domain.id == resolved:
            return domain
    raise ValueError(f"Unknown domain '{domain_id}'")


def get_workflow(domain_id: str, workflow_id: str, root: Path | None = None) -> CatalogWorkflow:
    domain = get_domain(domain_id, root)
    resolved = resolve_workflow_id(domain.id, workflow_id, root)
    for workflow in domain.workflows:
        if workflow.id == resolved:
            return workflow
    raise ValueError(f"Unknown workflow '{workflow_id}' in {domain.id}")


def workflow_snapshot(domain: CatalogDomain, workflow: CatalogWorkflow) -> dict:
    return {
        "summary": workflow.summary,
        "skills": list(workflow.skills),
        "tools": list(workflow.tools),
        "agents": [
            {
                "name": agent.name,
                "description": agent.description,
                "tools": list(agent.allowed_tools),
                "prompt": agent.prompt_stub.strip(),
            }
            for agent in workflow.agents
        ],
        "graph": {
            "entry": workflow.graph.entry,
            "nodes": [node.model_dump() for node in workflow.graph.nodes],
        },
    }


def evals_payload(workflow: CatalogWorkflow) -> list[dict]:
    return [{"id": item.id, "query": item.query} for item in workflow.evals]


def mcp_payload(domain: CatalogDomain) -> dict:
    return {
        "servers": [
            {
                "id": server.id,
                "enabled": server.enabled,
                "transport": server.transport,
                "url": server.url,
                "token_env": server.token_env,
            }
            for server in domain.mcp_servers
        ]
    }


def graph_chain(workflow: CatalogWorkflow) -> str:
    by_id = {n.id: n for n in workflow.graph.nodes}
    parts: list[str] = []
    seen: set[str] = set()
    current = workflow.graph.entry
    while current and current not in seen:
        seen.add(current)
        node = by_id.get(current)
        if node is None:
            break
        label = current
        if node.requires_hitl:
            label = f"{current} (HITL)"
        parts.append(label)
        nxt = node.next
        current = nxt[0] if nxt else ""
    return " → ".join(parts) if parts else workflow.graph.entry


def materialize_workflow(
    dest_root: Path,
    domain_id: str,
    workflow_id: str,
    *,
    mcp_examples: bool,
    catalog_root: Path | None = None,
    workflow: CatalogWorkflow | None = None,
) -> Path:
    domain = get_domain(domain_id, catalog_root)
    plan = workflow or get_workflow(domain.id, workflow_id, catalog_root)
    base = dest_root / "domains" / domain.id / "workflows" / plan.id
    agents_dir = base / "agents"
    prompts_dir = base / "prompts"
    agents_dir.mkdir(parents=True, exist_ok=True)
    prompts_dir.mkdir(parents=True, exist_ok=True)

    graph_payload = {
        "entry": plan.graph.entry,
        "nodes": [
            {
                "id": node.id,
                "agent_name": node.agent_name,
                "requires_hitl": node.requires_hitl,
                "next": node.next,
            }
            for node in plan.graph.nodes
        ],
    }
    (base / "graph.yaml").write_text(
        yaml.safe_dump(graph_payload, sort_keys=False),
        encoding="utf-8",
    )

    for agent in plan.agents:
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
