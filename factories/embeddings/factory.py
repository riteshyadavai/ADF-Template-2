"""Embeddings factory."""

from __future__ import annotations

import os

from config.settings import Settings, get_settings
from factories.embeddings.jina.client import JinaEmbeddingsClient
from factories.embeddings.litellm.client import LiteLLMEmbeddingsClient
from factories.embeddings.protocol import EmbeddingsClient


def make_embeddings_client(settings: Settings | None = None) -> EmbeddingsClient:
    settings = settings or get_settings()
    backend = os.getenv("EMBEDDINGS_BACKEND", settings.vector_store.embeddings_backend)
    jina_key = os.getenv("JINA_API_KEY")
    if backend == "jina" or jina_key:
        if not jina_key:
            raise ValueError("JINA_API_KEY is required when embeddings backend is jina")
        return JinaEmbeddingsClient(api_key=jina_key, model=settings.vector_store.embedding_model)
    return LiteLLMEmbeddingsClient(
        model=settings.vector_store.embedding_model,
        version=settings.vector_store.embedding_model_version,
    )
