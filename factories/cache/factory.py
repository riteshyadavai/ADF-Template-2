"""Cache factory — memory or Redis backends."""

from __future__ import annotations

from config.settings import Settings, get_settings
from factories.cache.memory.client import InMemoryCacheProvider
from factories.cache.protocol import CacheProvider


def make_cache_provider(settings: Settings | None = None) -> CacheProvider:
    settings = settings or get_settings()
    backend = settings.cache.backend

    if backend == "redis":
        from factories.cache.redis.client import RedisCacheProvider

        return RedisCacheProvider(settings.cache.redis_url)

    return InMemoryCacheProvider()
