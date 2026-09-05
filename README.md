# 66degrees Factory

Package **`multi-agent-factory` 0.2.9**. Console command **`66degrees-factory`** (alias **`factory`**).

This repo is the **generator** and the default runtime template. `init` writes a **developer agent app** (one domain + one workflow). It does **not** copy `catalogs/` or `cli/` into that app.

**Requires:** Python 3.11+, [uv](https://docs.astral.sh/uv/)

**Docs:** [https://adf-factory-docs-741027775203.us-central1.run.app](https://adf-factory-docs-741027775203.us-central1.run.app)

---

## Install the CLI

`uvx` runs once and does **not** put `66degrees-factory` on `PATH`. For a lasting command:

```bash
export PATH="$HOME/.local/bin:$PATH"   # keep this in ~/.zshrc
```

### From this checkout

```bash
cd /Users/ritesh/Desktop/multi-agent-factory
uv sync
uv tool install --editable .
66degrees-factory --help
```

### From Artifact Registry (hosted package)

Private index. `uv` does not use `gcloud` unless you pass a token. Use **`--extra-index-url`** (not `--index-url`, which hides PyPI).

```bash
gcloud auth login
export TOKEN=$(gcloud auth print-access-token)
export AR_SIMPLE="https://oauth2accesstoken:${TOKEN}@us-central1-python.pkg.dev/ai-ml-team-sandbox/adf-factory-pypi/simple/"

uv tool install multi-agent-factory --reinstall --extra-index-url "$AR_SIMPLE"
66degrees-factory --help
```

One-shot (no global command):

```bash
uvx --extra-index-url "$AR_SIMPLE" --from multi-agent-factory 66degrees-factory --help
```

Needs `roles/artifactregistry.reader` on repo `adf-factory-pypi` in project `ai-ml-team-sandbox`.

---

## Generate a project

From an empty folder, init writes **here**. Do not init into this template repo.

```bash
mkdir ~/Desktop/demo-afi && cd ~/Desktop/demo-afi
66degrees-factory init
```

Non-interactive:

```bash
66degrees-factory init \
  --name demo-afi \
  --output ~/Desktop/demo-afi \
  --domain bfs \
  --workflow afi \
  --yes
```

```bash
66degrees-factory list-domains
66degrees-factory list-workflows --domain bfs
66degrees-factory list-factories
66degrees-factory init --name demo --domain retail --workflow accr --yes --dry-run
```

| Domain | Workflows |
|--------|-----------|
| `bfs` | `afi`, `clu`, `rca` |
| `hcls` | `epa`, `ctpm`, `addw` |
| `retail` | `accr`, `dcap`, `avmts` |
| `other` | name your own domain + workflow |

Interactive `init` previews the catalog plan (agents + graph). Accept it, or customize agents/HITL and then configure backends.

### What `init` writes

| In the app | Purpose |
|------------|---------|
| `app/`, `agents/`, `factories/`, `config/`, `shared/` | Runtime |
| `domains/<domain>/workflows/<workflow>/` | That workflow only |
| `.env` | Secrets |
| `config/app.yaml` | Domain, workflow, backends |
| `factory-choices.json` | Wizard record (`--from-choices`) |

**Not copied:** `catalogs/`, `cli/`, site-packages (`aiohttp`, `*.dist-info`). Unused factory **backends** stay under `factories/` so env can switch later.

Then:

```bash
cd ~/Desktop/demo-afi
uv sync
# set GOOGLE_API_KEY and other CHANGE_ME keys in .env
make dev    # http://localhost:8000/api/v1/docs
```

---

## Run this repo as the template (no generate)

```bash
git clone https://github.com/riteshyadavai/ADF-Template-2.git
cd ADF-Template-2
uv sync --all-groups
cp .env.example .env
make dev
```

```bash
uv run 66degrees-factory serve
```

Optional extras:

```bash
uv sync --extra aws
uv sync --extra documents
uv sync --extra opensearch
uv sync --extra qdrant
uv sync --extra cache-memcached
uv sync --extra looker
uv sync --extra bqml
uv sync --extra asset-factory
uv sync --group observability
uv sync --group eval
```

```bash
uv run python examples/single_agent.py
uv run python examples/multi_agent.py
```

---

## This repo vs a generated app

| | Factory repo (this tree) | Generated project |
|--|--------------------------|-------------------|
| `cli/`, `catalogs/` | Yes — generator | No |
| `domains/` | Empty until you init elsewhere | One domain + one workflow |
| Console scripts | `66degrees-factory`, `factory` | None (use `make dev`) |

`Platform` loads `domains/…` when `config/app.yaml` has `project.domain` and `project.workflow`. This checkout without that block uses the default `respond` graph.

---

## Layout (factory repo)

```text
cli/          init, list-*, serve
catalogs/     catalog.yaml (domains, workflows, factory backends) for the wizard
config/       YAML + pydantic settings
app/          FastAPI
agents/       run loop, manifests, prompts
shared/       logging, errors, schemas
factories/    vendor backends (env-selected)
tests/        unit, contract, integration
evals/        eval sets
examples/     scripts
docs/         MkDocs source
```

| Folder | Change it when |
|--------|----------------|
| `catalogs/` | New domain or workflow for `init` |
| `factories/` | New backend |
| `app/` | HTTP / startup |
| `agents/` | How a run plans and executes |
| `config/` | Defaults and env overlays |

---

## HTTP API

Base: `/api/v1`. Local overlay skips auth. Header `X-Tenant-ID` (default `default`).

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness |
| GET | `/ready` | Readiness |
| POST | `/agents/run` | Run orchestrator |
| POST | `/agents/run/stream` | Stream |
| POST | `/agents/runs/{id}/resume` | Resume HITL |
| GET | `/costs/{tenant_id}` | Tenant spend |

```bash
curl -s -X POST http://localhost:8000/api/v1/agents/run \
  -H 'Content-Type: application/json' \
  -d '{"query":"Say hello in one sentence."}'
```

---

## Factories

Runtime selection is `config/app.yaml` then env (env wins). `init` writes both.

```python
from factories.registry import get_factory_registry

reg = get_factory_registry()
cache = reg.cache()
gateway = reg.ai_gateway()
```

| Capability | Implemented | Env |
|------------|-------------|-----|
| Gateway | litellm, openai, bedrock, ollama | `GATEWAY_PROVIDER` |
| Cache | memory, redis, memcached | `CACHE_BACKEND` |
| Vector | memory, opensearch, qdrant | `VECTOR_BACKEND` |
| Embeddings | litellm, jina | `EMBEDDINGS_BACKEND` |
| Parser | docling | `PDF_BACKEND` |
| Guardrails | passthrough, bedrock | `SECURITY_CONTENT_GUARDRAIL_BACKEND` |
| Eval | local, deepeval | `EVAL_BACKEND` |
| State | memory, sqlite | `DB_BACKEND` |
| Observability | Langfuse, Logfire | `LANGFUSE_*`, `LOGFIRE_*` |
| ADK / A2A | in-memory / SDK mount | `ADK_ENABLED`, `A2A_ENABLED` |

Kong, pgvector, weaviate, vault, sops are planned (`NotImplementedError`).

---

## Config and tests

Copy `.env.example` → `.env` in this repo. Generated apps already have `.env`. Minimum for Gemini via LiteLLM: `GOOGLE_API_KEY`.

```bash
make test
make contract
make integration
uv run ruff check app agents shared factories config tests examples cli
```

---

## Docs

```bash
make docs          # http://127.0.0.1:8001
make docs-deploy   # Cloud Run adf-factory-docs (ai-ml-team-sandbox only)
```

- [Install](docs/guide/install.md)
- [CLI](docs/guide/cli.md)
- [Init](docs/guide/init.md)
- [Factories](docs/guide/factories.md)
- [Run](docs/guide/run.md)
- [Publish the package](docs/guide/publish-gcp.md)

New CLI versions update **new** `init` snapshots (`template.version` in `config/app.yaml`). Existing apps keep the factories they were generated with. Pin `multi-agent-factory==0.2.9` in a team runbook.
