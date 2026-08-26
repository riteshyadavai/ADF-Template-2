"""Centralized AI Gateway — LiteLLM with routing, fallback, cost tracking, redaction."""

from __future__ import annotations

from litellm import acompletion
from tenacity import retry, stop_after_attempt, wait_exponential

from agents.security.redaction import redact_text
from config.settings import get_settings
from factories.ai_gateway.litellm.budget import BudgetTracker
from factories.ai_gateway.protocol import LLMGateway, LLMRequest, LLMResponse
from factories.observability.langfuse.factory import make_langfuse_tracer
from shared.logger import get_logger
from shared.metrics import LLM_COST, LLM_REQUESTS

log = get_logger(__name__)


class AIGateway(LLMGateway):
    """LiteLLM implementation of the platform LLM gateway."""

    def __init__(self, budget: BudgetTracker | None = None) -> None:
        settings = get_settings()
        self._settings = settings
        self._budget = budget or BudgetTracker(
            daily_limit_usd=settings.gateway.daily_budget_usd,
            monthly_limit_usd=settings.gateway.monthly_budget_usd,
            downgrade_model=settings.gateway.budget_downgrade_model,
        )
        self._tracer = make_langfuse_tracer()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def complete(self, request: LLMRequest) -> LLMResponse:
        tenant_id = request.tenant_id
        model = request.model or self._settings.gateway.default_model

        downgrade = self._budget.check_budget(tenant_id)
        if downgrade:
            log.warning("budget_downgrade", tenant_id=tenant_id, model=downgrade)
            model = downgrade

        messages = [{"role": m.role, "content": m.content} for m in request.messages]

        try:
            response = await acompletion(
                model=model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                fallbacks=self._settings.gateway.fallback_models or None,
            )
            LLM_REQUESTS.labels(model=model, status="success").inc()

            content = response.choices[0].message.content or ""
            usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            }
            cost = getattr(response, "_hidden_params", {}).get("response_cost", 0.0) or 0.0

            self._budget.record_spend(tenant_id, cost)
            LLM_COST.labels(tenant_id=tenant_id, model=model).inc(cost)

            if self._settings.gateway.redact_pii:
                content = redact_text(content)

            self._tracer.trace_generation(
                run_id=request.run_id or "unknown",
                model=model,
                prompt=str(messages),
                completion=content,
                token_usage=usage,
                cost_usd=cost,
            )

            return LLMResponse(
                content=content,
                model=model,
                token_usage=usage,
                cost_usd=cost,
                raw_metadata={"provider": self._settings.gateway.provider},
            )
        except Exception as exc:
            LLM_REQUESTS.labels(model=model, status="error").inc()
            log.error("llm_request_failed", model=model, error=str(exc))
            raise

    def get_spend(self, tenant_id: str) -> dict[str, float]:
        return self._budget.current_spend(tenant_id)
