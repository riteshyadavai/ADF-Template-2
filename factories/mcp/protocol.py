"""MCP toolset protocol."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class MCPBundle:
    stdio: Any | None = None
    http: Any | None = None
