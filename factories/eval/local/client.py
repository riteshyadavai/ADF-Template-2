"""Local eval backend — no DeepEval / no LLM judge."""

from __future__ import annotations

from factories.eval.protocol import EvalCase, EvalClient, MetricScore


class LocalEvalClient(EvalClient):
    def __init__(self, threshold: float = 0.8) -> None:
        self._threshold = threshold

    @property
    def backend(self) -> str:
        return "local"

    async def evaluate_case(self, case: EvalCase) -> list[MetricScore]:
        names = case.metrics or ["answer_relevancy"]
        scores: list[MetricScore] = []
        for name in names:
            score = _simple_score(case)
            scores.append(
                MetricScore(
                    name=name,
                    score=score,
                    passed=score >= self._threshold,
                    reason="local heuristic (no LLM judge)",
                )
            )
        return scores


def _simple_score(case: EvalCase) -> float:
    if not case.actual_output.strip():
        return 0.0
    expected = (case.expected_output or "").strip().lower()
    actual = case.actual_output.strip().lower()
    if not expected:
        return 1.0
    if expected in actual or actual in expected:
        return 1.0
    overlap = set(expected.split()) & set(actual.split())
    if not expected.split():
        return 1.0
    return round(len(overlap) / len(set(expected.split())), 4)
