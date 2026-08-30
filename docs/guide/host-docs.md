# Host this documentation

The MkDocs site is a **separate** Cloud Run service. It is not the Python package and it is not the agent API.

| Item | Value |
|------|--------|
| Project | `ai-ml-team-sandbox` |
| Service | `adf-factory-docs` |
| Region | `us-central1` |
| Image source | `deploy/docs` (nginx + `site/`) |
| Local preview | `make docs` → `:8001` |

!!! warning "Scope"
    Deploy **only** `adf-factory-docs`. Do not change the gcloud default project (`pin-bp-dev`), and do not delete or edit other Cloud Run services or Artifact Registry repos.

## Rebuild and deploy

Always pass `--project`. Never `gcloud config set project`.

```bash
cd /Users/ritesh/Desktop/multi-agent-factory
make docs-deploy
```

That runs `mkdocs build`, copies `site/` into `deploy/docs/site`, then:

```bash
gcloud run deploy adf-factory-docs \
  --project=ai-ml-team-sandbox \
  --region=us-central1 \
  --source deploy/docs \
  --allow-unauthenticated \
  --port=8080
```

Cloud Build may create or reuse a source-deploy image repo. Leave existing Docker repositories untouched.

## After deploy

`gcloud run services describe adf-factory-docs --project=ai-ml-team-sandbox --region=us-central1 --format='value(status.url)'`
