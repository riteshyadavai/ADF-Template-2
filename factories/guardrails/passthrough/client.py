"""No-op guardrail used when no external provider is configured."""

from __future__ import annotations

from factories.guardrails.protocol import ContentGuardrail, GuardrailResult


class PassthroughGuardrail(ContentGuardrail):
    async def check_input(self, text: str) -> GuardrailResult:
        return GuardrailResult(True, "NONE", "Content guardrails are disabled")

    async def check_output(
        self,
        text: str,
        *,
        source_documents: list[str] | None = None,
        query: str = "",
    ) -> GuardrailResult:
        return GuardrailResult(True, "NONE", "Content guardrails are disabled")
