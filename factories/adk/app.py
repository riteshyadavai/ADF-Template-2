"""Build a Google ADK App + LlmAgent from settings."""

from __future__ import annotations

from typing import Any

from config.settings import Settings, get_settings
from factories.mcp.factory import make_mcp_bundle


def make_adk_llm_agent(settings: Settings | None = None, tools: list[Any] | None = None):
    settings = settings or get_settings()
    from google.adk.agents import LlmAgent

    kwargs: dict[str, Any] = {
        "name": settings.adk.agent_name,
        "model": settings.adk.default_model,
        "description": settings.adk.description,
        "instruction": settings.adk.instruction,
    }
    if tools:
        kwargs["tools"] = tools
    return LlmAgent(**kwargs)


def make_adk_app(settings: Settings | None = None, tools: list[Any] | None = None):
    settings = settings or get_settings()
    agent = make_adk_llm_agent(settings, tools=tools)
    from google.adk.apps.app import App

    return App(name=settings.adk.app_name, root_agent=agent)


def make_adk_agent_with_mcp(settings: Settings | None = None):
    settings = settings or get_settings()
    bundle = make_mcp_bundle(settings)
    tools = [item for item in (bundle.stdio, bundle.http) if item is not None]
    return make_adk_app(settings, tools=tools or None)
