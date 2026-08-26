"""A2A HTTP server wiring."""

from __future__ import annotations

from a2a.server.agent_execution import AgentExecutor
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    create_agent_card_routes,
    create_jsonrpc_routes,
    create_rest_routes,
)
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill

from config.settings import Settings
from factories.a2a.protocol import A2AServerBundle


def build_agent_card(settings: Settings, *, public_base_url: str) -> AgentCard:
    """Build an A2A v1.0 agent card from settings."""
    jsonrpc_url = public_base_url.rstrip("/") + settings.a2a.jsonrpc_path
    if not jsonrpc_url.endswith("/"):
        jsonrpc_url += "/"

    skill = AgentSkill(
        id=settings.a2a.default_skill_id,
        name=settings.a2a.default_skill_name,
        description=settings.a2a.default_skill_description,
    )
    return AgentCard(
        name=settings.a2a.agent_name,
        description=settings.a2a.agent_description,
        version=settings.a2a.agent_version,
        default_input_modes=list(settings.a2a.default_input_modes),
        default_output_modes=list(settings.a2a.default_output_modes),
        capabilities=AgentCapabilities(
            streaming=settings.a2a.streaming,
            extended_agent_card=settings.a2a.extended_agent_card,
        ),
        skills=[skill],
        supported_interfaces=[
            AgentInterface(protocol_binding="JSONRPC", url=jsonrpc_url),
        ],
    )


def build_a2a_server(
    executor: AgentExecutor,
    settings: Settings,
    *,
    public_base_url: str,
) -> A2AServerBundle:
    """Compose request handler and Starlette routes for an A2A agent."""
    agent_card = build_agent_card(settings, public_base_url=public_base_url)
    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
        agent_card=agent_card,
    )
    routes = [
        *create_agent_card_routes(agent_card),
        *create_jsonrpc_routes(request_handler, rpc_url=settings.a2a.jsonrpc_path),
        *create_rest_routes(request_handler, path_prefix=settings.a2a.rest_path),
    ]
    return A2AServerBundle(
        agent_card=agent_card,
        request_handler=request_handler,
        routes=routes,
    )
