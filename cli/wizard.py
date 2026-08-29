"""Interactive prompts for init (skipped when flags or --yes are set)."""

from __future__ import annotations

from pathlib import Path

from cli.catalog import get_domain, load_domains
from cli.choices import FactoryChoices
from cli.factory_catalog import backend_id_from_label, labeled_backend_choices


def _select(message: str, choices: list[str], default: str) -> str:
    import questionary

    result = questionary.select(message, choices=choices, default=default).ask()
    if result is None:
        raise SystemExit("Cancelled")
    return result


def _text(message: str, default: str) -> str:
    import questionary

    result = questionary.text(message, default=default).ask()
    if result is None:
        raise SystemExit("Cancelled")
    return result


def _confirm(message: str, default: bool) -> bool:
    import questionary

    result = questionary.confirm(message, default=default).ask()
    if result is None:
        raise SystemExit("Cancelled")
    return result


def _select_backend(capability: str, current: str) -> str:
    labels = labeled_backend_choices(capability)
    default = next((label for label in labels if label.startswith(f"{current} ")), labels[0])
    return backend_id_from_label(_select(capability, labels, default))


def run_wizard(partial: FactoryChoices) -> FactoryChoices:
    name = partial.project_name or _text("Project name", "my-agent-project")
    default_out = str(partial.output) if str(partial.output) != "." else f"./{name}"
    output = Path(_text("Output directory", default_out))
    default_slug = name.replace("-", "_").replace(" ", "_")
    slug = _text("Package slug", partial.slug or default_slug)

    domains = load_domains()
    domain_id = partial.domain or _select(
        "Domain",
        [d.id for d in domains],
        domains[0].id,
    )
    domain = get_domain(domain_id)
    workflow_labels = {f"{w.id} — {w.name}": w.id for w in domain.workflows}
    if partial.workflow:
        workflow_id = partial.workflow
    else:
        picked = _select("Workflow", list(workflow_labels), next(iter(workflow_labels)))
        workflow_id = workflow_labels[picked]

    gateway = _select_backend("gateway", partial.gateway)
    default_model = _text("Default model", partial.default_model)
    bedrock_region = partial.bedrock_region
    bedrock_model_id = partial.bedrock_model_id
    ollama_url = partial.ollama_url
    ollama_model = partial.ollama_model
    if gateway == "bedrock":
        bedrock_region = _text("Bedrock region", bedrock_region)
        bedrock_model_id = _text("Bedrock model id", bedrock_model_id)
    if gateway == "ollama":
        ollama_url = _text("Ollama base URL", ollama_url)
        ollama_model = _text("Ollama model", ollama_model)

    cache = _select_backend("cache", partial.cache)
    redis_url = partial.redis_url
    memcached_url = partial.memcached_url
    if cache == "redis":
        redis_url = _text("Redis URL", redis_url)
    if cache == "memcached":
        memcached_url = _text("Memcached URL", memcached_url)

    vector = _select_backend("vector", partial.vector)
    opensearch_url = partial.opensearch_url
    qdrant_url = partial.qdrant_url
    if vector == "opensearch":
        opensearch_url = _text("OpenSearch URL", opensearch_url)
    if vector == "qdrant":
        qdrant_url = _text("Qdrant URL", qdrant_url)

    embeddings = _select_backend("embeddings", partial.embeddings)
    parser = _select_backend("parser", partial.parser)
    guardrails = _select_backend("guardrails", partial.guardrails)
    eval_backend = _select_backend("eval", partial.eval_backend)
    langfuse = _confirm("Enable Langfuse", partial.langfuse)
    logfire = _confirm("Enable Logfire", partial.logfire)
    state_backend = _select_backend("state", partial.state_backend)
    adk = _confirm("Enable Google ADK", partial.adk)
    a2a = _confirm("Enable A2A", partial.a2a)
    mcp_examples = _confirm("Include MCP connection examples", partial.mcp_examples)
    secrets_backend = _select_backend("secrets", partial.secrets_backend)
    tenant_isolation = _select(
        "Tenant isolation",
        ["logical", "namespace", "dedicated"],
        partial.tenant_isolation,
    )
    environment = _select(
        "Environment",
        ["local", "dev", "test", "uat", "production"],
        partial.environment,
    )

    return FactoryChoices(
        project_name=name,
        output=output,
        slug=slug,
        domain=domain_id,
        workflow=workflow_id,
        gateway=gateway,
        default_model=default_model,
        bedrock_region=bedrock_region,
        bedrock_model_id=bedrock_model_id,
        ollama_url=ollama_url,
        ollama_model=ollama_model,
        cache=cache,
        redis_url=redis_url,
        memcached_url=memcached_url,
        vector=vector,
        opensearch_url=opensearch_url,
        qdrant_url=qdrant_url,
        embeddings=embeddings,
        parser=parser,
        guardrails=guardrails,
        eval_backend=eval_backend,
        langfuse=langfuse,
        logfire=logfire,
        state_backend=state_backend,
        adk=adk,
        a2a=a2a,
        mcp_examples=mcp_examples,
        secrets_backend=secrets_backend,
        tenant_isolation=tenant_isolation,
        environment=environment,
    )
