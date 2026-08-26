# Run Record Schema

The `RunRecord` in `app/observability/run_record.py` is the first-class planning/execution trace.

## Fields

- `run_id`, `correlation_id`, `trace_id`, `tenant_id`
- `git_sha`, `prompt_version`, `model_version`
- `steps[]` — typed steps (plan, sub_agent, tool, mcp, llm, hitl, eval)
- `total_cost_usd`, `total_tokens`, `eval_score`

## Replay

Any run can be replayed step-by-step from the RunRecord without reconstructing from unstructured logs.

## Tool Integration

Emit the same schema to Langfuse generations, Logfire spans, and Prometheus counters — swap backends via config.
