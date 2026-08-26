"""Embeddings factory."""

from __future__ import annotations

import os

from config.settings import Settings, get_settings
from factories.embeddings.jina.client import JinaEmbeddingsClient
from factories.embeddings.protocol import EmbeddingsClient


class LiteLLMEmbeddingsClient(EmbeddingsClient):
    """Fallback embeddings via LiteLLM."""

    def __init__(self, model: str, version: str) -> None:
        self._model = model
        self._version = version

    @property
    def model_version(self) -> str:
        return self._version

    async def embed(self, texts: list[str], *, model: str | None = None) -> list[list[float]]:
        from litellm import aembedding

        response = await aembedding(model=model or self._model, input=texts)
        return [item["embedding"] for item in response.data]


def make_embeddings_client(settings: Settings | None = None) -> EmbeddingsClient:
    settings = settings or get_settings()
    jina_key = os.getenv("JINA_API_KEY")
    if jina_key:
        return JinaEmbeddingsClient(api_key=jina_key, model=settings.vector_store.embedding_model)
    return LiteLLMEmbeddingsClient(
        model=settings.vector_store.embedding_model,
        version=settings.vector_store.embedding_model_version,
    )
