"""Embeddings client protocol."""

from __future__ import annotations

from abc import ABC, abstractmethod


class EmbeddingsClient(ABC):
    @abstractmethod
    async def embed(self, texts: list[str], *, model: str | None = None) -> list[list[float]]: ...

    @property
    @abstractmethod
    def model_version(self) -> str: ...
