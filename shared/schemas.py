"""Platform request/response schemas (not HTTP DTOs)."""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TrustBoundary(StrEnum):
    TRUSTED = "trusted"
    UNTRUSTED = "untrusted"
    MCP_TOOL = "mcp_tool"
    USER_INPUT = "user_input"
    EXTERNAL_DOC = "external_doc"


class ContextChunk(BaseModel):
    content: str
    trust: TrustBoundary = TrustBoundary.TRUSTED
    source: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentRequest(BaseModel):
    query: str
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str = "anonymous"
    tenant_id: str = "default"
    idempotency_key: str | None = None
    bypass_cache: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    run_id: UUID
    output: str
    session_id: str
    model: str | None = None
    token_usage: dict[str, int] = Field(default_factory=dict)
    cost_usd: float | None = None
    latency_ms: float | None = None
    eval_score: float | None = None


class HealthStatus(BaseModel):
    status: str
    version: str
    environment: str
    checks: dict[str, str] = Field(default_factory=dict)


class IdempotencyRecord(BaseModel):
    key: str
    status: str
    response: dict[str, Any] | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
