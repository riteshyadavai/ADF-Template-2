"""MCP factory wrapping stdio/HTTP connection helpers."""

from __future__ import annotations

import os
import re
from pathlib import Path

import yaml

from config.project_config import load_mcp_servers
from config.settings import PROJECT_ROOT, Settings, get_settings
from factories.mcp.client.connections import http_toolset, stdio_toolset
from factories.mcp.protocol import MCPBundle

_ENV_PLACEHOLDER = re.compile(r"\$\{([A-Z0-9_]+)\}")


def expand_env_placeholders(value: str) -> str:
    def replace(match: re.Match[str]) -> str:
        return os.environ.get(match.group(1), "")

    return _ENV_PLACEHOLDER.sub(replace, value)


def make_mcp_bundle(
    settings: Settings | None = None,
    config_path: Path | None = None,
) -> MCPBundle:
    _ = settings or get_settings()
    servers = load_mcp_servers()
    if servers:
        http = None
        for server in servers:
            if not server.get("enabled"):
                continue
            url = expand_env_placeholders(str(server.get("url") or ""))
            if not url:
                continue
            token_env = server.get("token_env")
            token = os.environ.get(str(token_env)) if token_env else None
            http = http_toolset(url, token or None)
            break
        return MCPBundle(http=http)

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
