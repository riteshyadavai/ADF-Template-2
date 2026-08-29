"""Qdrant vector store via AsyncQdrantClient."""

from __future__ import annotations

import uuid
from typing import Any

from factories.vectorstore.protocol import VectorDocument, VectorSearchResult, VectorStore


def _point_id(doc_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, doc_id))


class QdrantVectorStore(VectorStore):
    def __init__(self, url: str, *, vector_size: int = 768) -> None:
        try:
            from qdrant_client import AsyncQdrantClient
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Qdrant requires the optional extra. Install with: uv sync --extra qdrant"
            ) from exc
        self.url = url
        self._vector_size = vector_size
        self._client = AsyncQdrantClient(url=url)
        self._ready: set[str] = set()

    async def _ensure_collection(self, collection: str, size: int) -> None:
        from qdrant_client.models import Distance, VectorParams

        if collection in self._ready:
            return
        exists = await self._client.collection_exists(collection)
        if not exists:
            await self._client.create_collection(
                collection_name=collection,
                vectors_config=VectorParams(size=size, distance=Distance.COSINE),
            )
        self._ready.add(collection)

    async def upsert(self, collection: str, documents: list[VectorDocument]) -> int:
        from qdrant_client.models import PointStruct

        if not documents:
            return 0
        size = len(documents[0].embedding or []) or self._vector_size
        await self._ensure_collection(collection, size)
        points = [
            PointStruct(
                id=_point_id(doc.id),
                vector=doc.embedding or [0.0] * size,
                payload={
                    "doc_id": doc.id,
                    "content": doc.content,
                    "metadata": doc.metadata,
                    "embedding_model_version": doc.embedding_model_version,
                    "chunk_index": doc.chunk_index,
                },
            )
            for doc in documents
        ]
        await self._client.upsert(collection_name=collection, points=points)
        return len(documents)

    async def search(
        self,
        collection: str,
        query_embedding: list[float],
        *,
        limit: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        await self._ensure_collection(collection, len(query_embedding) or self._vector_size)
        result = await self._client.query_points(
            collection_name=collection,
            query=query_embedding,
            limit=limit,
        )
        hits: list[VectorSearchResult] = []
        for point in result.points:
            payload = point.payload or {}
            metadata = payload.get("metadata") or {}
            if filters and not all(metadata.get(k) == v for k, v in filters.items()):
                continue
            hits.append(
                VectorSearchResult(
                    id=str(payload.get("doc_id") or point.id),
                    content=str(payload.get("content") or ""),
                    score=float(point.score or 0.0),
                    metadata=metadata,
                )
            )
        return hits

    async def delete(self, collection: str, doc_ids: list[str]) -> int:
        from qdrant_client.models import PointIdsList

        await self._client.delete(
            collection_name=collection,
            points_selector=PointIdsList(points=[_point_id(doc_id) for doc_id in doc_ids]),
        )
        return len(doc_ids)

    async def get(self, collection: str, doc_id: str) -> VectorDocument | None:
        points = await self._client.retrieve(collection_name=collection, ids=[_point_id(doc_id)])
        if not points:
            return None
        point = points[0]
        payload = point.payload or {}
        vector = point.vector if isinstance(point.vector, list) else None
        return VectorDocument(
            id=str(payload.get("doc_id") or doc_id),
            content=str(payload.get("content") or ""),
            embedding=vector,
            metadata=payload.get("metadata") or {},
            embedding_model_version=str(payload.get("embedding_model_version") or "v1"),
            chunk_index=int(payload.get("chunk_index") or 0),
        )
