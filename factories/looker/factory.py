"""Looker client factory."""

from __future__ import annotations

from config.settings import Settings, get_settings
from factories.looker.protocol import LookerClient
from factories.looker.sdk.client import LookerSdkClient, apply_looker_sdk_env


def make_looker_client(settings: Settings | None = None) -> LookerClient:
    settings = settings or get_settings()
    looker = settings.looker
    if not looker.enabled:
        return LookerSdkClient(looker, sdk=None)
    apply_looker_sdk_env(looker)
    try:
        import looker_sdk
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "looker-sdk is required when LOOKER_ENABLED=true. "
            "Install with: uv sync --extra looker"
        ) from exc
    sdk = looker_sdk.init40()
    return LookerSdkClient(looker, sdk=sdk)
