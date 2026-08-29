"""Planned pgvector backend."""


class PgVectorStore:
    def __init__(self, *_args, **_kwargs) -> None:
        raise NotImplementedError(
            "pgvector is planned. Use VECTOR_BACKEND=memory|opensearch|qdrant."
        )
