"""Evaluation runner — ties evals to git SHA + prompt version + model version."""

from __future__ import annotations

import subprocess
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any


def get_git_sha() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()[:12]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


@dataclass
class EvalContext:
    git_sha: str
    prompt_version: str
    model_version: str
    eval_suite: str


@dataclass
class EvalResult:
    name: str
    score: float
    passed: bool
    context: EvalContext
    metadata: dict[str, Any]


EvalFn = Callable[[], Awaitable[float]]


class EvaluationRunner:
    """Runnable independently of app runtime for CI/CD regression gates."""

    def __init__(self, threshold: float = 0.8) -> None:
        self._threshold = threshold

    def build_context(
        self, eval_suite: str, prompt_version: str, model_version: str
    ) -> EvalContext:
        return EvalContext(
            git_sha=get_git_sha(),
            prompt_version=prompt_version,
            model_version=model_version,
            eval_suite=eval_suite,
        )

    async def run(self, name: str, fn: EvalFn, context: EvalContext) -> EvalResult:
        score = await fn()
        return EvalResult(
            name=name,
            score=score,
            passed=score >= self._threshold,
            context=context,
            metadata={},
        )

    async def run_suite(
        self,
        cases: list[tuple[str, EvalFn]],
        context: EvalContext,
    ) -> list[EvalResult]:
        results = []
        for name, fn in cases:
            results.append(await self.run(name, fn, context))
        return results

    def regression_gate(self, results: list[EvalResult], baseline: dict[str, float]) -> bool:
        for result in results:
            base = baseline.get(result.name)
            if base is not None and result.score < base - 0.05:
                return False
        return all(r.passed for r in results)
