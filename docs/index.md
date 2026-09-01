# Getting started

`66degrees-factory` generates **one project** per domain + workflow. The same package is the runtime template.

<div class="grid cards" markdown>

-   :material-download: [Install the CLI](guide/install.md)

    ---

    Checkout, `uv tool`, Artifact Registry, or a local wheel.

-   :material-console: [CLI reference](guide/cli.md)

    ---

    Every subcommand and `init` flag.

-   :material-folder-plus: [Init a project](guide/init.md)

    ---

    What is copied, written, and refused.

-   :material-puzzle: [Factories](guide/factories.md)

    ---

    Env keys, extras, planned backends.

-   :material-play-circle: [Run the app](guide/run.md)

    ---

    HTTP surface, make targets, smoke scripts.

-   :material-cloud: [Publish & host](guide/publish-gcp.md)

    ---

    Artifact Registry package. Cloud Run docs site.

</div>

## Contract

| Rule | Meaning |
|------|---------|
| One `init` | One domain, one workflow, one output directory |
| Full snapshot | Entire template copy. Unused factory folders stay on disk |
| Runtime swap | Backends from `config/app.yaml` then env. `init` writes `app.yaml` + `.env` |
| Index URL | Must end in `/simple/` |
| Ports | Docs local `:8001`. FastAPI `:8000` |

!!! warning "Do not init into the template"
    Output must be a **new** directory (for example `~/Desktop/demo-afi`). `init` refuses the source tree.

## Local preview

```bash
cd /Users/ritesh/Desktop/multi-agent-factory
make docs
```

Open [http://127.0.0.1:8001](http://127.0.0.1:8001).
