"""
Knowledge base ingestion script.

Run with: python -m app.rag.ingest

Reads every markdown file under data/knowledge_base/<category>/, chunks
it, embeds the chunks via Gemini, and upserts into Qdrant. Safe to re-run:
chunk IDs are deterministic (see knowledge_base.py), so re-ingesting
unchanged content updates existing points rather than duplicating them.

This is a standalone script, not an API endpoint - the knowledge base
changes rarely, so it doesn't need to be a live service operation.
"""

import logging

from app.core.logging_config import configure_logging
from app.rag.embeddings import embed_documents
from app.rag.knowledge_base import load_and_chunk_knowledge_base
from app.rag.vector_store import ensure_collection, upsert_chunks

logger = logging.getLogger(__name__)

_EMBED_BATCH_SIZE = 20


def run_ingestion() -> None:
    ensure_collection()

    all_chunks = load_and_chunk_knowledge_base()
    logger.info(
        "Loaded and chunked %d total chunks from the knowledge base.",
        len(all_chunks),
    )

    if not all_chunks:
        logger.warning(
            "No knowledge base content found - check that data/knowledge_base/"
            "<category>/*.md files exist."
        )
        return

    for batch_start in range(0, len(all_chunks), _EMBED_BATCH_SIZE):
        batch = all_chunks[batch_start : batch_start + _EMBED_BATCH_SIZE]
        vectors = embed_documents([c.text for c in batch])
        upsert_chunks(batch, vectors)
        logger.info(
            "Upserted chunks %d-%d of %d",
            batch_start + 1,
            batch_start + len(batch),
            len(all_chunks),
        )

    logger.info("Ingestion complete: %d chunks indexed.", len(all_chunks))


if __name__ == "__main__":
    configure_logging()
    run_ingestion()
