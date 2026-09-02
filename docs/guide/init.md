# Init a project

One output directory = **one domain + one workflow**. `bfs/afi` and `bfs/clu` are two `init` runs.

Interactive `init` shows a **predefined plan** (agents + graph). Accept it, or customize agents/HITL and then configure backends.

!!! note "Write set"
    `.env` (secrets), `config/app.yaml` (runtime knobs), `factory-choices.json`, `pyproject.toml` name, `domains/<domain>/workflows/<workflow>/`.

!!! danger "Destructive `--force`"
    `--force` **deletes** a non-empty destination, then recopies. `--dry-run` writes nothing.

## Interactive

From an **empty folder** you already created, init writes **here** (project name = folder name):

```bash
mkdir ~/Desktop/demo-afi && cd ~/Desktop/demo-afi
66degrees-factory init
```

From this factory repo, init refuses `.` and defaults to `~/Desktop/<name>`:

```bash
uv run 66degrees-factory init
```

Or pass `--output` explicitly. Do **not** use this template repo as the destination.

Each workflow has a catalog **platform stack** (LLM / cache / vector). Accept the plan to keep it, or choose **Change stack** (current backends are pre-selected).

## What gets written

Runtime app snapshot (`app/`, `agents/`, `factories/`, `tests/`, `docs/`). **Not copied:** `catalogs/`, `cli/`.

| Path | Purpose |
|------|---------|
| `.env` | Secrets (`CHANGE_ME`) |
| `config/app.yaml` | Chosen workflow snapshot (agents, prompts, MCP, evals) plus backends |
| `factory-choices.json` | Replay (`--from-choices`) |
| `domains/<domain>/workflows/<workflow>/` | Manifests, prompts, `graph.yaml` |

`--yes` accepts the catalog plan and `recommended_stack` unless you pass factory flags.

`Platform` loads that workflow when `config/app.yaml` has `project.domain` and `project.workflow`. This checkout without a project block uses the default `respond` graph.

## After generate

```bash
cd ~/Desktop/demo-afi && uv sync && make dev
```
