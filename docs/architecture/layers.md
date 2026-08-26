# Layout

```text
app/           FastAPI (`main.py`, `routes/`, `platform.py`)
agents/        base agent, registry, prompts, memory
shared/        logger, errors, schemas, metrics
factories/     vendor backends
config/        YAML + settings
```

- **app** — HTTP only
- **shared** — code used by app, agents, and factories
- **factories** — keep this tree; swap backends here
