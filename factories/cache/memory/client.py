"""In-memory cache implementation."""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from factories.cache.protocol import CacheProvider


def content_addressed_key(
    *,
    namespace: str,
    prompt: str,
    model: str,
    params: dict[str, Any],
    tool_inputs: dict[str, Any] | None = None,
    tenant_id: str = "default",
) -> str:
    payload = {
        "namespace": namespace,
        "prompt": prompt,
        "model": model,
        "params": params,
        "tool_inputs": tool_inputs or {},
        "tenant_id": tenant_id,
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return f"{namespace}:{tenant_id}:{digest}"


class InMemoryCacheProvider(CacheProvider):
    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float | None]] = {}

    async def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires = entry
        if expires is not None and time.time() > expires:
            del self._store[key]
            return None
        return value

    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        expires = time.time() + ttl_seconds if ttl_seconds else None
        self._store[key] = (value, expires)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def invalidate(self, prefix: str) -> int:
        keys = [k for k in self._store if k.startswith(prefix)]
        for k in keys:
            del self._store[k]
        return len(keys)
