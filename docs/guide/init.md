# Init a project

One output directory = **one domain + one workflow**. KYC and fraud are two `init` runs.

!!! note "Write set"
    `.env`, `config/project.yaml`, `factory-choices.json`, `pyproject.toml` name, `domains/<domain>/workflows/<workflow>/`. Sibling workflows are not created. Unused factory folders are not deleted.

!!! danger "Destructive `--force`"
    `--force` **deletes** a non-empty destination, then recopies. `--dry-run` writes nothing.

## Interactive on Desktop

```bash
# after uv tool install --editable .  (or uvx from GCP)
export PATH="$HOME/.local/bin:$PATH"
66degrees-factory init --output /Users/ritesh/Desktop/demo-kyc
```

Or from the repo without a global install:

```bash
cd /Users/ritesh/Desktop/multi-agent-factory
uv run 66degrees-factory init --output /Users/ritesh/Desktop/demo-kyc
```

When asked for **output directory**, use the Desktop path (empty / new folder). Do **not** use this template repo as the output.

## What gets written

The destination is the **runtime app** (`app/`, `agents/`, `factories/`, `tests/`, `docs/`, …). The generator stays in the installed CLI: **`catalogs/` and `cli/` are not copied**.

Then init writes:

| Path | Purpose |
|------|---------|
| `.env` | All factory settings; secrets are `CHANGE_ME` |
| `config/project.yaml` | `domain`, `workflow`, `template_package`, `template_version` |
| `factory-choices.json` | Record of wizard answers (optional; `--from-choices` can replay it) |
| `pyproject.toml` | `name` set to `--name` |
| `domains/<domain>/workflows/<workflow>/` | `graph.yaml`, `agents/*.yaml`, `prompts/*.md`, optional `mcp.yaml` |

Sibling workflows are **not** created (e.g. `kyc` only, not `fraud`).

At runtime, `Platform` loads that workflow if `config/project.yaml` exists. This template repo (no `domains/` project file) still uses the default `respond` graph.

## After generate

```bash
cd /Users/ritesh/Desktop/demo-kyc
uv sync
# set GOOGLE_API_KEY and other CHANGE_ME keys in .env
make dev
```

The CLI also prints the exact `uv sync --extra …` / `--group …` lines for what you picked.

## Destination rules

- Non-empty destination → error unless `--force` (deletes the folder, then recopies).
- Output path equal to the template root → refused.
- `--dry-run` never writes.
