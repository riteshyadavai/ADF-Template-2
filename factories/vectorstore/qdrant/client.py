"""Qdrant vector store stub."""

from __future__ import annotations

from factories.vectorstore.memory.client import InMemoryVectorStore


class QdrantVectorStore(InMemoryVectorStore):
    def __init__(self, url: str) -> None:
        super().__init__()
        self.url = url
