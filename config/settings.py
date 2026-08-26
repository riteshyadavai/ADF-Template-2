"""Centralized configuration for all factory components."""

from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = Path(__file__).resolve().parent


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

    backend: str = "memory"  # memory | redis
    redis_url: str = "redis://localhost:6379/0"
    default_ttl_seconds: int = 3600


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DB_")

    hot_url: str = "sqlite+aiosqlite:///./data/hot_state.db"
    cold_url: str = "sqlite+aiosqlite:///./data/cold_state.db"


class VectorStoreSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="VECTOR_")

    backend: str = "memory"  # memory | qdrant | pgvector | weaviate | opensearch
    embedding_model: str = "text-embedding-004"
    embedding_model_version: str = "v1"
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
    eval: EvalSettings = Field(default_factory=EvalSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)

    git_sha: str = Field(default="unknown", validation_alias="GIT_SHA")
    prompt_version: str = Field(default="latest", validation_alias="PROMPT_VERSION")


def load_environment_overlay(env: Environment) -> dict[str, Any]:
    path = CONFIG_DIR / "environments" / f"{env.value}.yaml"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    overlay = load_environment_overlay(settings.environment)
    if overlay:
        merged = settings.model_dump()
        _deep_merge(merged, overlay)
        settings = Settings.model_validate(merged)
    return settings


def _deep_merge(base: dict, overlay: dict) -> None:
    for key, value in overlay.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
