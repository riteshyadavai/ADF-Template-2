"""Wires agents + factories for a running process."""

from __future__ import annotations

from functools import lru_cache

from agents.base_agent import Orchestrator
from agents.mcp.registry import MCPRegistry
from agents.prompts.registry import PromptRegistry
from agents.registry import AgentRegistry
from config.settings import Settings, get_settings
from factories.eval.protocol import EvalClient
from factories.registry import FactoryRegistry, get_factory_registry
from shared.middleware import IdempotencyStore


class Platform:
    """Running instance of the template: registries + orchestrator + backends."""

    def __init__(
        self,
        settings: Settings | None = None,
        factories: FactoryRegistry | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.factories = factories or FactoryRegistry(self.settings)
        self.mcp = MCPRegistry()
        self.agents = AgentRegistry(mcp_registry=self.mcp)
        self.prompts = PromptRegistry()
        self.idempotency = IdempotencyStore()
        self.orchestrator = Orchestrator(
            gateway=self.factories.ai_gateway(),
            agent_registry=self.agents,
            prompt_registry=self.prompts,
        )

    def evaluation(self) -> EvalClient:
        return self.factories.eval()


@lru_cache
def get_platform() -> Platform:
    return Platform(factories=get_factory_registry())
