"""Database / state factory."""

from __future__ import annotations

from agents.memory import ColdStateStore, HotStateStore
from config.settings import Settings, get_settings
from factories.database.memory.client import InMemoryColdStateStore, InMemoryHotStateStore


def make_hot_state_store(settings: Settings | None = None) -> HotStateStore:
    settings = settings or get_settings()
    if settings.database.backend == "sqlite":
        from factories.database.sqlite.client import SqliteHotStateStore

        return SqliteHotStateStore(settings.database.hot_url)
    return InMemoryHotStateStore()


def make_cold_state_store(settings: Settings | None = None) -> ColdStateStore:
    settings = settings or get_settings()
    if settings.database.backend == "sqlite":
        from factories.database.sqlite.client import SqliteColdStateStore

        return SqliteColdStateStore(settings.database.cold_url)
    return InMemoryColdStateStore()
