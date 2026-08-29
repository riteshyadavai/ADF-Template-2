"""Platform composition tests."""

from pathlib import Path

from app.platform import Platform


def test_platform_wires_orchestrator_and_factories():
    platform = Platform()
    assert platform.orchestrator is not None
    assert platform.factories.ai_gateway() is not None
    assert platform.agents.list_agents() == []


def test_platform_loads_project_workflow(tmp_path: Path):
    wf = tmp_path / "domains" / "banking" / "workflows" / "kyc"
    (wf / "agents").mkdir(parents=True)
    (wf / "prompts").mkdir()
    (wf / "graph.yaml").write_text(
        "entry: intake\nnodes:\n  - id: intake\n    agent_name: kyc_intake\n    next: []\n",
        encoding="utf-8",
    )
    (wf / "agents" / "kyc_intake.yaml").write_text(
        "name: kyc_intake\n"
        "version: 1.0.0\n"
        "description: test\n"
        "allowed_tools: []\n"
        "prompt_version: 1.0.0\n",
        encoding="utf-8",
    )
    (wf / "prompts" / "kyc_intake_1.0.0.md").write_text("You are KYC intake.\n", encoding="utf-8")
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "project.yaml").write_text(
        "domain: banking\nworkflow: kyc\n",
        encoding="utf-8",
    )
    platform = Platform(project_root=tmp_path)
    assert platform.agents.list_agents() == ["kyc_intake"]
    assert platform.orchestrator._workflow.entry_node == "intake"
    assert "You are KYC intake" in platform.prompts.load("kyc_intake", "1.0.0")
