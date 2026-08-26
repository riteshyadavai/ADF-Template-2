"""Agent registry — validates manifests, enforces contracts, versioned registration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import semver
import yaml
from pydantic import ValidationError

from agents.contracts import AgentCapabilityContract
from agents.mcp.registry import MCPRegistry
from shared.errors import AgentContractError, AgentNotFoundError
from shared.logger import get_logger

log = get_logger(__name__)


class AgentRegistry:
    def __init__(self, mcp_registry: MCPRegistry | None = None) -> None:
        self._agents: dict[str, dict[str, Any]] = {}
        self._contracts: dict[str, AgentCapabilityContract] = {}
        self._mcp = mcp_registry or MCPRegistry()

    def register_from_manifest(self, manifest_path: Path) -> AgentCapabilityContract:
        with manifest_path.open(encoding="utf-8") as fh:
            raw = yaml.safe_load(fh)
        try:
            contract = AgentCapabilityContract.model_validate(raw)
        except ValidationError as exc:
            raise AgentContractError(f"Invalid manifest {manifest_path}: {exc}") from exc

        if not semver.Version.is_valid(contract.version):
            raise AgentContractError(f"Invalid semver: {contract.version}")

        key = f"{contract.name}@{contract.version}"
        self._contracts[key] = contract
        self._agents[contract.name] = {"latest": contract, "versions": {contract.version: contract}}
        self._mcp.grant_tools(contract.name, contract.allowed_tools)
        log.info("agent_registered", agent=contract.name, version=contract.version)
        return contract

    def get(self, name: str, version: str | None = None) -> AgentCapabilityContract:
        if name not in self._agents:
            raise AgentNotFoundError(f"Agent '{name}' not registered")
        if version:
            versions = self._agents[name]["versions"]
            if version not in versions:
                raise AgentNotFoundError(f"Agent '{name}@{version}' not found")
            return versions[version]
        return self._agents[name]["latest"]

    def list_agents(self) -> list[str]:
        return sorted(self._agents.keys())
