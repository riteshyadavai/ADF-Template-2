# Run the generated app

Minimum for Gemini via LiteLLM: `GOOGLE_API_KEY` in `.env`. Local overlay skips auth.

## HTTP API

```bash
cd ~/Desktop/demo-afi   # or this template repo
uv sync
# edit .env — minimum: GOOGLE_API_KEY for Gemini via LiteLLM
make dev
```

Docs: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/health` | Liveness |
| GET | `/api/v1/ready` | Readiness |
| POST | `/api/v1/agents/run` | Run orchestrator |
| POST | `/api/v1/agents/run/stream` | Stream a run |
| POST | `/api/v1/agents/runs/{id}/resume` | Resume after HITL |
| GET | `/api/v1/costs/{tenant_id}` | Tenant spend |

Headers: `X-Tenant-ID` (default `default`), optional `Idempotency-Key`. Local overlay skips auth.

```bash
curl -s -X POST http://localhost:8000/api/v1/agents/run \
  -H 'Content-Type: application/json' \
  -d '{"query":"Say hello in one sentence."}'
```

## Other make targets

```bash
make install        # uv sync --all-groups
make test           # unit (skips integration)
make contract
make integration
make lint
make openapi        # writes dist/openapi.json
make run            # 66degrees-factory / factory serve
make docs           # MkDocs at http://127.0.0.1:8001
make docs-deploy    # publish site to Cloud Run (adf-factory-docs)
```

## Scripts without HTTP

```bash
uv run python examples/single_agent.py
uv run python examples/multi_agent.py
uv run python examples/adk_smoke.py
uv run python examples/a2a_client_smoke.py
```

## Tests

```bash
uv run pytest tests -m "not integration"
uv run pytest tests/integration -v
uv run ruff check app agents shared factories config tests examples cli
```
