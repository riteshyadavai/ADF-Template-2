"""Contract tests for agent manifest validation."""

from pathlib import Path

import pytest

from agents.contracts import AgentCapabilityContract
from agents.registry import AgentRegistry
from shared.errors import AgentContractError

MANIFEST = Path(__file__).resolve().parents[1] / "fixtures" / "agents" / "example_research.yaml"


def test_example_research_manifest_valid():
    registry = AgentRegistry()
    contract = registry.register_from_manifest(MANIFEST)
    assert contract.name == "example_research"
    assert contract.version == "1.0.0"
    assert "vector_search" in contract.allowed_tools


def test_invalid_manifest_rejected(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("name: broken\nversion: not-semver\n")
    registry = AgentRegistry()
    with pytest.raises(AgentContractError):
        registry.register_from_manifest(bad)


def test_capability_contract_schema():
    contract = AgentCapabilityContract(
        name="test",
        version="1.0.0",
        description="test agent",
        allowed_tools=["tool_a"],
        cost_ceiling_usd=0.10,
    )
    assert contract.timeout_seconds == 120
