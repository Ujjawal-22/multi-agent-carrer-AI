"""
Shared knowledge base loading + chunking logic.

CRITICAL: this is used by BOTH the ingestion script (populates Qdrant)
and the retriever (builds the in-memory BM25 index). Both MUST produce
identical chunk_ids for the same source content - if ingestion generated
IDs one way and the retriever's BM25 builder generated them another way,
dense and BM25 results for the exact same underlying chunk would never be
recognized as the same chunk during reciprocal rank fusion, silently
breaking hybrid retrieval in a way that would be very confusing to debug
later. Routing both paths through this one function eliminates that
entire class of bug by construction.
"""

import uuid
from pathlib import Path

from app.core.config import get_settings
from app.rag.chunking import chunk_text
from app.rag.schemas import KnowledgeChunk


def _derive_title(markdown_text: str, fallback: str) -> str:
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return fallback


def _chunk_id(category: str, filename: str, index: int) -> str:
    # Deterministic UUID derived from (category, filename, chunk index) -
    # re-running ingestion on unchanged content produces the same IDs, so
    # Qdrant upserts update existing points rather than duplicating them.
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{category}/{filename}::{index}"))


def load_and_chunk_knowledge_base() -> list[KnowledgeChunk]:
    """
    Walks data/knowledge_base/<category>/*.md, chunks each file, and
    returns every chunk with consistent metadata and IDs.
    """
    settings = get_settings()
    kb_root = Path(settings.DATA_DIR) / "knowledge_base"

    chunks: list[KnowledgeChunk] = []
    if not kb_root.exists():
        return chunks

    for category_dir in sorted(kb_root.iterdir()):
        if not category_dir.is_dir():
            continue
        for md_file in sorted(category_dir.glob("*.md")):
            text = md_file.read_text(encoding="utf-8")
            title = _derive_title(
                text, fallback=md_file.stem.replace("_", " ").title()
            )
            for index, piece in enumerate(chunk_text(text)):
                chunks.append(
                    KnowledgeChunk(
                        chunk_id=_chunk_id(category_dir.name, md_file.name, index),
                        text=piece,
                        source_file=md_file.name,
                        category=category_dir.name,
                        title=title,
                    )
                )
    return chunks
