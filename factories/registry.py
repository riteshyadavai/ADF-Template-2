"""Vendor backend composition — not the application runtime.

`app.platform.Platform` owns agent/prompt/MCP registries and the orchestrator.
This registry only constructs swappable backends from settings.
"""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from agents.memory import ColdStateStore, HotStateStore
from config.settings import Settings, get_settings
from factories.a2a.factory import make_a2a_server
from factories.a2a.protocol import A2AServerBundle
from factories.adk.app import make_adk_app
from factories.adk.factory import make_adk_runner
from factories.adk.protocol import ADKRunner
from factories.ai_gateway.litellm.factory import make_ai_gateway
from factories.ai_gateway.protocol import LLMGateway
from factories.cache.factory import make_cache_provider
from factories.cache.protocol import CacheProvider
from factories.database.factory import make_cold_state_store, make_hot_state_store
from factories.embeddings.factory import make_embeddings_client
from factories.embeddings.protocol import EmbeddingsClient
from factories.eval.factory import make_eval_client
from factories.eval.protocol import EvalClient
from factories.guardrails.factory import make_content_guardrail
from factories.guardrails.protocol import ContentGuardrail
from factories.llm.factory import make_llm_client
from factories.llm.protocol import LLMClientProtocol
from factories.mcp.factory import make_mcp_bundle
from factories.mcp.protocol import MCPBundle
from factories.observability.factory import (
    make_langfuse,
    make_llm_tracer,
    make_observability_bundle,
)
from factories.observability.langfuse.client import LangfuseTracer
from factories.observability.protocol import ObservabilityBundle
from factories.parsers.factory import make_document_parser
from factories.parsers.protocol import DocumentParser
from factories.secrets.factory import make_secrets_provider
from factories.secrets.protocol import SecretsProvider
from factories.vectorstore.factory import make_vector_store
from factories.vectorstore.protocol import VectorStore

if TYPE_CHECKING:
    from a2a.server.agent_execution import AgentExecutor
    from google.adk.agents.base_agent import BaseAgent


class FactoryRegistry:
    """Settings → concrete backends."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def ai_gateway(self) -> LLMGateway:
        return make_ai_gateway(self.settings)

    def cache(self) -> CacheProvider:
        return make_cache_provider(self.settings)

    def vector_store(self) -> VectorStore:
        return make_vector_store(self.settings)

    def embeddings(self) -> EmbeddingsClient:
        return make_embeddings_client(self.settings)

    def llm(self) -> LLMClientProtocol:
        return make_llm_client(self.settings)

    def content_guardrail(self) -> ContentGuardrail:
        return make_content_guardrail(self.settings)

    def document_parser(self) -> DocumentParser:
        return make_document_parser(self.settings)

    def eval(self) -> EvalClient:
        return make_eval_client(self.settings)

    def adk_app(self):
        return make_adk_app(self.settings)

    def adk_runner(self, agent: BaseAgent | None = None) -> ADKRunner | None:
        return make_adk_runner(agent, self.settings)

    def mcp(self) -> MCPBundle:
        return make_mcp_bundle(self.settings)

    def secrets(self) -> SecretsProvider:
        return make_secrets_provider(self.settings)

    def a2a_server(
        self,
        executor: AgentExecutor,
        *,
        public_base_url: str | None = None,
    ) -> A2AServerBundle | None:
        return make_a2a_server(
            executor,
            self.settings,
            public_base_url=public_base_url,
        )

    def hot_state(self) -> HotStateStore:
        return make_hot_state_store(self.settings)

    def cold_state(self) -> ColdStateStore:
        return make_cold_state_store(self.settings)

    def observability(self) -> ObservabilityBundle:
        return make_observability_bundle(self.settings)

    def langfuse(self) -> LangfuseTracer:
        return make_langfuse(self.settings)

    def llm_tracer(self) -> LangfuseTracer:
        return make_llm_tracer(self.settings)


@lru_cache
def get_factory_registry() -> FactoryRegistry:
    return FactoryRegistry()
