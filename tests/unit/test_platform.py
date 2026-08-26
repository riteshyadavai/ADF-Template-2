"""Platform composition tests."""

from app.platform import Platform


def test_platform_wires_orchestrator_and_factories():
    platform = Platform()
    assert platform.orchestrator is not None
    assert platform.factories.ai_gateway() is not None
    assert platform.agents.list_agents() == []
