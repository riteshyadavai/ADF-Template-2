"""OpenAI-compatible LLM client via LiteLLM."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from litellm import acompletion

from config.settings import get_settings
from factories.llm.protocol import LLMClientProtocol


class OpenAILLMClient(LLMClientProtocol):
    async def complete(self, messages: list[dict[str, str]], *, model: str = "") -> dict[str, Any]:
        settings = get_settings()
        response = await acompletion(
            model=model or settings.gateway.default_model,
            messages=messages,
        )
        content = response.choices[0].message.content or ""
        return {
            "content": content,
            "model": model or settings.gateway.default_model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            },
        }

    async def complete_stream(
        self, messages: list[dict[str, str]], *, model: str = ""
    ) -> AsyncIterator[str]:
        settings = get_settings()
        response = await acompletion(
            model=model or settings.gateway.default_model,
            messages=messages,
            stream=True,
        )
        async for chunk in response:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                yield delta

    async def health_check(self) -> dict[str, Any]:
        return {"status": "ok", "provider": "openai/litellm"}
