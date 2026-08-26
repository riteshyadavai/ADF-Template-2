"""Jina AI embeddings client (Agentic-RAG compatible)."""

from __future__ import annotations

import httpx

from factories.embeddings.protocol import EmbeddingsClient


class JinaEmbeddingsClient(EmbeddingsClient):
    def __init__(self, api_key: str, model: str = "jina-embeddings-v3") -> None:
        self._api_key = api_key
        self._model = model
        self._version = "v3"

    @property
    def model_version(self) -> str:
        return self._version

    async def embed(self, texts: list[str], *, model: str | None = None) -> list[list[float]]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.jina.ai/v1/embeddings",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={"model": model or self._model, "input": texts},
            )
            response.raise_for_status()
            data = response.json()
            return [item["embedding"] for item in data["data"]]
