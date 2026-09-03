# Factories and extras

Selection is **runtime** (`config/app.yaml` then env). `init` writes those values. Allowed backends live in `catalogs/catalog.yaml` (CLI only).

!!! note "Planned backends"
    Kong, pgvector, weaviate, vault, sops raise `NotImplementedError`. Do not ship silent memory fakes.

```python
from factories.registry import get_factory_registry

reg = get_factory_registry()
cache = reg.cache()
gateway = reg.ai_gateway()
```

## Capability → env → backends

| Capability | Primary env | Implemented | Planned / notes | Extra or group |
|------------|-------------|-------------|-----------------|----------------|
| Gateway / LLM | `GATEWAY_PROVIDER` | `litellm`, `openai`, `bedrock`, `ollama` | `kong` | `--extra aws` for Bedrock |
| Cache | `CACHE_BACKEND` | `memory`, `redis`, `memcached` | — | `--extra cache-memcached` |
| Vector | `VECTOR_BACKEND` | `memory`, `opensearch`, `qdrant` | `pgvector`, `weaviate` | `--extra opensearch`, `--extra qdrant` |
| Embeddings | `EMBEDDINGS_BACKEND` / `VECTOR_EMBEDDINGS_BACKEND` | `litellm`, `jina` | — | `JINA_API_KEY` for Jina |
| Parser | `PDF_BACKEND` | `docling` | — | `--extra documents` |
| Guardrails | `SECURITY_CONTENT_GUARDRAIL_BACKEND` | `passthrough`, `bedrock` | — | `--extra aws` |
| Eval | `EVAL_BACKEND` | `local`, `deepeval` | — | `--group eval` |
| State | `DB_BACKEND` | `memory`, `sqlite` | — | `DB_HOT_URL`, `DB_COLD_URL` |
| Secrets | `SECURITY_SECRETS_BACKEND` | `env` | `vault`, `aws_secrets_manager`, `sops` | — |
| Observability | `LANGFUSE_*`, `LOGFIRE_*` | Langfuse, Logfire | — | `--group observability` |
| ADK | `ADK_ENABLED` | in-memory App + runner | `vertex` | `examples/adk_smoke.py` |
| A2A | `A2A_ENABLED` | SDK server + client | — | mount on FastAPI; `A2A_PEER_URL` |
| MCP | `mcp.yaml` | stdio, HTTP | — | `--mcp-examples` on init |
| Looker | `LOOKER_ENABLED` | `sdk` (`looker-sdk` init40) | — | `--extra looker` |
| BQML | `BQML_ENABLED` | `bigquery` | — | `--extra bqml` |

## Install extras after generate

```bash
cd /path/to/generated-project
uv sync
uv sync --extra aws
uv sync --extra documents
uv sync --extra opensearch
uv sync --extra qdrant
uv sync --extra cache-memcached
uv sync --extra looker
uv sync --extra bqml
uv sync --group eval
uv sync --group observability
```

## Useful env pairs

```bash
CACHE_BACKEND=redis
CACHE_REDIS_URL=redis://localhost:6379/0

CACHE_BACKEND=memcached
CACHE_MEMCACHED_URL=memcached://localhost:11211

VECTOR_BACKEND=qdrant
VECTOR_QDRANT_URL=http://localhost:6333

VECTOR_BACKEND=opensearch
VECTOR_OPENSEARCH_URL=http://localhost:9200

DB_BACKEND=sqlite
DB_HOT_URL=sqlite+aiosqlite:///./data/hot_state.db
DB_COLD_URL=sqlite+aiosqlite:///./data/cold_state.db

ADK_ENABLED=true
A2A_ENABLED=true
A2A_PEER_URL=http://127.0.0.1:8000

LOOKER_ENABLED=true
LOOKERSDK_BASE_URL=https://your.cloud.looker.com
LOOKERSDK_CLIENT_ID=...
LOOKERSDK_CLIENT_SECRET=...

BQML_ENABLED=true
BQML_PROJECT=my-gcp-project
BQML_LOCATION=US
BQML_DATASET=sites
BQML_MODEL=site_score
```

## Add a backend

1. Row under `factories.capabilities` in `catalogs/catalog.yaml` (`implemented` \| `planned`).
2. `factories/<capability>/<backend>/client.py` (+ `connector.yaml`).
3. Branch in `factories/<capability>/factory.py`.
4. `66degrees-factory list-factories` and the init wizard pick it up.

Do not implement planned backends as silent in-memory fakes.

## ADK / A2A smoke

```bash
# ADK
export ADK_ENABLED=true
export GOOGLE_API_KEY=...
uv run python examples/adk_smoke.py

# A2A (server already mounted when A2A_ENABLED=true)
export A2A_ENABLED=true
export A2A_PEER_URL=http://127.0.0.1:8000
uv run python examples/a2a_client_smoke.py

# Looker
export LOOKER_ENABLED=true
uv sync --extra looker
uv run python examples/looker_smoke.py

# BQML
export BQML_ENABLED=true
uv sync --extra bqml
uv run python examples/bqml_smoke.py
```
