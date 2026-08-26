"""Agent capability contract manifest schema."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AgentCapabilityContract(BaseModel):
    """Validated at registration — makes sub-agents swappable."""

    name: str
    version: str  # semver
    description: str
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    side_effects: list[str] = Field(default_factory=list)
    allowed_tools: list[str] = Field(default_factory=list)
    cost_ceiling_usd: float = 1.0
    timeout_seconds: int = 120
    eval_suite: str | None = None
    prompt_version: str = "latest"
