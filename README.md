# ADF Template

Reusable template for multi-agent apps. Clone it, set env vars, swap backends via factories, and add your own agents.

**Requires:** Python 3.11+, [uv](https://docs.astral.sh/uv/)

## Quick start

```bash
git clone https://github.com/riteshyadavai/ADF-Template-2.git
cd ADF-Template-2
uv sync --all-groups
cp .env.example .env          # set GOOGLE_API_KEY (or another LLM key)
make dev                      # http://localhost:8000/api/v1/docs
```

Optional backends:

```bash
uv sync --extra aws           # Bedrock LLM / guardrails
uv sync --extra documents     # Docling PDF parsing
uv sync --extra opensearch    # OpenSearch vector store
uv sync --group observability # Langfuse + Logfire
uv sync --group eval          # DeepEval
```

Scripts without HTTP:

```bash
uv run python examples/single_agent.py
uv run python examples/multi_agent.py
```

## Layout

```text
config/       YAML + pydantic settings (env overlays)
app/          FastAPI (`main.py`, `routes/`, `platform.py`)
agents/       run loop, manifests, prompts, memory, MCP allow-lists
shared/       logger, errors, schemas, metrics (used by everyone)
factories/    vendor backends — swap without changing agents
tests/        unit, contract, integration
evals/        regression / ADK eval sets
examples/     small scripts
```

| Folder | Change it when |
|--------|----------------|
| `app/` | HTTP routes or startup wiring |
| `agents/` | How an agent plans and runs |
| `factories/` | Redis vs memory, LiteLLM vs Bedrock, DeepEval, ADK, A2A |
| `shared/` | Logging, errors, common request types |
| `config/` | Defaults and environment YAML |

`Platform` (`app/platform.py`) is the composition root: it builds the orchestrator and `FactoryRegistry`.

## HTTP API

Base path: `/api/v1`

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness |
| GET | `/ready` | Readiness |
| POST | `/agents/run` | Run the orchestrator |
| POST | `/agents/run/stream` | Stream a run |
| POST | `/agents/runs/{id}/resume` | Resume after HITL |
| GET | `/costs/{tenant_id}` | Spend for a tenant |

Headers: `X-Tenant-ID` (default `default`), optional `Idempotency-Key`. Local env skips auth.

```bash
curl -s -X POST http://localhost:8000/api/v1/agents/run \
  -H 'Content-Type: application/json' \
  -d '{"query":"Say hello in one sentence."}'
```

## Factories

Each factory is `protocol.py` + backend `client.py` + `make_*()` in `factory.py`. Wired in `factories/registry.py`.

```python
from factories.registry import get_factory_registry

reg = get_factory_registry()
cache = reg.cache()              # memory | redis
gateway = reg.ai_gateway()       # LiteLLM (+ budget, redaction)
eval_client = reg.eval()         # local | deepeval
```

| Factory | Backends | Env |
|---------|----------|-----|
| AI Gateway | LiteLLM | `GATEWAY_PROVIDER`, `GATEWAY_DEFAULT_MODEL` |
| Cache | memory, Redis | `CACHE_BACKEND` |
| LLM | LiteLLM, Bedrock, Ollama | `GATEWAY_PROVIDER` |
| Vector store | memory, OpenSearch, Qdrant | `VECTOR_BACKEND` |
| Guardrails | passthrough, Bedrock | `SECURITY_CONTENT_GUARDRAIL_BACKEND` |
| Parsers | Docling | `PDF_BACKEND` |
| Eval | local, DeepEval | `EVAL_BACKEND` |
| Observability | Langfuse, Logfire | `LANGFUSE_*`, `LOGFIRE_*` |
| ADK | in-memory runner | `ADK_ENABLED` |
| A2A | JSON-RPC / REST | `A2A_ENABLED` |

## Add an agent

1. Write a `manifest.yaml` (name, semver, `allowed_tools`, `prompt_version`).
2. Register it: `platform.agents.register_from_manifest(path)`.
3. Put instructions under `agents/prompts/versions/` as `{name}_{version}.md`.

Contract tests live in `tests/contract/`. Fixture example: `tests/fixtures/agents/example_research.yaml`.

## Config

Copy `.env.example` → `.env`. Overlays: `config/environments/{local,production}.yaml`.

Minimum for Gemini via LiteLLM: `GOOGLE_API_KEY`.

## Tests

```bash
make test          # unit (skips integration)
make contract      # manifests + MCP
make integration   # FastAPI health
uv run ruff check app agents shared factories config tests
```

## Docs

- [Layers](docs/architecture/layers.md)
- [Factories](docs/architecture/factories.md)
- [Agent contracts](docs/agents/capability-contracts.md)
- [Security](docs/security/guardrails.md)
