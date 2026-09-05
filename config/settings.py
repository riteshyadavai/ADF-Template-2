"""Centralized configuration for all factory components."""

import os
from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Environment(StrEnum):
    LOCAL = "local"
    DEV = "dev"
    TEST = "test"
    UAT = "uat"
    PRODUCTION = "production"


class ObservabilitySettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OBS_")

    enabled: bool = True
    log_level: str = "INFO"
    otel_endpoint: str | None = None
    prometheus_enabled: bool = True


class LangfuseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LANGFUSE_")

    enabled: bool = True
    public_key: SecretStr | None = None
    secret_key: SecretStr | None = None
    host: str = "https://cloud.langfuse.com"
    flush_at: int = 15
    flush_interval: float = 1.0
    debug: bool = False


class LogfireSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LOGFIRE_")

    enabled: bool = False
    token: SecretStr | None = None
    service_name: str = "multi-agent-factory"
    send_to_logfire: str = "if-token-present"


class GatewaySettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GATEWAY_")

    provider: str = "litellm"  # litellm | bedrock | kong
    default_model: str = "gemini/gemini-2.5-flash"
    fallback_models: list[str] = Field(default_factory=lambda: ["gemini/gemini-2.0-flash"])
    max_retries: int = 3
    daily_budget_usd: float | None = None
    monthly_budget_usd: float | None = None
    budget_downgrade_model: str | None = "gemini/gemini-2.0-flash"
    redact_pii: bool = True


class BedrockSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BEDROCK_")

    region: str = "us-east-1"
    model_id: str = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    guardrail_id: str | None = None
    guardrail_version: str = "DRAFT"


class OllamaSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OLLAMA_")

    base_url: str = "http://localhost:11434"
    model: str = "llama3.2"
    timeout_seconds: float = 120.0


class CacheSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CACHE_")

    backend: str = "memory"  # memory | redis | memcached
    redis_url: str = "redis://localhost:6379/0"
    memcached_url: str = "memcached://localhost:11211"
    default_ttl_seconds: int = 3600


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DB_")

    backend: str = "memory"  # memory | sqlite
    hot_url: str = "sqlite+aiosqlite:///./data/hot_state.db"
    cold_url: str = "sqlite+aiosqlite:///./data/cold_state.db"


class VectorStoreSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="VECTOR_")

    backend: str = "memory"  # memory | qdrant | pgvector | weaviate | opensearch
    embedding_model: str = "text-embedding-004"
    embedding_model_version: str = "v1"
    embeddings_backend: str = "litellm"  # litellm | jina
    qdrant_url: str | None = None
    opensearch_url: str = "http://localhost:9200"
    opensearch_username: str | None = None
    opensearch_password: SecretStr | None = None
    opensearch_verify_certs: bool = True


class PdfSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PDF_")

    backend: str = "docling"
    max_pages: int = 100
    max_file_size_mb: int = 20
    enable_ocr: bool = False
    enable_table_structure: bool = True


class AdkSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ADK_")

    enabled: bool = False
    app_name: str = "multi-agent-factory"
    agent_name: str = "factory_agent"
    default_model: str = "gemini-2.5-flash"
    description: str = "Google ADK agent created by the factory template."
    instruction: str = "You are a helpful assistant."


class A2ASettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="A2A_")

    enabled: bool = False
    public_base_url: str = "http://127.0.0.1:8000"
    jsonrpc_path: str = "/a2a/jsonrpc"
    rest_path: str = "/a2a/rest"
    agent_name: str = "multi-agent-factory"
    agent_description: str = "A2A-compatible agent exposed by the factory template."
    agent_version: str = "1.0.0"
    default_skill_id: str = "default"
    default_skill_name: str = "Default"
    default_skill_description: str = "Default conversational skill."
    default_input_modes: list[str] = Field(default_factory=lambda: ["text/plain"])
    default_output_modes: list[str] = Field(default_factory=lambda: ["text/plain"])
    streaming: bool = True
    extended_agent_card: bool = False
    client_timeout_seconds: float = 60.0
    peer_url: str = "http://127.0.0.1:8000"


class LookerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LOOKER_")

    enabled: bool = False
    base_url: str = ""
    client_id: SecretStr | None = None
    client_secret: SecretStr | None = None
    verify_ssl: bool = True
    timeout: int = 120
    api_version: str = "4.0"


class BqmlSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BQML_")

    enabled: bool = False
    project: str = ""
    location: str = "US"
    dataset: str = ""
    model: str = ""


def _split_csv(value: object) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [part.strip() for part in str(value).split(",") if part.strip()]


class AssetsSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ASSETS_")

    enabled: bool = False
    sql_db_url: SecretStr | None = None
    sql_read_only: bool = True
    sql_max_rows: int = 200
    sql_allowed_tables: list[str] = Field(default_factory=list)
    openapi_base_url: str = ""
    openapi_spec_url: str = ""
    openapi_auth_header: SecretStr | None = None
    openapi_max_retries: int = 3
    hitl_webhook_url: str = ""
    hitl_timeout_seconds: int = 3600
    hitl_required_approvers: int = 1
    pii_block_on_toxicity: bool = True
    pii_toxicity_keywords: list[str] = Field(default_factory=list)
    crawler_source_type: str = "local"
    crawler_allowed_folders: list[str] = Field(default_factory=list)
    crawler_file_extensions: list[str] = Field(default_factory=lambda: [".txt", ".md"])
    crawler_s3_access_key: SecretStr | None = None
    crawler_s3_secret_key: SecretStr | None = None
    vector_provider: str = "memory"
    vector_chunk_size: int = 500
    vector_chunk_overlap: int = 50

    @field_validator(
        "sql_allowed_tables",
        "pii_toxicity_keywords",
        "crawler_allowed_folders",
        "crawler_file_extensions",
        mode="before",
    )
    @classmethod
    def _csv_lists(cls, value: object) -> list[str]:
        return _split_csv(value)


class EvalSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EVAL_")

    backend: str = "local"  # local | deepeval
    threshold: float = 0.8
    model: str | None = None


class SecuritySettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SECURITY_")

    secrets_backend: str = "env"  # env | vault | aws_secrets_manager | sops
    oidc_issuer: str | None = None
    audit_log_path: str = "./data/audit.log"
    retention_days: int = 90
    enable_guardrails: bool = True
    content_guardrail_backend: str = "passthrough"  # passthrough | bedrock


class TenantSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TENANT_")

    default_tenant_id: str = "default"
    isolation_mode: str = "logical"  # logical | namespace | dedicated


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "multi-agent-factory"
    environment: Environment = Environment.LOCAL
    debug: bool = False
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    tenant: TenantSettings = Field(default_factory=TenantSettings)
    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)
    langfuse: LangfuseSettings = Field(default_factory=LangfuseSettings)
    logfire: LogfireSettings = Field(default_factory=LogfireSettings)
    gateway: GatewaySettings = Field(default_factory=GatewaySettings)
    bedrock: BedrockSettings = Field(default_factory=BedrockSettings)
    ollama: OllamaSettings = Field(default_factory=OllamaSettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    vector_store: VectorStoreSettings = Field(default_factory=VectorStoreSettings)
    pdf: PdfSettings = Field(default_factory=PdfSettings)
    adk: AdkSettings = Field(default_factory=AdkSettings)
    a2a: A2ASettings = Field(default_factory=A2ASettings)
    looker: LookerSettings = Field(default_factory=LookerSettings)
    bqml: BqmlSettings = Field(default_factory=BqmlSettings)
    assets: AssetsSettings = Field(default_factory=AssetsSettings)
    eval: EvalSettings = Field(default_factory=EvalSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)

    git_sha: str = Field(default="unknown", validation_alias="GIT_SHA")
    prompt_version: str = Field(default="latest", validation_alias="PROMPT_VERSION")


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    return raw if isinstance(raw, dict) else {}


def load_app_yaml(root: Path | None = None) -> dict[str, Any]:
    base = root or PROJECT_ROOT
    return _normalize_app_yaml(_load_yaml(base / "config" / "app.yaml"))


def _normalize_app_yaml(raw: dict[str, Any]) -> dict[str, Any]:
    """Map app.yaml keys onto Settings field names."""
    out: dict[str, Any] = {}
    if "environment" in raw and isinstance(raw["environment"], str):
        out["environment"] = raw["environment"]
    if "gateway" in raw:
        out["gateway"] = raw["gateway"]
    if "cache" in raw:
        out["cache"] = raw["cache"]
    if "database" in raw:
        out["database"] = raw["database"]
    if "pdf" in raw:
        out["pdf"] = raw["pdf"]
    if "eval" in raw:
        out["eval"] = raw["eval"]
    if "adk" in raw:
        out["adk"] = raw["adk"]
    if "a2a" in raw:
        out["a2a"] = raw["a2a"]
    if "looker" in raw:
        out["looker"] = raw["looker"]
    if "bqml" in raw:
        out["bqml"] = raw["bqml"]
    if "assets" in raw:
        out["assets"] = raw["assets"]
    if "tenant" in raw:
        out["tenant"] = raw["tenant"]
    if "security" in raw:
        out["security"] = raw["security"]
    vector = raw.get("vector")
    if isinstance(vector, dict):
        vs = dict(vector)
        if "embeddings_backend" in vs and "embeddings_backend" not in vs:
            pass
        out["vector_store"] = vs
    obs = raw.get("observability")
    if isinstance(obs, dict):
        langfuse = _observability_plugin(obs.get("langfuse"))
        if langfuse:
            out["langfuse"] = langfuse
        logfire = _observability_plugin(obs.get("logfire"))
        if logfire:
            out["logfire"] = logfire
        if "otel_endpoint" in obs:
            out.setdefault("observability", {})["otel_endpoint"] = obs.get("otel_endpoint")
    return out


def _observability_plugin(value: Any) -> dict[str, Any]:
    if isinstance(value, bool):
        return {"enabled": value}
    if isinstance(value, dict):
        mapped: dict[str, Any] = {}
        if "enabled" in value:
            mapped["enabled"] = bool(value["enabled"])
        if "host" in value:
            mapped["host"] = value["host"]
        if "service_name" in value:
            mapped["service_name"] = value["service_name"]
        return mapped
    return {}


def load_environment_overlay(env: Environment, root: Path | None = None) -> dict[str, Any]:
    base = root or PROJECT_ROOT
    return _load_yaml(base / "config" / "environments" / f"{env.value}.yaml")


_ENV_NESTED_PREFIXES = (
    ("observability", "OBS_"),
    ("langfuse", "LANGFUSE_"),
    ("logfire", "LOGFIRE_"),
    ("gateway", "GATEWAY_"),
    ("bedrock", "BEDROCK_"),
    ("ollama", "OLLAMA_"),
    ("cache", "CACHE_"),
    ("database", "DB_"),
    ("vector_store", "VECTOR_"),
    ("pdf", "PDF_"),
    ("adk", "ADK_"),
    ("a2a", "A2A_"),
    ("looker", "LOOKER_"),
    ("bqml", "BQML_"),
    ("assets", "ASSETS_"),
    ("eval", "EVAL_"),
    ("security", "SECURITY_"),
    ("tenant", "TENANT_"),
)


def _environment_from_sources(app_overlay: dict[str, Any]) -> Environment:
    raw = os.environ.get("ENVIRONMENT") or app_overlay.get("environment") or "local"
    if isinstance(raw, Environment):
        return raw
    return Environment(str(raw).lower())


@lru_cache
def get_settings() -> Settings:
    defaults = Settings.model_construct().model_dump()
    app_overlay = load_app_yaml()
    if app_overlay:
        _deep_merge(defaults, app_overlay)
    env_name = _environment_from_sources(app_overlay)
    defaults["environment"] = env_name
    env_overlay = load_environment_overlay(env_name)
    if env_overlay:
        _deep_merge(defaults, env_overlay)
    yaml_settings = Settings.model_validate(defaults)
    env_settings = Settings()
    merged = yaml_settings.model_dump()
    for field, prefix in _ENV_NESTED_PREFIXES:
        if any(key.startswith(prefix) for key in os.environ):
            merged[field] = getattr(env_settings, field).model_dump()
    if "ENVIRONMENT" in os.environ:
        merged["environment"] = env_settings.environment
    return Settings.model_validate(merged)


def _deep_merge(base: dict, overlay: dict) -> None:
    for key, value in overlay.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
