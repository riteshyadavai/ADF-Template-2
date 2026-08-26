"""Logfire infrastructure observability factory."""

from __future__ import annotations

import importlib
from typing import Any

from config.settings import Settings, get_settings
from shared.logger import get_logger

log = get_logger(__name__)


def configure_logfire(settings: Settings | None = None, app: Any | None = None) -> bool:
    """Configure Logfire and wire auto-instrumentation.

    When no token is set, Logfire still prints structured output locally but
    sends nothing to the cloud (`send_to_logfire=if-token-present`).
    Langfuse owns LLM semantic traces; Logfire owns infrastructure telemetry.
    """
    settings = settings or get_settings()
    if not settings.logfire.enabled:
        log.info("logfire_disabled")
        return False

    try:
        logfire = importlib.import_module("logfire")
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Logfire is enabled but its dependency is missing. "
            "Install it with: uv sync --group observability"
        ) from exc

    token = settings.logfire.token.get_secret_value() if settings.logfire.token else None
    logfire.configure(
        token=token,
        service_name=settings.logfire.service_name,
        environment=settings.environment.value,
        send_to_logfire=settings.logfire.send_to_logfire,
    )

    if app is not None:
        logfire.instrument_fastapi(app)

    _instrument_optional(logfire, "instrument_sqlalchemy")
    _instrument_optional(logfire, "instrument_redis")
    _instrument_optional(logfire, "instrument_httpx")
    _instrument_optional(logfire, "instrument_pydantic")

    log.info(
        "logfire_configured",
        service=settings.logfire.service_name,
        environment=settings.environment.value,
        send=settings.logfire.send_to_logfire,
    )
    return True


def _instrument_optional(logfire: Any, method_name: str) -> None:
    instrument = getattr(logfire, method_name, None)
    if instrument is None:
        return
    try:
        instrument()
    except Exception as exc:
        log.warning("logfire_instrumentation_skipped", method=method_name, error=str(exc))
