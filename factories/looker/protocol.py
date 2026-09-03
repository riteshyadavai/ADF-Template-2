"""Looker API client protocol."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LookerClient(ABC):
    enabled: bool

    @abstractmethod
    def me(self) -> dict[str, Any]: ...

    @abstractmethod
    def run_look(self, look_id: str, result_format: str = "json") -> list[dict[str, Any]] | str: ...

    @abstractmethod
    def run_inline_query(
        self,
        *,
        model: str,
        view: str,
        fields: list[str],
        filters: dict[str, str] | None = None,
        limit: int = 100,
        result_format: str = "json",
    ) -> list[dict[str, Any]] | str: ...
