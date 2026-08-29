"""Secrets backend protocol."""

from __future__ import annotations

from abc import ABC, abstractmethod


class SecretsProvider(ABC):
    @abstractmethod
    def get_secret(self, name: str) -> str | None: ...
