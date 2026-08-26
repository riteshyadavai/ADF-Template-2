"""Versioned prompt registry — prompts as artifacts, not inline strings."""

from __future__ import annotations

from pathlib import Path

from config.settings import PROJECT_ROOT
from shared.logger import get_logger

log = get_logger(__name__)

PROMPTS_DIR = PROJECT_ROOT / "agents" / "prompts" / "versions"


class PromptRegistry:
    def __init__(self, base_dir: Path | None = None) -> None:
        self._base = base_dir or PROMPTS_DIR
        self._base.mkdir(parents=True, exist_ok=True)

    def load(self, agent_name: str, version: str = "latest") -> str:
        if version == "latest":
            versions = sorted(self._base.glob(f"{agent_name}_*.md"))
            if not versions:
                return self._default_prompt(agent_name)
            path = versions[-1]
        else:
            path = self._base / f"{agent_name}_{version}.md"
            if not path.exists():
                return self._default_prompt(agent_name)

        content = path.read_text(encoding="utf-8")
        log.debug("prompt_loaded", agent=agent_name, version=version)
        return content

    def _default_prompt(self, agent_name: str) -> str:
        return f"You are the {agent_name} agent. Follow your capability contract."

    def list_versions(self, agent_name: str) -> list[str]:
        return [p.stem.replace(f"{agent_name}_", "") for p in self._base.glob(f"{agent_name}_*.md")]
