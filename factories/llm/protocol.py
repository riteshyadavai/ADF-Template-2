"""LLM client protocol — swappable OpenAI/Bedrock/LiteLLM providers."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LLMClientProtocol(Protocol):
    async def complete(
        self, messages: list[dict[str, str]], *, model: str = ""
    ) -> dict[str, Any]: ...

    def complete_stream(
        self, messages: list[dict[str, str]], *, model: str = ""
    ) -> AsyncIterator[str]: ...

    async def health_check(self) -> dict[str, Any]: ...
