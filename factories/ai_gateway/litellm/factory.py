"""AI Gateway factory — LiteLLM (default) or Bedrock."""

from __future__ import annotations

from config.settings import Settings
from factories.ai_gateway.litellm.ai_gateway import AIGateway
from factories.ai_gateway.litellm.budget import BudgetTracker
from factories.ai_gateway.protocol import LLMGateway


def make_ai_gateway(settings: Settings) -> LLMGateway:
    provider = settings.gateway.provider
    if provider == "litellm":
        budget = BudgetTracker(
            daily_limit_usd=settings.gateway.daily_budget_usd,
            monthly_limit_usd=settings.gateway.monthly_budget_usd,
            downgrade_model=settings.gateway.budget_downgrade_model,
        )
        return AIGateway(budget=budget)
    if provider == "bedrock":
        # Bedrock uses same gateway with model prefix routing via LiteLLM
        return AIGateway()
    return AIGateway()
