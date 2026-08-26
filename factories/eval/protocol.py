"""Eval client protocol."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class EvalCase:
    input: str
    actual_output: str
    expected_output: str | None = None
    retrieval_context: list[str] = field(default_factory=list)
    metrics: list[str] = field(default_factory=lambda: ["answer_relevancy"])


@dataclass
class MetricScore:
    name: str
    score: float
    passed: bool
    reason: str = ""


class EvalClient(ABC):
    @property
    @abstractmethod
    def backend(self) -> str: ...

    @abstractmethod
    async def evaluate_case(self, case: EvalCase) -> list[MetricScore]: ...
