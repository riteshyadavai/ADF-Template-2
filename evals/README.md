# Evals

Agent evaluations built on ADK's evaluation framework. Add a folder per agent or project; thresholds live in a `test_config.json` next to each eval set.

```
evals/
  test_agents.py            # pytest entry point
  <your_agent>/
    basic.evalset.json      # eval cases (user turn + expected response + tool trajectory)
    test_config.json        # pass/fail criteria for this folder
```

## What an eval set contains

Each case in `*.evalset.json` records a conversation turn with:

- `user_content` — the prompt sent to the agent.
- `final_response` — the reference answer (scored by `response_match_score`).
- `intermediate_data.tool_uses` — the expected tool calls, in order (scored by
  `tool_trajectory_avg_score`).

## Criteria (`test_config.json`)

| Metric | Meaning |
|--------|---------|
| `tool_trajectory_avg_score` | How closely the agent's tool calls match the expected trajectory (1.0 = exact). |
| `response_match_score` | ROUGE-style similarity between the agent's answer and the reference. |

## Run

```bash
uv run pytest evals/                     # all evals
uv run pytest evals/ -k my_agent         # one specialist
```

Requires a valid `GOOGLE_API_KEY` (the eval actually runs the agent). Add the test deps once with:

```bash
uv add --dev pytest pytest-asyncio
```

## Add evals for a new sub-agent

1. Create `evals/<name>/` with a `*.evalset.json` and a `test_config.json`.
2. Add a test in `test_agents.py` pointing `AgentEvaluator.evaluate` at it
   (use `agent_name="<sub_agent_name>"` to target a specific specialist).

## DeepEval factory

For LLM-as-judge scoring from app code:

```python
from factories.eval.protocol import EvalCase
from app.platform import get_platform

scores = await get_platform().evaluation().evaluate_case(
    EvalCase(input="...", actual_output="...", expected_output="...")
)
```

`EVAL_BACKEND=local` (default, no extra deps) or `deepeval` after `uv sync --group eval`.
