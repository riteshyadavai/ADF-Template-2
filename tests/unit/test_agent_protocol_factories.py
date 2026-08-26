"""Tests for A2A and Google ADK factories."""

from __future__ import annotations

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue_v2 import EventQueue

from config.settings import Settings
from factories.a2a.factory import make_a2a_client_config, make_a2a_server
from factories.a2a.server import build_agent_card
from factories.adk.factory import make_adk_runner, make_default_llm_agent
from factories.adk.memory.client import InMemoryADKRunner


class _NoOpExecutor(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        return None

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        return None


def test_a2a_server_is_disabled_by_default():
    assert make_a2a_server(_NoOpExecutor(), Settings()) is None


def test_a2a_server_builds_routes_when_enabled():
    settings = Settings(a2a={"enabled": True, "public_base_url": "http://127.0.0.1:8000"})
    bundle = make_a2a_server(_NoOpExecutor(), settings)
    assert bundle is not None
    assert bundle.agent_card.name == settings.a2a.agent_name
    assert len(bundle.routes) >= 3


def test_a2a_agent_card_uses_jsonrpc_interface():
    settings = Settings(a2a={"enabled": True})
    card = build_agent_card(settings, public_base_url="http://example.test")
    assert card.supported_interfaces[0].url.startswith("http://example.test/a2a/jsonrpc")


def test_a2a_client_config_uses_timeout():
    settings = Settings(a2a={"client_timeout_seconds": 42.0})
    config = make_a2a_client_config(settings)
    assert config.httpx_client is not None
    assert config.httpx_client.timeout.as_dict()["connect"] == 42.0


def test_adk_runner_wraps_in_memory_runner():
    settings = Settings(adk={"enabled": True, "app_name": "test-app"})
    agent = make_default_llm_agent(settings)
    runner = make_adk_runner(agent, settings)
    assert isinstance(runner, InMemoryADKRunner)
    assert runner.app_name == "test-app"
