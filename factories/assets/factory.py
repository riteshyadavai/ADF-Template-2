"""Hydrate enterprise_agent_sdk assets from settings."""

from __future__ import annotations

from config.settings import AssetsSettings, Settings, get_settings
from factories.assets.protocol import AssetBundle, AssetsConfigError


def make_asset_bundle(settings: Settings | None = None) -> AssetBundle:
    settings = settings or get_settings()
    assets = settings.assets
    if not assets.enabled:
        return AssetBundle(enabled=False)
    try:
        from enterprise_agent_sdk.assets import (
            AnySQLSafeExecutor,
            DynamicOpenAPIClient,
            HITLApprovalGateway,
            OmniChannelDocumentCrawler,
            PIIToxicContentShield,
            ZeroCodeVectorSyncNode,
        )
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "enterprise-agent-sdk is required when ASSETS_ENABLED=true. "
            "Install with: uv sync --extra asset-factory "
            "(needs GitHub access to 66degrees/agentic-asset-factory)."
        ) from exc

    return AssetBundle(
        enabled=True,
        sql=_hydrate_sql(AnySQLSafeExecutor, assets),
        openapi=_hydrate_openapi(DynamicOpenAPIClient, assets),
        hitl=_hydrate_hitl(HITLApprovalGateway, assets),
        pii=_hydrate_pii(PIIToxicContentShield, assets),
        crawler=_hydrate_crawler(OmniChannelDocumentCrawler, assets),
        vector_sync=_hydrate_vector(ZeroCodeVectorSyncNode, assets),
    )


def _secret(value: object) -> str:
    if value is None:
        return ""
    if hasattr(value, "get_secret_value"):
        return str(value.get_secret_value() or "")
    return str(value)


def _hydrate_sql(cls: type, assets: AssetsSettings) -> object | None:
    db_url = _secret(assets.sql_db_url)
    if not db_url or db_url == "CHANGE_ME":
        return None
    return cls().hydrate(
        {
            "db_url": db_url,
            "read_only": assets.sql_read_only,
            "max_rows": assets.sql_max_rows,
            "allowed_tables": list(assets.sql_allowed_tables),
        }
    )


def _hydrate_openapi(cls: type, assets: AssetsSettings) -> object | None:
    if not assets.openapi_base_url or not assets.openapi_spec_url:
        return None
    config: dict = {
        "base_url": assets.openapi_base_url,
        "openapi_spec_url": assets.openapi_spec_url,
        "max_retries": assets.openapi_max_retries,
    }
    auth = _secret(assets.openapi_auth_header)
    if auth and auth != "CHANGE_ME":
        config["auth_header"] = auth
    return cls().hydrate(config)


def _hydrate_hitl(cls: type, assets: AssetsSettings) -> object | None:
    if not assets.hitl_webhook_url:
        return None
    return cls().hydrate(
        {
            "webhook_url": assets.hitl_webhook_url,
            "timeout_seconds": assets.hitl_timeout_seconds,
            "required_approvers": assets.hitl_required_approvers,
        }
    )


def _hydrate_pii(cls: type, assets: AssetsSettings) -> object:
    return cls().hydrate(
        {
            "block_on_toxicity": assets.pii_block_on_toxicity,
            "toxicity_keywords": list(assets.pii_toxicity_keywords),
        }
    )


def _hydrate_crawler(cls: type, assets: AssetsSettings) -> object | None:
    source = (assets.crawler_source_type or "local").lower()
    folders = list(assets.crawler_allowed_folders)
    if source in {"gdrive", "sharepoint"}:
        raise AssetsConfigError(
            "Crawler source_type gdrive/sharepoint is stubbed in enterprise-agent-sdk. "
            "Use local or s3."
        )
    if source == "s3":
        creds = {
            k: v
            for k, v in {
                "access_key": _secret(assets.crawler_s3_access_key),
                "secret_key": _secret(assets.crawler_s3_secret_key),
            }.items()
            if v and v != "CHANGE_ME"
        }
        if not creds or not folders:
            return None
        return cls().hydrate(
            {
                "source_type": "s3",
                "allowed_folders": folders,
                "file_extensions": list(assets.crawler_file_extensions),
                "credentials": creds,
            }
        )
    if source != "local" or not folders:
        return None
    return cls().hydrate(
        {
            "source_type": "local",
            "allowed_folders": folders,
            "file_extensions": list(assets.crawler_file_extensions),
        }
    )


def _hydrate_vector(cls: type, assets: AssetsSettings) -> object:
    provider = (assets.vector_provider or "memory").lower()
    if provider != "memory":
        raise AssetsConfigError(
            "ASSETS_VECTOR_PROVIDER must be 'memory'. "
            "pinecone/milvus/qdrant are stubbed in enterprise-agent-sdk."
        )
    return cls().hydrate(
        {
            "vector_provider": "memory",
            "chunk_size": assets.vector_chunk_size,
            "chunk_overlap": assets.vector_chunk_overlap,
        }
    )
