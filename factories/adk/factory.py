"""Google ADK factory."""

from __future__ import annotations

from typing import TYPE_CHECKING

from config.settings import Settings, get_settings
from factories.adk.memory.client import InMemoryADKRunner
from factories.adk.protocol import ADKRunner

if TYPE_CHECKING:
    from google.adk.agents.base_agent import BaseAgent


def make_adk_runner(
    agent: BaseAgent,
    settings: Settings | None = None,
) -> ADKRunner | None:
    """Build an in-memory ADK runner for the given root agent."""
    settings = settings or get_settings()
    if not settings.adk.enabled:
        return None

    from google.adk.runners import InMemoryRunner

    runner = InMemoryRunner(agent=agent, app_name=settings.adk.app_name)
    return InMemoryADKRunner(runner, app_name=settings.adk.app_name)


def make_default_llm_agent(settings: Settings | None = None) -> BaseAgent:
    """Create a minimal ``LlmAgent`` from settings — useful for smoke tests."""
    settings = settings or get_settings()
    from google.adk.agents import LlmAgent

    return LlmAgent(
        name=settings.adk.agent_name,
        model=settings.adk.default_model,
        description=settings.adk.description,
        instruction=settings.adk.instruction,
    )
