"""Evaluation regression gate tests."""

import pytest

from shared.evaluator import EvalContext, EvaluationRunner


@pytest.mark.asyncio
async def test_eval_regression_gate():
    runner = EvaluationRunner(threshold=0.7)
    context = EvalContext(
        git_sha="abc123",
        prompt_version="1.0.0",
        model_version="gemini-2.5-flash",
        eval_suite="example",
    )

    async def good_eval() -> float:
        return 0.9

    result = await runner.run("quality", good_eval, context)
    assert result.passed
    assert result.context.git_sha == "abc123"


def test_regression_gate_blocks_score_drop():
    runner = EvaluationRunner()
    from shared.evaluator import EvalResult

    results = [EvalResult("quality", 0.7, True, EvalContext("a", "1", "m", "s"), {})]
    assert runner.regression_gate(results, {"quality": 0.8}) is False
