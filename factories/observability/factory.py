"""Observability factory composition root."""

from __future__ import annotations

from typing import Any

from config.settings import Settings, get_settings
from factories.observability.langfuse.client import LangfuseTracer
from factories.observability.langfuse.factory import make_langfuse_tracer, make_langfuse_tracer_for
from factories.observability.logfire.factory import configure_logfire as _configure_logfire
from factories.observability.protocol import ObservabilityBundle
from shared.logger import get_logger


def make_langfuse(settings: Settings | None = None) -> LangfuseTracer:
    if settings is None:
        return make_langfuse_tracer()
    return make_langfuse_tracer_for(settings)


def make_llm_tracer(settings: Settings | None = None) -> LangfuseTracer:
    """Backward-compatible alias for the Langfuse tracer."""
    return make_langfuse(settings)


def configure_logfire(settings: Settings | None = None, app: Any | None = None) -> bool:
    return _configure_logfire(settings, app)


def make_observability_bundle(settings: Settings | None = None) -> ObservabilityBundle:
    settings = settings or get_settings()
    langfuse = make_langfuse(settings)
    return ObservabilityBundle(
        logger=get_logger("factory"),
        langfuse=langfuse,
    )
