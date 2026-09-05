"""Enterprise Asset Factory bundle — wraps enterprise_agent_sdk assets."""

from __future__ import annotations

from typing import Any, Protocol


class AssetsDisabledError(RuntimeError):
    pass


class AssetsConfigError(RuntimeError):
    pass


class HydratedAsset(Protocol):
    def safe_run(self, **kwargs: Any) -> Any: ...


class AssetBundle:
    """Lazy accessors for hydrated SDK assets. Missing config raises; no fake results."""

    def __init__(
        self,
        *,
        enabled: bool,
        sql: Any | None = None,
        openapi: Any | None = None,
        hitl: Any | None = None,
        pii: Any | None = None,
        crawler: Any | None = None,
        vector_sync: Any | None = None,
    ) -> None:
        self.enabled = enabled
        self._sql = sql
        self._openapi = openapi
        self._hitl = hitl
        self._pii = pii
        self._crawler = crawler
        self._vector_sync = vector_sync

    def _require_enabled(self) -> None:
        if not self.enabled:
            raise AssetsDisabledError(
                "Asset Factory is disabled. Set ASSETS_ENABLED=true and "
                "uv sync --extra asset-factory."
            )

    def _require(self, tool: Any | None, env_hint: str) -> Any:
        self._require_enabled()
        if tool is None:
            raise AssetsConfigError(env_hint)
        return tool

    def sql(self) -> Any:
        return self._require(
            self._sql,
            "ASSETS_SQL_DB_URL is required to hydrate AnySQLSafeExecutor.",
        )

    def openapi(self) -> Any:
        return self._require(
            self._openapi,
            "ASSETS_OPENAPI_BASE_URL and ASSETS_OPENAPI_SPEC_URL are required.",
        )

    def hitl(self) -> Any:
        return self._require(self._hitl, "ASSETS_HITL_WEBHOOK_URL is required.")

    def pii(self) -> Any:
        return self._require(self._pii, "PII shield failed to hydrate.")

    def crawler(self) -> Any:
        return self._require(
            self._crawler,
            "ASSETS_CRAWLER_ALLOWED_FOLDERS is required "
            "(source_type=local, or s3 with credentials).",
        )

    def vector_sync(self) -> Any:
        return self._require(
            self._vector_sync,
            "Vector sync failed to hydrate (memory provider only).",
        )
