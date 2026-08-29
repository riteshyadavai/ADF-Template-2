"""Workflow YAML loader tests."""

from pathlib import Path

from agents.workflow_loader import load_workflow_graph


def test_load_workflow_graph(tmp_path: Path):
    path = tmp_path / "graph.yaml"
    path.write_text(
        "entry: intake\n"
        "nodes:\n"
        "  - id: intake\n"
        "    agent_name: kyc_intake\n"
        "    next: [review]\n"
        "  - id: review\n"
        "    requires_hitl: true\n"
        "    next: []\n",
        encoding="utf-8",
    )
    graph = load_workflow_graph(path)
    assert graph.entry_node == "intake"
    assert graph.nodes["intake"].agent_name == "kyc_intake"
    assert graph.nodes["intake"].next_nodes == ["review"]
    assert "review" in graph.hitl_nodes
