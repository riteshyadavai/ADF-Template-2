# CLI command reference

Same Typer app, two names. No subcommand → help (`no_args_is_help`).

```bash
66degrees-factory --help
factory --help
```

## Command map

<div class="grid cards" markdown>

-   :material-domain: [`list-domains`](#list-domains)

    Catalog domain ids.

-   :material-sitemap: [`list-workflows`](#list-workflows)

    Workflows for one `--domain`.

-   :material-factory: [`list-factories`](#list-factories)

    Capability backends and status.

-   :material-folder-plus: [`init`](#init)

    Generate one domain + one workflow.

-   :material-play: [`serve`](#serve)

    Uvicorn for `app.main:app`.

</div>


## `list-domains`

Print catalog domain ids (`catalogs/domains/*.yaml`).

```bash
66degrees-factory list-domains
```

| Domain | Workflows |
|--------|-----------|
| `banking` | `kyc`, `fraud`, `loan_origination`, `compliance` |
| `healthcare` | `prior_auth`, `claims`, `clinical_summary` |
| `insurance` | `fnol`, `policy_qa` |
| `retail` | `returns`, `catalog_qa` |

---

## `list-workflows`

List workflows for **one** domain.

```bash
66degrees-factory list-workflows --domain banking
```

| Flag | Required | Description |
|------|----------|-------------|
| `--domain` | yes | Catalog domain id |

Prints `workflow_id` and display name. Example for `--domain banking`: `kyc`, `fraud`, `loan_origination`, `compliance`.

---

## `list-factories`

Print capabilities and backends from `catalogs/factories.yaml` (status: `implemented` / `stub` / `planned`).

```bash
66degrees-factory list-factories
66degrees-factory list-factories --capability cache
```

| Flag | Required | Description |
|------|----------|-------------|
| `--capability` | no | Filter: `gateway`, `cache`, `vector`, `embeddings`, `parser`, `guardrails`, `eval`, `state`, `secrets`, `observability`, `adk`, `a2a`, `mcp` |

---

## `init`

Create a **new directory** that is a full copy of this template plus **one** domain and **one** workflow. Factory answers write `.env` and `config/project.yaml`. Unused factory folders are **not** deleted.

### Interactive (cookiecutter-style)

```bash
66degrees-factory init
```

Prompts (arrow keys / Enter):

1. Project name  
2. Output directory (use an empty path such as `/Users/ritesh/Desktop/demo-kyc`)  
3. Package slug  
4. Domain  
5. Workflow (only that domain’s list)  
6. Every factory: gateway, default model, cache (+ URL), vector (+ URL), embeddings, parser, guardrails, eval, Langfuse, Logfire, state, ADK, A2A, MCP examples, secrets, tenant isolation, environment  
7. Summary table → **Create project?**

Follow-up URL prompts appear only for Redis, memcached, OpenSearch, Qdrant, Bedrock, Ollama.

`init` **refuses** to generate into the template source tree. If `config/project.yaml` already exists in the current repo, it warns that `init` creates a **new** folder.

### Non-interactive

`--yes` requires `--name`, `--domain`, and `--workflow`.

```bash
66degrees-factory init \
  --name demo-kyc \
  --output /Users/ritesh/Desktop/demo-kyc \
  --domain banking \
  --workflow kyc \
  --yes
```

### Dry run (no files written)

```bash
66degrees-factory init \
  --name demo \
  --output /Users/ritesh/Desktop/demo \
  --domain retail \
  --workflow returns \
  --yes \
  --dry-run
```

### Replay a previous run

```bash
66degrees-factory init --from-choices /path/to/factory-choices.json --output /Users/ritesh/Desktop/copy
```

Optional `--name` / `--output` override the JSON.

### All `init` flags

| Flag | Default | Meaning |
|------|---------|---------|
| `--name` | (prompt / `my-agent-project`) | Project name; written to `pyproject.toml` |
| `--output` | `./<name>` | Destination directory |
| `--domain` | (prompt) | Catalog domain id |
| `--workflow` | (prompt) | One workflow id in that domain |
| `--gateway` | `litellm` | `litellm` \| `openai` \| `bedrock` \| `ollama` \| `kong` (planned) |
| `--default-model` | `gemini/gemini-2.5-flash` | `GATEWAY_DEFAULT_MODEL` |
| `--cache` | `memory` | `memory` \| `redis` \| `memcached` |
| `--redis-url` | `redis://localhost:6379/0` | `CACHE_REDIS_URL` |
| `--memcached-url` | `memcached://localhost:11211` | `CACHE_MEMCACHED_URL` |
| `--vector` | `memory` | `memory` \| `opensearch` \| `qdrant` \| `pgvector` \| `weaviate` |
| `--opensearch-url` | `http://localhost:9200` | `VECTOR_OPENSEARCH_URL` |
| *(no `--qdrant-url` flag)* | `http://localhost:6333` | Wizard-only; default `VECTOR_QDRANT_URL` in `factory-choices.json` |
| `--embeddings` | `litellm` | `litellm` \| `jina` |
| `--parser` | `docling` | `PDF_BACKEND` |
| `--guardrails` | `passthrough` | `passthrough` \| `bedrock` |
| `--eval` | `local` | `local` \| `deepeval` |
| `--langfuse` / `--no-langfuse` | on | `LANGFUSE_ENABLED` |
| `--logfire` / `--no-logfire` | off | `LOGFIRE_ENABLED` |
| `--adk` / `--no-adk` | off | `ADK_ENABLED` |
| `--a2a` / `--no-a2a` | off | `A2A_ENABLED` |
| `--mcp-examples` / `--no-mcp-examples` | off | writes `mcp.yaml` under the workflow |
| `--secrets-backend` | `env` | `env` \| `vault` \| `aws_secrets_manager` \| `sops` |
| `--environment` | `local` | `local` \| `dev` \| `test` \| `uat` \| `production` |
| `--yes` | off | No prompts; requires name, domain, workflow |
| `--dry-run` | off | Print plan and `.env`; write nothing |
| `--force` | off | Overwrite a non-empty destination |
| `--force-planned` | off | Allow `--yes` with planned backends (Kong, pgvector, …) |
| `--from-choices` | — | Path to `factory-choices.json` |

`--yes` **rejects** planned backends unless `--force-planned`.

---

## `serve`

Start uvicorn (`app.main:app`). Same as the old `factory` launcher.

```bash
66degrees-factory serve
66degrees-factory serve --host 127.0.0.1 --port 8000
```

| Flag | Default | Meaning |
|------|---------|---------|
| `--host` | `0.0.0.0` | Bind address |
| `--port` | `8000` | Port |

Reload follows `Settings.debug` (local overlay often sets `debug: true`).

Equivalent without the CLI:

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
make dev
```
