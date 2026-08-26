"""MCP tool registry — allow-lists and result sanitization (platform runtime)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field

from shared.errors import MCPPermissionError
from shared.logger import get_logger
from shared.schemas import ContextChunk, TrustBoundary

log = get_logger(__name__)


class MCPServerConfig(BaseModel):
    name: str
    transport: str  # stdio | http
    command: str | None = None
    args: list[str] = Field(default_factory=list)
    url: str | None = None
    allowed_agents: list[str] = Field(default_factory=lambda: ["*"])
    tools: list[str] = Field(default_factory=list)


@dataclass
class MCPRegistry:
    """Enforces least-privilege tool allow-lists per agent."""

    servers: dict[str, MCPServerConfig] = field(default_factory=dict)
    _agent_allow_lists: dict[str, set[str]] = field(default_factory=dict)

    def register_server(self, config: MCPServerConfig) -> None:
        self.servers[config.name] = config

    def grant_tools(self, agent_name: str, tools: list[str]) -> None:
        self._agent_allow_lists[agent_name] = set(tools)

    def authorize(self, agent_name: str, tool_name: str) -> None:
        allowed = self._agent_allow_lists.get(agent_name)
        if allowed is None:
            raise MCPPermissionError(f"No tool allow-list configured for agent '{agent_name}'")
        if tool_name not in allowed:
            raise MCPPermissionError(
                f"Agent '{agent_name}' is not permitted to use tool '{tool_name}'"
            )

    def sanitize_tool_result(self, result: Any, source: str) -> ContextChunk:
        if isinstance(result, dict):
            content = str(result)
        elif isinstance(result, str):
            content = result
        else:
            content = str(result)

        content = content.replace("Ignore previous instructions", "[FILTERED]")
        return ContextChunk(
            content=content,
            trust=TrustBoundary.MCP_TOOL,
            source=source,
            metadata={"sanitized": True},
        )

    def list_tools_for_agent(self, agent_name: str) -> list[str]:
        allowed = self._agent_allow_lists.get(agent_name, set())
        return sorted(allowed)
