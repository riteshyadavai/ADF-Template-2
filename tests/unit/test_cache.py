"""Unit tests for content-addressed cache keys."""

import pytest

from factories.cache.memory.client import InMemoryCacheProvider, content_addressed_key


@pytest.mark.asyncio
async def test_cache_get_set():
    cache = InMemoryCacheProvider()
    key = content_addressed_key(
        namespace="llm",
        prompt="hello",
        model="gpt-4",
        params={"temperature": 0.7},
        tenant_id="tenant-a",
    )
    await cache.set(key, {"response": "world"}, ttl_seconds=60)
    assert await cache.get(key) == {"response": "world"}


@pytest.mark.asyncio
async def test_cache_tenant_isolation():
    key_a = content_addressed_key(
        namespace="llm", prompt="q", model="m", params={}, tenant_id="a"
    )
    key_b = content_addressed_key(
        namespace="llm", prompt="q", model="m", params={}, tenant_id="b"
    )
    assert key_a != key_b
