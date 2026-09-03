"""Looker API 4.0 client via looker-sdk."""

from __future__ import annotations

import json
import os
from typing import Any

from config.settings import LookerSettings
from factories.looker.protocol import LookerClient


class LookerDisabledError(RuntimeError):
    pass


class LookerSdkClient(LookerClient):
    def __init__(self, settings: LookerSettings, sdk: Any | None = None) -> None:
        self._settings = settings
        self._sdk = sdk
        self.enabled = bool(settings.enabled and sdk is not None)

    def _require(self) -> Any:
        if not self.enabled or self._sdk is None:
            raise LookerDisabledError(
                "Looker is disabled or not configured. Set LOOKER_ENABLED=true "
                "and LOOKERSDK_BASE_URL / LOOKERSDK_CLIENT_ID / LOOKERSDK_CLIENT_SECRET."
            )
        return self._sdk

    def me(self) -> dict[str, Any]:
        user = self._require().me()
        if isinstance(user, dict):
            return user
        return {
            "id": getattr(user, "id", None),
            "first_name": getattr(user, "first_name", None),
            "last_name": getattr(user, "last_name", None),
            "email": getattr(user, "email", None),
        }

    def run_look(self, look_id: str, result_format: str = "json") -> list[dict[str, Any]] | str:
        raw = self._require().run_look(look_id=look_id, result_format=result_format)
        return _parse_looker_result(raw, result_format)

    def run_inline_query(
        self,
        *,
        model: str,
        view: str,
        fields: list[str],
        filters: dict[str, str] | None = None,
        limit: int = 100,
        result_format: str = "json",
    ) -> list[dict[str, Any]] | str:
        body = {
            "model": model,
            "view": view,
            "fields": fields,
            "filters": filters or {},
            "limit": str(limit),
        }
        raw = self._require().run_inline_query(result_format=result_format, body=body)
        return _parse_looker_result(raw, result_format)


def apply_looker_sdk_env(settings: LookerSettings) -> None:
    """Map factory settings onto official LOOKERSDK_* names for init40()."""
    from dotenv import load_dotenv

    load_dotenv()
    base_url = settings.base_url or os.environ.get("LOOKERSDK_BASE_URL", "")
    client_id = (
        settings.client_id.get_secret_value()
        if settings.client_id
        else os.environ.get("LOOKERSDK_CLIENT_ID", "")
    )
    client_secret = (
        settings.client_secret.get_secret_value()
        if settings.client_secret
        else os.environ.get("LOOKERSDK_CLIENT_SECRET", "")
    )
    if base_url:
        os.environ["LOOKERSDK_BASE_URL"] = base_url
    if client_id:
        os.environ["LOOKERSDK_CLIENT_ID"] = client_id
    if client_secret:
        os.environ["LOOKERSDK_CLIENT_SECRET"] = client_secret
    os.environ["LOOKERSDK_API_VERSION"] = settings.api_version
    os.environ["LOOKERSDK_VERIFY_SSL"] = "true" if settings.verify_ssl else "false"
    os.environ["LOOKERSDK_TIMEOUT"] = str(settings.timeout)


def _parse_looker_result(raw: Any, result_format: str) -> list[dict[str, Any]] | str:
    if result_format != "json":
        return raw if isinstance(raw, str) else str(raw)
    if isinstance(raw, list):
        return [item if isinstance(item, dict) else {"value": item} for item in raw]
    if isinstance(raw, dict):
        return [raw]
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode()
    if isinstance(raw, str) and raw.strip():
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [item if isinstance(item, dict) else {"value": item} for item in parsed]
        if isinstance(parsed, dict):
            return [parsed]
    return []
