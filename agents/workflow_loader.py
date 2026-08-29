"""Load WorkflowGraph from YAML written by the project factory."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from agents.base_agent import WorkflowGraph, WorkflowNode


def load_workflow_graph(path: Path) -> WorkflowGraph:
    with path.open(encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    return workflow_graph_from_dict(raw)


def workflow_graph_from_dict(raw: dict[str, Any]) -> WorkflowGraph:
    entry = raw.get("entry") or raw.get("entry_node")
    if not entry:
        raise ValueError("Workflow graph requires 'entry' (or entry_node)")

    nodes: dict[str, WorkflowNode] = {}
    hitl_nodes: set[str] = set()
    for item in raw.get("nodes") or []:
        node_id = item["id"]
        nxt = item.get("next") or item.get("next_nodes") or []
        if isinstance(nxt, str):
            nxt = [nxt]
        node = WorkflowNode(
            id=node_id,
            agent_name=item.get("agent_name"),
            requires_hitl=bool(item.get("requires_hitl", False)),
            next_nodes=list(nxt),
        )
        nodes[node_id] = node
        if node.requires_hitl:
            hitl_nodes.add(node_id)

    if entry not in nodes:
        raise ValueError(f"Workflow entry '{entry}' is not in nodes")

    return WorkflowGraph(entry_node=entry, nodes=nodes, hitl_nodes=hitl_nodes)
