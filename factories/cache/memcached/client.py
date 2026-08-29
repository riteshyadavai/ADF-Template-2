"""Memcached CacheProvider via pymemcache."""

from __future__ import annotations

import asyncio
import json
from typing import Any
from urllib.parse import urlparse

from factories.cache.protocol import CacheProvider


def _host_port(url: str) -> tuple[str, int]:
    parsed = urlparse(url if "://" in url else f"memcached://{url}")
    host = parsed.hostname or "localhost"
    port = parsed.port or 11211
    return host, port


class MemcachedCacheProvider(CacheProvider):
    def __init__(self, url: str) -> None:
        try:
            from pymemcache.client.base import Client
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Memcached requires: uv sync --extra cache-memcached"
            ) from exc
        self.url = url
        host, port = _host_port(url)
        self._client = Client((host, port))

    async def get(self, key: str) -> Any | None:
        raw = await asyncio.to_thread(self._client.get, key)
        if raw is None:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode()
        return json.loads(raw)

    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        payload = json.dumps(value)
        expire = int(ttl_seconds or 0)
        await asyncio.to_thread(self._client.set, key, payload, expire)

    async def delete(self, key: str) -> None:
        await asyncio.to_thread(self._client.delete, key)

    async def invalidate(self, prefix: str) -> int:
        return 0
