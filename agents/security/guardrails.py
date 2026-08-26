"""Backward-compatible aliases for execution policy types."""

from agents.security.execution_policies import (
    BlockedToolComboPolicy,
    ExecutionPolicy,
    ExecutionPolicyContext,
    ExecutionPolicyEngine,
    SpendLimitPolicy,
)

GuardrailContext = ExecutionPolicyContext
GuardrailPolicy = ExecutionPolicy
GuardrailEngine = ExecutionPolicyEngine

__all__ = [
    "BlockedToolComboPolicy",
    "ExecutionPolicy",
    "ExecutionPolicyContext",
    "ExecutionPolicyEngine",
    "GuardrailContext",
    "GuardrailEngine",
    "GuardrailPolicy",
    "SpendLimitPolicy",
]
