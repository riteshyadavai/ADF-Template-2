# Install the CLI

Requires **Python 3.11+** and [uv](https://docs.astral.sh/uv/). Entry points: `66degrees-factory` and `factory` (same Typer app).

!!! tip "You do not activate uv"
    `uv` is a binary. Activate the **project venv** with `source .venv/bin/activate`, or skip activation and use `uv run …`.

## Choose a path

<div class="grid cards" markdown>

-   :material-source-repository: __Checkout__

    This repo’s `.venv` via `uv run`.

-   :material-toolbox: __Global tool__

    Editable install on `~/.local/bin`.

-   :material-cloud-download: __Artifact Registry__

    Shared `multi-agent-factory` wheel.

-   :material-package-variant: __Local wheel__

    `uv build --wheel` then `uv tool install`.

</div>

=== "Checkout"

    `uv run` uses this repo’s `.venv`. `cd` first, or pass `--directory`.

    ```bash
    cd /Users/ritesh/Desktop/multi-agent-factory
    uv sync --all-groups
    uv run 66degrees-factory --help
    ```

    ```bash
    uv run --directory /Users/ritesh/Desktop/multi-agent-factory 66degrees-factory --help
    ```

=== "Global tool"

    Puts `66degrees-factory` on `~/.local/bin`. Re-run after large pulls.

    ```bash
    cd /Users/ritesh/Desktop/multi-agent-factory
    uv sync
    uv tool install --editable .
    export PATH="$HOME/.local/bin:$PATH"
    66degrees-factory --help
    ```

=== "Artifact Registry"

    Package already published: project `ai-ml-team-sandbox`, repo `adf-factory-pypi`.

    Needs `gcloud auth login` **and** `roles/artifactregistry.reader` on that repo.

    `uv` does **not** send gcloud credentials by itself. A bare `--index-url` also **replaces PyPI**, so runtime deps (`a2a-sdk`, …) cannot resolve. Use `--extra-index-url` plus a user access token.

    ```bash
    gcloud auth login

    export TOKEN=$(gcloud auth print-access-token)
    export AR_SIMPLE="https://oauth2accesstoken:${TOKEN}@us-central1-python.pkg.dev/ai-ml-team-sandbox/adf-factory-pypi/simple/"

    uv tool install multi-agent-factory --extra-index-url "$AR_SIMPLE"
    66degrees-factory --help
    ```

    One-shot:

    ```bash
    gcloud auth login
    export TOKEN=$(gcloud auth print-access-token)

    uvx --extra-index-url "https://oauth2accesstoken:${TOKEN}@us-central1-python.pkg.dev/ai-ml-team-sandbox/adf-factory-pypi/simple/" \
      --from multi-agent-factory \
      66degrees-factory --help
    ```

    `401 Unauthorized` = no token / expired login. `was not found` after auth with `--index-url` = PyPI was disabled; switch to `--extra-index-url`.

=== "Local wheel"

    ```bash
    cd /Users/ritesh/Desktop/multi-agent-factory
    uv build --wheel
    uv tool install dist/multi_agent_factory-0.2.2-py3-none-any.whl
    ```

## Command not found

```bash
export PATH="$HOME/.local/bin:/opt/homebrew/bin:$PATH"
which uv
which 66degrees-factory
```
