"""OpenSearch k-NN vector store adapter."""

from __future__ import annotations

import importlib
from typing import Any
from urllib.parse import urlparse

from factories.vectorstore.protocol import VectorDocument, VectorSearchResult, VectorStore


class OpenSearchVectorStore(VectorStore):
    def __init__(
        self,
        url: str,
        *,
        username: str | None = None,
        password: str | None = None,
        verify_certs: bool = True,
    ) -> None:
        parsed = urlparse(url if "://" in url else f"http://{url}")
        self._hosts = [
            {
                "host": parsed.hostname or "localhost",
                "port": parsed.port or (443 if parsed.scheme == "https" else 9200),
            }
        ]
        self._use_ssl = parsed.scheme == "https"
        self._auth = (username, password) if username and password else None
        self._verify_certs = verify_certs
        self._client: Any | None = None

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                opensearch = importlib.import_module("opensearchpy")
            except ModuleNotFoundError as exc:
                raise RuntimeError(
                    "The OpenSearch backend requires its optional dependencies. "
                    "Install them with: uv sync --extra opensearch"
                ) from exc
            kwargs: dict[str, Any] = {
                "hosts": self._hosts,
                "use_ssl": self._use_ssl,
                "verify_certs": self._verify_certs,
                "connection_class": opensearch.AsyncHttpConnection,
            }
            if self._auth:
                kwargs["http_auth"] = self._auth
            self._client = opensearch.AsyncOpenSearch(**kwargs)
        return self._client

    async def _ensure_index(self, collection: str, dimension: int) -> None:
        client = self._get_client()
        if await client.indices.exists(index=collection):
            return
        await client.indices.create(
            index=collection,
            body={
                "settings": {"index": {"knn": True}},
                "mappings": {
                    "properties": {
                        "content": {"type": "text"},
                        "embedding": {"type": "knn_vector", "dimension": dimension},
                        "metadata": {"type": "object"},
                        "embedding_model_version": {"type": "keyword"},
                        "chunk_index": {"type": "integer"},
                    }
                },
            },
        )

    async def upsert(self, collection: str, documents: list[VectorDocument]) -> int:
        if not documents:
            return 0
        first_embedding = next((doc.embedding for doc in documents if doc.embedding), None)
        if first_embedding is None:
            raise ValueError("OpenSearch vector documents require embeddings")
        if any(doc.embedding is None for doc in documents):
            raise ValueError("All OpenSearch vector documents must include an embedding")
        await self._ensure_index(collection, len(first_embedding))
        body: list[dict[str, Any]] = []
        for document in documents:
            body.extend(
                [
                    {"index": {"_index": collection, "_id": document.id}},
                    {
                        "content": document.content,
                        "embedding": document.embedding,
                        "metadata": document.metadata,
                        "embedding_model_version": document.embedding_model_version,
                        "chunk_index": document.chunk_index,
                    },
                ]
            )
        response = await self._get_client().bulk(body=body, refresh=True)
        failures = [item for item in response.get("items", []) if item["index"]["status"] >= 300]
        if failures:
            raise RuntimeError(f"OpenSearch bulk upsert failed for {len(failures)} documents")
        return len(documents)

    async def search(
        self,
        collection: str,
        query_embedding: list[float],
        *,
        limit: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        knn: dict[str, Any] = {"vector": query_embedding, "k": limit}
        if filters:
            knn["filter"] = {
                "bool": {
                    "filter": [
                        {"term": {f"metadata.{key}": value}}
                        for key, value in filters.items()
                    ]
                }
            }
        response = await self._get_client().search(
            index=collection,
            body={"size": limit, "query": {"knn": {"embedding": knn}}},
        )
        return [
            VectorSearchResult(
                id=hit["_id"],
                content=hit["_source"]["content"],
                score=hit.get("_score", 0.0),
                metadata=hit["_source"].get("metadata", {}),
            )
            for hit in response.get("hits", {}).get("hits", [])
        ]

    async def delete(self, collection: str, doc_ids: list[str]) -> int:
        if not doc_ids:
            return 0
        body = [{"delete": {"_index": collection, "_id": doc_id}} for doc_id in doc_ids]
        response = await self._get_client().bulk(body=body, refresh=True)
        return sum(
            1
            for item in response.get("items", [])
            if item["delete"]["status"] in {200, 202}
        )

    async def get(self, collection: str, doc_id: str) -> VectorDocument | None:
        client = self._get_client()
        if not await client.exists(index=collection, id=doc_id):
            return None
        response = await client.get(index=collection, id=doc_id)
        source = response["_source"]
        return VectorDocument(
            id=response["_id"],
            content=source["content"],
            embedding=source.get("embedding"),
            metadata=source.get("metadata", {}),
            embedding_model_version=source.get("embedding_model_version", "v1"),
            chunk_index=source.get("chunk_index", 0),
        )

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None
