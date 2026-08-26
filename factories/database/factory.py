"""Database / state factory."""

from __future__ import annotations

from agents.memory import ColdStateStore, HotStateStore
from config.settings import Settings
from factories.database.memory.client import InMemoryColdStateStore, InMemoryHotStateStore


def make_hot_state_store(settings: Settings | None = None) -> HotStateStore:
    return InMemoryHotStateStore()


def make_cold_state_store(settings: Settings | None = None) -> ColdStateStore:
    return InMemoryColdStateStore()
