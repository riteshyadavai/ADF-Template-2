"""Unified run record schema — ties trace → plan → agents → tools → output → eval."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class RunStepType(StrEnum):
    PLAN = "plan"
    ORCHESTRATOR = "orchestrator"
    SUB_AGENT = "sub_agent"
    TOOL = "tool"
    MCP = "mcp"
    LLM = "llm"
    HITL = "hitl"
    GUARDRAIL = "guardrail"
    OUTPUT = "output"
    EVAL = "eval"


class RunStep(BaseModel):
    step_id: UUID = Field(default_factory=uuid4)
    step_type: RunStepType
    name: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: datetime | None = None
    latency_ms: float | None = None
    input_summary: str | None = None
    output_summary: str | None = None
    token_usage: dict[str, int] = Field(default_factory=dict)
    cost_usd: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    parent_step_id: UUID | None = None


class RunRecord(BaseModel):
    """First-class planning/execution trace emitted to observability."""

    run_id: UUID = Field(default_factory=uuid4)
    correlation_id: str
    trace_id: str
    tenant_id: str = "default"
    session_id: str | None = None
    git_sha: str = "unknown"
    prompt_version: str = "latest"
    model_version: str | None = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: datetime | None = None
    status: str = "running"
    user_query: str | None = None
    final_output: str | None = None
    eval_score: float | None = None
    total_cost_usd: float = 0.0
    total_tokens: int = 0
    steps: list[RunStep] = Field(default_factory=list)

    def add_step(self, step: RunStep) -> RunStep:
        self.steps.append(step)
        if step.cost_usd:
            self.total_cost_usd += step.cost_usd
        if step.token_usage:
            self.total_tokens += step.token_usage.get("total", 0)
        return step

    def complete(self, output: str, eval_score: float | None = None) -> None:
        self.final_output = output
        self.eval_score = eval_score
        self.status = "completed"
        self.ended_at = datetime.utcnow()

    def fail(self, reason: str) -> None:
        self.status = "failed"
        self.final_output = reason
        self.ended_at = datetime.utcnow()
