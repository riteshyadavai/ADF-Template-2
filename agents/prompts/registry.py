"""Versioned prompt registry — prompts as artifacts, not inline strings."""

from __future__ import annotations

from pathlib import Path

from config.settings import PROJECT_ROOT
from shared.logger import get_logger

log = get_logger(__name__)

PROMPTS_DIR = PROJECT_ROOT / "agents" / "prompts" / "versions"


class PromptRegistry:
    def __init__(
        self,
        base_dir: Path | None = None,
        extra_dirs: list[Path] | None = None,
    ) -> None:
        self._base = base_dir or PROMPTS_DIR
        self._base.mkdir(parents=True, exist_ok=True)
        self._dirs = [self._base, *(extra_dirs or [])]

    def _search_dirs(self) -> list[Path]:
        return [d for d in self._dirs if d.exists()]

    def load(self, agent_name: str, version: str = "latest") -> str:
        if version == "latest":
            versions: list[Path] = []
            for directory in self._search_dirs():
                versions.extend(directory.glob(f"{agent_name}_*.md"))
            if not versions:
                return self._default_prompt(agent_name)
            path = sorted(versions)[-1]
        else:
            path = None
            for directory in self._search_dirs():
                candidate = directory / f"{agent_name}_{version}.md"
                if candidate.exists():
                    path = candidate
                    break
            if path is None:
                return self._default_prompt(agent_name)

        content = path.read_text(encoding="utf-8")
        log.debug("prompt_loaded", agent=agent_name, version=version)
        return content

    def _default_prompt(self, agent_name: str) -> str:
        return f"You are the {agent_name} agent. Follow your capability contract."

    def list_versions(self, agent_name: str) -> list[str]:
        names: list[str] = []
        for directory in self._search_dirs():
            names.extend(
                p.stem.replace(f"{agent_name}_", "")
                for p in directory.glob(f"{agent_name}_*.md")
            )
        return names
