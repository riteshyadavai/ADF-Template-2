"""Langfuse tracer factory."""

from __future__ import annotations

from functools import lru_cache

from config.settings import Settings, get_settings
from factories.observability.langfuse.client import LangfuseTracer


@lru_cache(maxsize=1)
def make_langfuse_tracer() -> LangfuseTracer:
    return LangfuseTracer(get_settings().langfuse)


def make_langfuse_tracer_for(settings: Settings) -> LangfuseTracer:
    return LangfuseTracer(settings.langfuse)
