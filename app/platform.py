"""Wires agents + factories for a running process."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from agents.base_agent import Orchestrator, WorkflowGraph
from agents.mcp.registry import MCPRegistry
from agents.prompts.registry import PromptRegistry
from agents.registry import AgentRegistry
from agents.workflow_loader import load_workflow_graph
from config.project_config import load_project_config, workflow_dir
from config.settings import PROJECT_ROOT, Settings, get_settings
from factories.eval.protocol import EvalClient
from factories.registry import FactoryRegistry, get_factory_registry
from shared.middleware import IdempotencyStore


class Platform:
    """Running instance of the template: registries + orchestrator + backends."""

    def __init__(
        self,
        settings: Settings | None = None,
        factories: FactoryRegistry | None = None,
        project_root: Path | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.project_root = project_root or PROJECT_ROOT
        self.factories = factories or FactoryRegistry(self.settings)
        self.mcp = MCPRegistry()
        self.agents = AgentRegistry(mcp_registry=self.mcp)
        extra_prompt_dirs: list[Path] = []
        workflow: WorkflowGraph | None = None

        project = load_project_config(self.project_root)
        wf_path = workflow_dir(self.project_root, project) if project else None
        if wf_path is not None:
            agents_dir = wf_path / "agents"
            if agents_dir.is_dir():
                for manifest in sorted(agents_dir.glob("*.yaml")):
                    self.agents.register_from_manifest(manifest)
            prompts_dir = wf_path / "prompts"
            if prompts_dir.is_dir():
                extra_prompt_dirs.append(prompts_dir)
            graph_file = wf_path / "graph.yaml"
            if graph_file.exists():
                workflow = load_workflow_graph(graph_file)

        self.prompts = PromptRegistry(extra_dirs=extra_prompt_dirs)
        self.idempotency = IdempotencyStore()
        self.orchestrator = Orchestrator(
            gateway=self.factories.ai_gateway(),
            agent_registry=self.agents,
            prompt_registry=self.prompts,
            workflow=workflow,
        )

    def evaluation(self) -> EvalClient:
        return self.factories.eval()


@lru_cache
def get_platform() -> Platform:
    return Platform(factories=get_factory_registry())
