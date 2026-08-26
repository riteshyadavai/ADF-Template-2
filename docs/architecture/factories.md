# Factories

All vendor backends stay under `factories/`.

```python
from factories.registry import get_factory_registry

reg = get_factory_registry()
cache = reg.cache()
gateway = reg.ai_gateway()
eval_client = reg.eval()  # local | deepeval
```

DeepEval (optional): `uv sync --group eval` then `EVAL_BACKEND=deepeval`.

Wire agents through `app.platform.Platform`, not by constructing SDKs in `agents/`.
