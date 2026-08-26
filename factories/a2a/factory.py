"""A2A factory entry points."""

from __future__ import annotations

import httpx
from a2a.client import ClientConfig
from a2a.server.agent_execution import AgentExecutor

from config.settings import Settings, get_settings
from factories.a2a.client import A2AClient, connect_a2a_client
from factories.a2a.protocol import A2AServerBundle
from factories.a2a.server import build_a2a_server


def make_a2a_client_config(settings: Settings | None = None) -> ClientConfig:
    settings = settings or get_settings()
    return ClientConfig(
        streaming=settings.a2a.streaming,
        httpx_client=httpx.AsyncClient(timeout=settings.a2a.client_timeout_seconds),
    )


async def make_a2a_client(
    agent_url: str,
    settings: Settings | None = None,
) -> A2AClient | None:
    """Connect to a remote A2A agent when the integration is enabled."""
    settings = settings or get_settings()
    if not settings.a2a.enabled:
        return None
    return await connect_a2a_client(
        agent_url,
        client_config=make_a2a_client_config(settings),
    )


def make_a2a_server(
    executor: AgentExecutor,
    settings: Settings | None = None,
    *,
    public_base_url: str | None = None,
) -> A2AServerBundle | None:
    """Build A2A server routes for a project-provided ``AgentExecutor``."""
    settings = settings or get_settings()
    if not settings.a2a.enabled:
        return None
    base_url = public_base_url or settings.a2a.public_base_url
    return build_a2a_server(executor, settings, public_base_url=base_url)
