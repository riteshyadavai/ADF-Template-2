"""MCP client factories — stdio and HTTP transports."""

from __future__ import annotations

import os
from collections.abc import Callable

from google.adk.tools.mcp_tool.mcp_session_manager import (
    StdioConnectionParams,
    StreamableHTTPConnectionParams,
)
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from mcp import StdioServerParameters

HeaderProvider = Callable[..., dict[str, str]]


def stdio_toolset(
    command: str,
    args: list[str],
    tool_filter: list[str] | None = None,
    timeout: float = 120.0,
) -> McpToolset:
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=command,
                args=args,
                env=os.environ.copy(),
            ),
            timeout=timeout,
        ),
        tool_filter=tool_filter,
    )


def http_toolset(
    url: str,
    bearer_token: str | None = None,
    tool_filter: list[str] | None = None,
) -> McpToolset:
    headers = {"Authorization": f"Bearer {bearer_token}"} if bearer_token else None
    return McpToolset(
        connection_params=StreamableHTTPConnectionParams(url=url, headers=headers),
        tool_filter=tool_filter,
    )
