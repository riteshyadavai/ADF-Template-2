"""OpenTelemetry and Prometheus metrics hooks."""

from __future__ import annotations

from prometheus_client import Counter, Histogram

AGENT_RUNS = Counter(
    "factory_agent_runs_total",
    "Total agent runs",
    ["tenant_id", "status"],
)
LLM_REQUESTS = Counter(
    "factory_llm_requests_total",
    "Total LLM requests",
    ["model", "status"],
)
LLM_COST = Counter(
    "factory_llm_cost_usd_total",
    "Total LLM cost in USD",
    ["tenant_id", "model"],
)
MCP_CALLS = Counter(
    "factory_mcp_calls_total",
    "Total MCP tool calls",
    ["server", "tool", "status"],
)
RUN_LATENCY = Histogram(
    "factory_run_latency_seconds",
    "End-to-end run latency",
    ["tenant_id"],
)
GUARDRAIL_BLOCKS = Counter(
    "factory_guardrail_blocks_total",
    "Guardrail policy blocks",
    ["policy"],
)
