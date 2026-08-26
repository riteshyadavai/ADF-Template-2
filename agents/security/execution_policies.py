"""Pre-execution policy engine (spend limits, blocked tool combos)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from shared.errors import GuardrailViolationError


@dataclass
class ExecutionPolicyContext:
    agent_name: str
    action: str
    tools: list[str]
    estimated_cost_usd: float
    tenant_id: str
    metadata: dict[str, Any]


class ExecutionPolicy(ABC):
    @abstractmethod
    def evaluate(self, ctx: ExecutionPolicyContext) -> None:
        """Raise GuardrailViolationError if policy is violated."""


class SpendLimitPolicy(ExecutionPolicy):
    def __init__(self, max_cost_usd: float) -> None:
        self._max = max_cost_usd

    def evaluate(self, ctx: ExecutionPolicyContext) -> None:
        if ctx.estimated_cost_usd > self._max:
            raise GuardrailViolationError(
                f"Estimated cost ${ctx.estimated_cost_usd:.4f} exceeds limit ${self._max:.4f}"
            )


class BlockedToolComboPolicy(ExecutionPolicy):
    def __init__(self, blocked_combos: list[frozenset[str]]) -> None:
        self._blocked = blocked_combos

    def evaluate(self, ctx: ExecutionPolicyContext) -> None:
        tool_set = frozenset(ctx.tools)
        for combo in self._blocked:
            if combo.issubset(tool_set):
                raise GuardrailViolationError(f"Blocked tool combination: {sorted(combo)}")


class ExecutionPolicyEngine:
    def __init__(self, policies: list[ExecutionPolicy] | None = None) -> None:
        self._policies = policies or []

    def check(self, ctx: ExecutionPolicyContext) -> None:
        for policy in self._policies:
            policy.evaluate(ctx)
