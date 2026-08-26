"""Content guardrail factory."""

from __future__ import annotations

from config.settings import Settings, get_settings
from factories.guardrails.bedrock.client import BedrockContentGuardrail
from factories.guardrails.passthrough.client import PassthroughGuardrail
from factories.guardrails.protocol import ContentGuardrail


def make_content_guardrail(settings: Settings | None = None) -> ContentGuardrail:
    settings = settings or get_settings()
    backend = settings.security.content_guardrail_backend
    if not settings.security.enable_guardrails or backend == "passthrough":
        return PassthroughGuardrail()
    if backend == "bedrock":
        if not settings.bedrock.guardrail_id:
            return PassthroughGuardrail()
        return BedrockContentGuardrail(
            region=settings.bedrock.region,
            guardrail_id=settings.bedrock.guardrail_id,
            guardrail_version=settings.bedrock.guardrail_version,
        )
    raise ValueError(f"Unsupported content guardrail backend: {backend}")
