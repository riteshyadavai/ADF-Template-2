"""LiteLLM embeddings client."""

from __future__ import annotations

from factories.embeddings.protocol import EmbeddingsClient


class LiteLLMEmbeddingsClient(EmbeddingsClient):
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
