"""Planned Weaviate backend."""


class WeaviateVectorStore:
    def __init__(self, *_args, **_kwargs) -> None:
        raise NotImplementedError(
            "Weaviate is planned. Use VECTOR_BACKEND=memory|opensearch|qdrant."
        )
