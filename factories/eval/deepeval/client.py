"""DeepEval adapter — LLM-as-judge metrics."""

from __future__ import annotations

import asyncio
from typing import Any

from factories.eval.protocol import EvalCase, EvalClient, MetricScore


class DeepEvalClient(EvalClient):
    def __init__(self, threshold: float = 0.8, model: str | None = None) -> None:
        self._threshold = threshold
        self._model = model

    @property
    def backend(self) -> str:
        return "deepeval"

    async def evaluate_case(self, case: EvalCase) -> list[MetricScore]:
        try:
            from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
            from deepeval.test_case import LLMTestCase
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "DeepEval is not installed. Run: uv sync --group eval"
            ) from exc

        test_case = LLMTestCase(
            input=case.input,
            actual_output=case.actual_output,
            expected_output=case.expected_output,
            retrieval_context=case.retrieval_context or None,
        )
        results: list[MetricScore] = []
        for name in case.metrics or ["answer_relevancy"]:
            metric = self._build_metric(name, AnswerRelevancyMetric, FaithfulnessMetric)
            await asyncio.to_thread(metric.measure, test_case)
            score = float(metric.score or 0.0)
            results.append(
                MetricScore(
                    name=name,
                    score=score,
                    passed=bool(metric.is_successful()),
                    reason=getattr(metric, "reason", "") or "",
                )
            )
        return results

    def _build_metric(self, name: str, answer_relevancy_cls: type, faithfulness_cls: type) -> Any:
        kwargs: dict[str, Any] = {"threshold": self._threshold}
        if self._model:
            kwargs["model"] = self._model
        if name == "faithfulness":
            return faithfulness_cls(**kwargs)
        if name in ("answer_relevancy", "relevancy"):
            return answer_relevancy_cls(**kwargs)
        raise ValueError(f"Unsupported DeepEval metric: {name}")
