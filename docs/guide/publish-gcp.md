# Publish to GCP Artifact Registry

The **CLI package** lives in Artifact Registry. This documentation site is a different Cloud Run service — see [Host this site](host-docs.md).

**Already created (do not recreate unless missing):**

| Item | Value |
|------|--------|
| Project | `ai-ml-team-sandbox` |
| Repository | `adf-factory-pypi` |
| Format | Python |
| Location | `us-central1` |
| Package | `multi-agent-factory` |
| Version | `0.2.7` |
| Upload URL | `https://us-central1-python.pkg.dev/ai-ml-team-sandbox/adf-factory-pypi/` |
| Install index | `https://us-central1-python.pkg.dev/ai-ml-team-sandbox/adf-factory-pypi/simple/` |

Twine upload URL has **no** `/simple/`. pip/uv install URL **must** end with `/simple/`.

## Create a repo (only if you need a new one)

Names must start with a **letter** (`66degrees-…` is invalid).

```bash
gcloud artifacts repositories create adf-factory-pypi \
  --project=ai-ml-team-sandbox \
  --repository-format=python \
  --location=us-central1 \
  --description="Python packages for 66degrees-factory CLI"
```

Do not delete or modify existing Docker repositories in that project.

## Auth

```bash
gcloud auth login
gcloud auth application-default login   # optional; used by some keyring flows
```

Upload can use the **gcloud user** if ADC is stale.

## Build and upload a new version

Prefer **wheel only** (`uv build` sdist may fail on empty `data/` force-include):

```bash
cd /Users/ritesh/Desktop/multi-agent-factory
# bump version in pyproject.toml first if this is a new release
uv build --wheel

uvx --with keyrings.google-artifactregistry-auth --with twine \
  twine upload --non-interactive \
  --repository-url https://us-central1-python.pkg.dev/ai-ml-team-sandbox/adf-factory-pypi/ \
  dist/multi_agent_factory-0.2.7-py3-none-any.whl
```

Verify:

```bash
gcloud artifacts packages list \
  --project=ai-ml-team-sandbox \
  --location=us-central1 \
  --repository=adf-factory-pypi
```

## Install from the registry

`--index-url` replaces PyPI and returns 401 unless you embed credentials. Use `--extra-index-url` and a gcloud user token.

```bash
gcloud auth login
export TOKEN=$(gcloud auth print-access-token)
export AR_SIMPLE="https://oauth2accesstoken:${TOKEN}@us-central1-python.pkg.dev/ai-ml-team-sandbox/adf-factory-pypi/simple/"

uv tool install multi-agent-factory --extra-index-url "$AR_SIMPLE"
66degrees-factory init --output ~/Desktop/demo-afi
```

```bash
uvx --extra-index-url "$AR_SIMPLE" \
  --from multi-agent-factory \
  66degrees-factory init --output ~/Desktop/demo-afi
```

IAM (only if a teammate cannot install): grant `roles/artifactregistry.reader` on `adf-factory-pypi`. Publishers need `roles/artifactregistry.writer`.

## Local private index (optional)

No GCP:

```bash
mkdir -p ~/pypi-packages
uv tool install pypiserver
pypi-server run -p 8080 ~/pypi-packages
uv publish --publish-url http://127.0.0.1:8080/ --username unused --password unused dist/*
```

## How updates work

Publishing a new version updates the **generator**. Existing generated projects keep the `factories/` copy from init time (`template.version` in `config/app.yaml`). Re-init into a new folder to take a newer snapshot.
