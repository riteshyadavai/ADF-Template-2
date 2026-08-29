"""Google ADK factory."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from config.settings import Settings, get_settings
from factories.adk.app import make_adk_app, make_adk_llm_agent
from factories.adk.memory.client import InMemoryADKRunner
from factories.adk.protocol import ADKRunner

if TYPE_CHECKING:
    from google.adk.agents.base_agent import BaseAgent


def make_adk_runner(
    agent: BaseAgent | None = None,
    settings: Settings | None = None,
    *,
    app: Any | None = None,
) -> ADKRunner | None:
    settings = settings or get_settings()
    if not settings.adk.enabled:
        return None

    from google.adk.runners import InMemoryRunner

    if app is not None:
        runner = InMemoryRunner(app=app, app_name=settings.adk.app_name)
    elif agent is not None:
        runner = InMemoryRunner(agent=agent, app_name=settings.adk.app_name)
    else:
        runner = InMemoryRunner(app=make_adk_app(settings), app_name=settings.adk.app_name)
    return InMemoryADKRunner(runner, app_name=settings.adk.app_name)


def make_default_llm_agent(settings: Settings | None = None) -> BaseAgent:
    return make_adk_llm_agent(settings)
