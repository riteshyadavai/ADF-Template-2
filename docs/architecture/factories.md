# Factories

All vendor backends stay under `factories/`. Init choices come from `catalogs/catalog.yaml`.

```python
from factories.registry import get_factory_registry

reg = get_factory_registry()
cache = reg.cache()
gateway = reg.ai_gateway()
eval_client = reg.eval()
```

## Add a backend

1. Add a row under `factories.capabilities` in `catalogs/catalog.yaml` (`implemented` | `planned`).
2. Add `factories/<capability>/<backend>/client.py` (and `connector.yaml`).
3. Branch in `factories/<capability>/factory.py`.
4. `66degrees-factory list-factories` and the init wizard pick it up automatically.

DeepEval: `uv sync --group eval` then `EVAL_BACKEND=deepeval`.
Qdrant: `uv sync --extra qdrant`. Memcached: `uv sync --extra cache-memcached`.
Looker: `uv sync --extra looker`. BQML: `uv sync --extra bqml`.

Wire agents through `app.platform.Platform`, not by constructing SDKs in `agents/`.
