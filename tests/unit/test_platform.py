"""Platform composition tests."""

from pathlib import Path

from app.platform import Platform


def test_platform_wires_orchestrator_and_factories():
    platform = Platform()
    assert platform.orchestrator is not None
    assert platform.factories.ai_gateway() is not None
    assert platform.agents.list_agents() == []


def test_platform_loads_project_workflow(tmp_path: Path):
    wf = tmp_path / "domains" / "bfs" / "workflows" / "afi"
    (wf / "agents").mkdir(parents=True)
    (wf / "prompts").mkdir()
    (wf / "graph.yaml").write_text(
        "entry: intake\nnodes:\n  - id: intake\n    agent_name: afi_intake\n    next: []\n",
        encoding="utf-8",
    )
    (wf / "agents" / "afi_intake.yaml").write_text(
        "name: afi_intake\n"
        "version: 1.0.0\n"
        "description: test\n"
        "allowed_tools: []\n"
        "prompt_version: 1.0.0\n",
        encoding="utf-8",
    )
    (wf / "prompts" / "afi_intake_1.0.0.md").write_text("You are AFI intake.\n", encoding="utf-8")
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "app.yaml").write_text(
        "project:\n  domain: bfs\n  workflow: afi\n",
        encoding="utf-8",
    )
    platform = Platform(project_root=tmp_path)
    assert platform.agents.list_agents() == ["afi_intake"]
    assert platform.orchestrator._workflow.entry_node == "intake"
    assert "You are AFI intake" in platform.prompts.load("afi_intake", "1.0.0")
