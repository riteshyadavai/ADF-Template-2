# Agent Capability Contracts

Each sub-agent declares a manifest (`manifest.yaml`) validated at registration:

```yaml
name: example_research
version: "1.0.0"
description: Research specialist
inputs: [query, session_id]
outputs: [summary, citations]
allowed_tools: [vector_search, web_search]
cost_ceiling_usd: 0.50
timeout_seconds: 60
eval_suite: example_research_v1
prompt_version: "1.0.0"
```

## Semver Independence

Agents are versioned independently: `example_research@1.4.0` can be pinned while the platform stays at `0.1.0`.

## Swappability

The orchestrator depends only on the contract — not implementation details. Replace an agent by updating its manifest and prompt version.

## Contract Tests

Run `make contract` to validate all manifests before merge.
