"""MCP factory wrapping stdio/HTTP connection helpers."""

from __future__ import annotations

from pathlib import Path

import yaml

from config.settings import PROJECT_ROOT, Settings, get_settings
from factories.mcp.client.connections import http_toolset, stdio_toolset
from factories.mcp.protocol import MCPBundle


def make_mcp_bundle(
    settings: Settings | None = None,
    config_path: Path | None = None,
) -> MCPBundle:
    _ = settings or get_settings()
    path = config_path
    if path is None:
        candidates = list((PROJECT_ROOT / "domains").glob("**/mcp.yaml")) if (
            PROJECT_ROOT / "domains"
        ).exists() else []
        path = candidates[0] if candidates else None
    if path is None or not path.exists():
        return MCPBundle()
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    stdio = None
    http = None
    if "stdio" in raw:
        stdio = stdio_toolset(raw["stdio"]["command"], list(raw["stdio"].get("args") or []))
    if "http" in raw:
        http = http_toolset(raw["http"]["url"], raw["http"].get("bearer_token"))
    return MCPBundle(stdio=stdio, http=http)
