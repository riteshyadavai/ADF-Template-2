"""LLM gateway protocol implemented by factory backends."""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field


class LLMMessage(BaseModel):
    role: str
    content: str


class LLMRequest(BaseModel):
    messages: list[LLMMessage]
    model: str | None = None
    temperature: float = 0.7
    max_tokens: int | None = None
    tenant_id: str = "default"
    run_id: str | None = None
    bypass_cache: bool = False


class LLMResponse(BaseModel):
    content: str
    model: str
    token_usage: dict[str, int] = Field(default_factory=dict)
    cost_usd: float = 0.0
    raw_metadata: dict[str, str] = Field(default_factory=dict)


class LLMGateway(ABC):
    """Complete LLM calls and report spend. Implemented by factories."""

    @abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse: ...

    @abstractmethod
    def get_spend(self, tenant_id: str) -> dict[str, float]: ...
