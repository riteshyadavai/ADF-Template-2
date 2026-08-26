"""Eval factory — local heuristic or DeepEval."""

from __future__ import annotations

from config.settings import Settings, get_settings
from factories.eval.local.client import LocalEvalClient
from factories.eval.protocol import EvalClient


def make_eval_client(settings: Settings | None = None) -> EvalClient:
    settings = settings or get_settings()
    backend = settings.eval.backend
    threshold = settings.eval.threshold
    if backend == "local":
        return LocalEvalClient(threshold=threshold)
    if backend == "deepeval":
        from factories.eval.deepeval.client import DeepEvalClient

        return DeepEvalClient(threshold=threshold, model=settings.eval.model)
    raise ValueError(f"Unsupported eval backend: {backend}")
