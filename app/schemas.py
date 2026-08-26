"""HTTP DTOs for platform routes."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class RunAgentRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=32000)
    session_id: str | None = None
    bypass_cache: bool = False
    metadata: dict = Field(default_factory=dict)


class RunAgentResponse(BaseModel):
    run_id: UUID
    output: str
    session_id: str
    cost_usd: float | None = None
    token_usage: dict[str, int] = Field(default_factory=dict)


class ResumeRequest(BaseModel):
    approval: str = Field(..., min_length=1)


class CostReportResponse(BaseModel):
    tenant_id: str
    daily_spend_usd: float
    monthly_spend_usd: float
