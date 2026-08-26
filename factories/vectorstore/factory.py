"""Vector store factory."""

from __future__ import annotations

from config.settings import Settings, get_settings
from factories.vectorstore.memory.client import InMemoryVectorStore
from factories.vectorstore.opensearch.client import OpenSearchVectorStore
from factories.vectorstore.protocol import VectorStore
from factories.vectorstore.qdrant.client import QdrantVectorStore


def make_vector_store(settings: Settings | None = None) -> VectorStore:
    settings = settings or get_settings()
    backend = settings.vector_store.backend

    if backend == "opensearch":
        password = settings.vector_store.opensearch_password
        return OpenSearchVectorStore(
            url=settings.vector_store.opensearch_url,
            username=settings.vector_store.opensearch_username,
            password=password.get_secret_value() if password else None,
            verify_certs=settings.vector_store.opensearch_verify_certs,
        )

    if backend == "qdrant":
        return QdrantVectorStore(url=settings.vector_store.qdrant_url or "http://localhost:6333")

    if backend == "memory":
        return InMemoryVectorStore()
    raise ValueError(f"Unsupported vector store backend: {backend}")
