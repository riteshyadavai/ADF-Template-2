# Agentic AI template

```text
config/       YAML + settings
app/          FastAPI
agents/       agent run loop, registry, prompts
shared/       logger, errors, schemas used everywhere
factories/    vendor backends
data/
examples/
tests/
```

| Folder | What it is |
|--------|------------|
| `app/` | HTTP server (`app/main.py`) and `Platform` |
| `agents/` | How agents are defined and run |
| `shared/` | Logger, errors, common schemas |
| `factories/` | Redis, LiteLLM, ADK, A2A, DeepEval, … |
| `config/` | YAML + pydantic settings |

```bash
uv sync --all-groups
cp .env.example .env
make dev
```
