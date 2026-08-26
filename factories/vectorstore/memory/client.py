"""In-memory vector store."""

from __future__ import annotations

from typing import Any

from factories.vectorstore.protocol import VectorDocument, VectorSearchResult, VectorStore


class InMemoryVectorStore(VectorStore):
    def __init__(self) -> None:
        self._collections: dict[str, dict[str, VectorDocument]] = {}

    async def upsert(self, collection: str, documents: list[VectorDocument]) -> int:
        self._collections.setdefault(collection, {})
        for doc in documents:
            self._collections[collection][doc.id] = doc
        return len(documents)

    async def search(
        self,
        collection: str,
        query_embedding: list[float],
        *,
        limit: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        docs = self._collections.get(collection, {})
        results = []
        for doc in docs.values():
            if filters and not all(doc.metadata.get(k) == v for k, v in filters.items()):
                continue
            score = 1.0 if doc.embedding else 0.5
            results.append(
                VectorSearchResult(
                    id=doc.id,
                    content=doc.content,
                    score=score,
                    metadata=doc.metadata,
                )
            )
        return sorted(results, key=lambda r: r.score, reverse=True)[:limit]

    async def delete(self, collection: str, doc_ids: list[str]) -> int:
        store = self._collections.get(collection, {})
        count = 0
        for doc_id in doc_ids:
            if doc_id in store:
                del store[doc_id]
                count += 1
        return count

    async def get(self, collection: str, doc_id: str) -> VectorDocument | None:
        return self._collections.get(collection, {}).get(doc_id)
