"""Factory and project answers collected by init."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
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

    langfuse: bool = False
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
    plan_mode: str = "accepted"
    dest_mode: str = "new_folder"
    workflow_plan: dict | None = None

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

    def render_app_yaml(self) -> str:
        payload = {
            "template": {
                "package": self.template_package,
                "version": self.template_version,
            },
            "project": {
                "domain": self.domain,
                "workflow": self.workflow,
                "plan": self.plan_mode,
            },
            "environment": self.environment,
            "gateway": {
                "provider": self.gateway,
                "default_model": self.default_model,
            },
            "cache": {
                "backend": self.cache,
                "redis_url": self.redis_url,
                "memcached_url": self.memcached_url,
                "default_ttl_seconds": self.cache_ttl,
            },
            "vector": {
                "backend": self.vector,
                "embeddings_backend": self.embeddings,
                "embedding_model": self.embedding_model,
                "opensearch_url": self.opensearch_url,
                "qdrant_url": self.qdrant_url,
            },
            "database": {
                "backend": self.state_backend,
                "hot_url": self.db_hot_url,
                "cold_url": self.db_cold_url,
            },
            "pdf": {"backend": self.parser},
            "eval": {
                "backend": self.eval_backend,
                "threshold": self.eval_threshold,
            },
            "observability": {
                "langfuse": self.langfuse,
                "logfire": self.logfire,
            },
            "adk": {"enabled": self.adk},
            "a2a": {"enabled": self.a2a},
            "security": {
                "secrets_backend": self.secrets_backend,
                "content_guardrail_backend": self.guardrails,
            },
            "tenant": {"isolation_mode": self.tenant_isolation},
        }
        return yaml.safe_dump(payload, sort_keys=False)

    def to_json_dict(self) -> dict:
        data = self.model_dump(mode="json")
        data["output"] = str(self.output)
        return data

    def write_choices_file(self, dest: Path) -> None:
        (dest / "factory-choices.json").write_text(
            json.dumps(self.to_json_dict(), indent=2),
            encoding="utf-8",
        )


def factory_choices_from_app_yaml(
    raw: dict,
    *,
    project_name: str | None = None,
    output: Path | None = None,
) -> FactoryChoices:
    project = raw.get("project") or {}
    template = raw.get("template") or {}
    gateway = raw.get("gateway") or {}
    cache = raw.get("cache") or {}
    vector = raw.get("vector") or {}
    database = raw.get("database") or {}
    pdf = raw.get("pdf") or {}
    ev = raw.get("eval") or {}
    obs = raw.get("observability") or {}
    adk = raw.get("adk") or {}
    a2a = raw.get("a2a") or {}
    security = raw.get("security") or {}
    tenant = raw.get("tenant") or {}
    domain = str(project.get("domain") or "")
    workflow = str(project.get("workflow") or "")
    name = project_name or (f"{domain}-{workflow}" if domain and workflow else "replayed-project")
    dest = output or Path(f"./{name}")
    return FactoryChoices(
        project_name=name,
        output=dest,
        slug=name.replace("-", "_").replace(" ", "_"),
        domain=domain,
        workflow=workflow,
        plan_mode=str(project.get("plan") or "accepted"),
        template_package=str(template.get("package") or "66degrees-factory"),
        template_version=str(template.get("version") or template_version()),
        gateway=str(gateway.get("provider") or "litellm"),
        default_model=str(gateway.get("default_model") or "gemini/gemini-2.5-flash"),
        cache=str(cache.get("backend") or "memory"),
        redis_url=str(cache.get("redis_url") or "redis://localhost:6379/0"),
        memcached_url=str(cache.get("memcached_url") or "memcached://localhost:11211"),
        cache_ttl=int(cache.get("default_ttl_seconds") or 3600),
        vector=str(vector.get("backend") or "memory"),
        embeddings=str(vector.get("embeddings_backend") or "litellm"),
        embedding_model=str(vector.get("embedding_model") or "text-embedding-004"),
        opensearch_url=str(vector.get("opensearch_url") or "http://localhost:9200"),
        qdrant_url=str(vector.get("qdrant_url") or "http://localhost:6333"),
        parser=str(pdf.get("backend") or "docling"),
        eval_backend=str(ev.get("backend") or "local"),
        eval_threshold=float(ev.get("threshold") or 0.8),
        langfuse=bool(obs.get("langfuse", False)),
        logfire=bool(obs.get("logfire", False)),
        state_backend=str(database.get("backend") or "memory"),
        db_hot_url=str(database.get("hot_url") or "sqlite+aiosqlite:///./data/hot_state.db"),
        db_cold_url=str(database.get("cold_url") or "sqlite+aiosqlite:///./data/cold_state.db"),
        adk=bool(adk.get("enabled", False)),
        a2a=bool(a2a.get("enabled", False)),
        secrets_backend=str(security.get("secrets_backend") or "env"),
        guardrails=str(security.get("content_guardrail_backend") or "passthrough"),
        tenant_isolation=str(tenant.get("isolation_mode") or "logical"),
        environment=str(raw.get("environment") or "local"),
    )


def load_choices_file(path: Path) -> FactoryChoices:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        raw = yaml.safe_load(text) or {}
        if not isinstance(raw, dict):
            raise ValueError(f"Invalid app.yaml: {path}")
        return factory_choices_from_app_yaml(raw)
    raw = json.loads(text)
    return FactoryChoices.model_validate(raw)
