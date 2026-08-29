"""Factory and project answers collected by init."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from cli.template_root import template_version


class FactoryChoices(BaseModel):
    project_name: str
    output: Path
    slug: str
    domain: str
    workflow: str

    gateway: str = "litellm"
    default_model: str = "gemini/gemini-2.5-flash"
    bedrock_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    cache: str = "memory"
    redis_url: str = "redis://localhost:6379/0"
    memcached_url: str = "memcached://localhost:11211"
    cache_ttl: int = 3600

    vector: str = "memory"
    opensearch_url: str = "http://localhost:9200"
    qdrant_url: str = "http://localhost:6333"

    embeddings: str = "litellm"
    embedding_model: str = "text-embedding-004"

    parser: str = "docling"
    guardrails: str = "passthrough"
    eval_backend: str = "local"
    eval_threshold: float = 0.8

    langfuse: bool = True
    logfire: bool = False

    state_backend: str = "memory"
    db_hot_url: str = "sqlite+aiosqlite:///./data/hot_state.db"
    db_cold_url: str = "sqlite+aiosqlite:///./data/cold_state.db"

    adk: bool = False
    a2a: bool = False
    mcp_examples: bool = False

    secrets_backend: str = "env"
    tenant_isolation: str = "logical"
    environment: str = "local"

    template_package: str = "66degrees-factory"
    template_version: str = Field(default_factory=template_version)

    def dest(self) -> Path:
        return self.output.expanduser().resolve()

    def extras_hints(self) -> list[str]:
        from cli.factory_catalog import extras_for_choices

        hints = extras_for_choices(
            gateway=self.gateway,
            cache=self.cache,
            vector=self.vector,
            parser=self.parser,
            guardrails=self.guardrails,
            eval_backend=self.eval_backend,
            langfuse=self.langfuse,
            logfire=self.logfire,
        )
        if self.adk:
            hints.append("# then: uv run python examples/adk_smoke.py")
        if self.a2a:
            hints.append("# A2A: uv run python examples/a2a_client_smoke.py")
        return hints

    def render_env(self) -> str:
        lines = [
            f"ENVIRONMENT={self.environment}",
            "GIT_SHA=local",
            "PROMPT_VERSION=latest",
            "",
            "GOOGLE_API_KEY=CHANGE_ME",
            f"GATEWAY_PROVIDER={self.gateway}",
            f"GATEWAY_DEFAULT_MODEL={self.default_model}",
            "GATEWAY_REDACT_PII=true",
            f"OLLAMA_BASE_URL={self.ollama_url}",
            f"OLLAMA_MODEL={self.ollama_model}",
            f"BEDROCK_REGION={self.bedrock_region}",
            f"BEDROCK_MODEL_ID={self.bedrock_model_id}",
            "",
            "OBS_LOG_LEVEL=INFO",
            "OBS_PROMETHEUS_ENABLED=true",
            f"LANGFUSE_ENABLED={str(self.langfuse).lower()}",
            "LANGFUSE_PUBLIC_KEY=CHANGE_ME",
            "LANGFUSE_SECRET_KEY=CHANGE_ME",
            "LANGFUSE_HOST=https://cloud.langfuse.com",
            f"LOGFIRE_ENABLED={str(self.logfire).lower()}",
            "LOGFIRE_TOKEN=CHANGE_ME",
            f"LOGFIRE_SERVICE_NAME={self.slug}",
            "",
            f"CACHE_BACKEND={self.cache}",
            f"CACHE_REDIS_URL={self.redis_url}",
            f"CACHE_MEMCACHED_URL={self.memcached_url}",
            f"CACHE_DEFAULT_TTL_SECONDS={self.cache_ttl}",
            "",
            f"DB_BACKEND={self.state_backend}",
            f"DB_HOT_URL={self.db_hot_url}",
            f"DB_COLD_URL={self.db_cold_url}",
            "",
            f"VECTOR_BACKEND={self.vector}",
            f"VECTOR_EMBEDDINGS_BACKEND={self.embeddings}",
            f"EMBEDDINGS_BACKEND={self.embeddings}",
            f"VECTOR_EMBEDDING_MODEL={self.embedding_model}",
            "VECTOR_EMBEDDING_MODEL_VERSION=v1",
            f"VECTOR_OPENSEARCH_URL={self.opensearch_url}",
            f"VECTOR_QDRANT_URL={self.qdrant_url}",
            "",
            f"PDF_BACKEND={self.parser}",
            "",
            f"ADK_ENABLED={str(self.adk).lower()}",
            f"ADK_APP_NAME={self.slug}",
            f"A2A_ENABLED={str(self.a2a).lower()}",
            f"A2A_AGENT_NAME={self.slug}",
            "A2A_PEER_URL=http://127.0.0.1:8000",
            "",
            f"EVAL_BACKEND={self.eval_backend}",
            f"EVAL_THRESHOLD={self.eval_threshold}",
            "",
            f"SECURITY_SECRETS_BACKEND={self.secrets_backend}",
            f"SECURITY_CONTENT_GUARDRAIL_BACKEND={self.guardrails}",
            "SECURITY_ENABLE_GUARDRAILS=true",
            "",
            "TENANT_DEFAULT_TENANT_ID=default",
            f"TENANT_ISOLATION_MODE={self.tenant_isolation}",
        ]
        if self.mcp_examples:
            lines.extend(
                [
                    "",
                    "# MCP examples (see domains/<domain>/workflows/<workflow>/mcp.yaml)",
                    "# STDIO or HTTP connection params are not secrets; keep keys out of git.",
                ]
            )
        if self.embeddings == "jina":
            lines.extend(["", "JINA_API_KEY=CHANGE_ME"])
        return "\n".join(lines) + "\n"

    def to_json_dict(self) -> dict:
        data = self.model_dump(mode="json")
        data["output"] = str(self.output)
        return data

    def write_choices_file(self, dest: Path) -> None:
        (dest / "factory-choices.json").write_text(
            json.dumps(self.to_json_dict(), indent=2),
            encoding="utf-8",
        )


def load_choices_file(path: Path) -> FactoryChoices:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return FactoryChoices.model_validate(raw)
