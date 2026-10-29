"""
Hybrid retrieval: dense (Qdrant) + keyword (BM25), combined via
reciprocal rank fusion (RRF).

No reranking stage - deliberately skipped given this knowledge base's
small size (tens of documents, not thousands) and this project's hardware
constraints (a cross-encoder reranker would require torch +
sentence-transformers, the same heavy dependency stack already avoided
for local LLM inference). If retrieval quality ever needs it, this
module is the natural place to add a reranking step later.

RRF combines rankings using each result's RANK, not its raw score - dense
cosine similarity and BM25 scores aren't on comparable numeric scales, so
fusing by rank avoids needing score normalization.

Degrades gracefully: if Qdrant is unreachable, falls back to BM25-only
results rather than failing retrieval entirely (consistent with the
"vector database failure" graceful-handling requirement from the spec).
"""

import logging
from functools import lru_cache

from rank_bm25 import BM25Okapi

from app.core.config import get_settings
from app.rag.embeddings import embed_query
from app.rag.knowledge_base import load_and_chunk_knowledge_base
from app.rag.schemas import KnowledgeChunk, RetrievedChunk
from app.rag.vector_store import dense_search

logger = logging.getLogger(__name__)

_RRF_K = 60  # standard reciprocal rank fusion constant


@lru_cache
def _build_bm25_index() -> tuple[BM25Okapi | None, tuple[KnowledgeChunk, ...]]:
    """
    Builds an in-memory BM25 index directly from the knowledge base source
    files (not from Qdrant) - a cheap, pure-text operation with no
    embedding calls, and independent of whether the vector store is up.
    Cached for the process lifetime; picking up knowledge base changes
    requires a restart, same as any in-memory cache of this kind.
    """
    chunks = tuple(load_and_chunk_knowledge_base())
    if not chunks:
        return None, chunks
    tokenized = [c.text.lower().split() for c in chunks]
    return BM25Okapi(tokenized), chunks


def _bm25_search(query: str, top_k: int) -> list[tuple[KnowledgeChunk, float]]:
    index, chunks = _build_bm25_index()
    if index is None:
        return []
    scores = index.get_scores(query.lower().split())
    ranked = sorted(zip(chunks, scores), key=lambda pair: pair[1], reverse=True)
    return list(ranked[:top_k])


def retrieve(
    query: str,
    top_k: int | None = None,
    category_filter: str | None = None,
) -> list[RetrievedChunk]:
    """
    Hybrid retrieval combining dense (Qdrant) and keyword (BM25) search via
    reciprocal rank fusion. Returns up to top_k chunks, each carrying its
    source metadata (source_file, category, title) so every retrieved
    piece of context is attributable to a specific document.
    """
    settings = get_settings()
    k = top_k or settings.RAG_TOP_K

    try:
        query_vector = embed_query(query)
        dense_results = dense_search(query_vector, top_k=k * 2)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Dense retrieval failed, falling back to BM25-only results: %s", exc
        )
        dense_results = []

    bm25_results = _bm25_search(query, top_k=k * 2)

    fused_scores: dict[str, float] = {}
    chunk_lookup: dict[str, KnowledgeChunk] = {}

    for rank, (chunk, _score) in enumerate(dense_results):
        fused_scores[chunk.chunk_id] = fused_scores.get(chunk.chunk_id, 0.0) + 1.0 / (
            _RRF_K + rank + 1
        )
        chunk_lookup[chunk.chunk_id] = chunk

    for rank, (chunk, _score) in enumerate(bm25_results):
        fused_scores[chunk.chunk_id] = fused_scores.get(chunk.chunk_id, 0.0) + 1.0 / (
            _RRF_K + rank + 1
        )
        chunk_lookup[chunk.chunk_id] = chunk

    if category_filter:
        fused_scores = {
            cid: score
            for cid, score in fused_scores.items()
            if chunk_lookup[cid].category == category_filter
        }

    ranked_ids = sorted(fused_scores, key=lambda cid: fused_scores[cid], reverse=True)[
        :k
    ]

    return [
        RetrievedChunk(
            chunk=chunk_lookup[cid],
            score=fused_scores[cid],
            retrieval_method="hybrid",
        )
        for cid in ranked_ids
    ]
