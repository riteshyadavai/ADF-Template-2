"""Redis cache — Upstash/local compatible."""

from __future__ import annotations

import json
from typing import Any

from factories.cache.protocol import CacheProvider


class RedisCacheProvider(CacheProvider):
    def __init__(self, url: str) -> None:
        if not url:
            raise ValueError("CACHE_REDIS_URL is required when CACHE_BACKEND=redis")
        import redis.asyncio as redis

        self._client = redis.from_url(url, decode_responses=True)

    async def aclose(self) -> None:
        close = getattr(self._client, "aclose", None)
        if close is not None:
            await close()
            return
        await self._client.close()

    async def get(self, key: str) -> Any | None:
        raw = await self._client.get(key)
        return json.loads(raw) if raw else None

    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        payload = json.dumps(value)
        if ttl_seconds:
            await self._client.setex(key, ttl_seconds, payload)
        else:
            await self._client.set(key, payload)

    async def delete(self, key: str) -> None:
        await self._client.delete(key)

    async def invalidate(self, prefix: str) -> int:
        keys = [k async for k in self._client.scan_iter(f"{prefix}*")]
        if keys:
            await self._client.delete(*keys)
        return len(keys)
