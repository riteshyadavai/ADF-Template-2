"""Agent evaluations, run with pytest.

    uv run pytest evals/

Add a test per eval set that points AgentEvaluator at an evalset JSON.
Pass/fail thresholds come from the `test_config.json` sitting next to that evalset.

Example:

    from pathlib import Path
    import pytest
    from google.adk.evaluation.agent_evaluator import AgentEvaluator

    EVAL_DIR = Path(__file__).parent

    @pytest.mark.asyncio
    async def test_my_agent_basic():
        await AgentEvaluator.evaluate(
            agent_module="agents.base_agent",
            eval_dataset_file_path_or_dir=str(EVAL_DIR / "my_agent" / "basic.evalset.json"),
        )
"""
