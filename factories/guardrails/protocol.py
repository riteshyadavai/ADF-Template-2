"""Content guardrail interfaces shared by provider implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class GuardrailResult:
    allowed: bool
    action: str
    reason: str
    outputs: list[str] = field(default_factory=list)


class ContentGuardrail(ABC):
    @abstractmethod
    async def check_input(self, text: str) -> GuardrailResult: ...

    @abstractmethod
    async def check_output(
        self,
        text: str,
        *,
        source_documents: list[str] | None = None,
        query: str = "",
    ) -> GuardrailResult: ...
