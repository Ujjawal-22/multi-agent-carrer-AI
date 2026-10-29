"""
Qdrant vector store wrapper. Thin layer - no business logic here, just
collection management and the raw upsert/search calls.
"""

import logging

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.core.config import get_settings
from app.rag.schemas import KnowledgeChunk

logger = logging.getLogger(__name__)
_settings = get_settings()

_client = QdrantClient(url=_settings.QDRANT_URL)


def ensure_collection() -> None:
    """Creates the knowledge base collection if it doesn't already exist."""
    collections = [c.name for c in _client.get_collections().collections]
    if _settings.QDRANT_COLLECTION_NAME not in collections:
        _client.create_collection(
            collection_name=_settings.QDRANT_COLLECTION_NAME,
            vectors_config=VectorParams(
                size=_settings.EMBEDDING_DIMENSIONS, distance=Distance.COSINE
            ),
        )
        logger.info(
            "Created Qdrant collection '%s'", _settings.QDRANT_COLLECTION_NAME
        )


def upsert_chunks(chunks: list[KnowledgeChunk], vectors: list[list[float]]) -> None:
    points = [
        PointStruct(id=chunk.chunk_id, vector=vector, payload=chunk.model_dump())
        for chunk, vector in zip(chunks, vectors, strict=True)
    ]
    _client.upsert(collection_name=_settings.QDRANT_COLLECTION_NAME, points=points)


def dense_search(
    query_vector: list[float], top_k: int
) -> list[tuple[KnowledgeChunk, float]]:
    results = _client.search(
        collection_name=_settings.QDRANT_COLLECTION_NAME,
        query_vector=query_vector,
        limit=top_k,
    )
    return [(KnowledgeChunk(**point.payload), point.score) for point in results]


def is_healthy() -> bool:
    """Used by the /api/health endpoint - true if Qdrant is reachable."""
    try:
        _client.get_collections()
        return True
    except Exception:  # noqa: BLE001
        return False
