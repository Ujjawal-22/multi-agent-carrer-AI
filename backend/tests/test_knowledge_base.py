"""
Tests for the shared knowledge base loader. Pure function, no network -
reads the actual markdown files in data/knowledge_base/.

The chunk_id determinism test is the most important one here: it directly
verifies the property the whole hybrid retrieval design depends on - that
re-loading the same content always produces the same chunk IDs, so dense
(Qdrant) and BM25 results for the same underlying chunk can be correctly
recognized as the same chunk during fusion.
"""

from app.rag.knowledge_base import load_and_chunk_knowledge_base


def test_loads_chunks_from_real_knowledge_base_files() -> None:
    chunks = load_and_chunk_knowledge_base()
    assert len(chunks) > 0


def test_every_chunk_has_required_metadata() -> None:
    chunks = load_and_chunk_knowledge_base()
    for chunk in chunks:
        assert chunk.chunk_id
        assert chunk.text.strip()
        assert chunk.source_file.endswith(".md")
        assert chunk.category
        assert chunk.title


def test_chunk_ids_are_deterministic_across_reloads() -> None:
    """
    CRITICAL: this is the property hybrid retrieval depends on. If this
    test ever fails, dense and BM25 fusion will silently break.
    """
    first_load = load_and_chunk_knowledge_base()
    second_load = load_and_chunk_knowledge_base()

    first_ids = [c.chunk_id for c in first_load]
    second_ids = [c.chunk_id for c in second_load]

    assert first_ids == second_ids


def test_expected_categories_present() -> None:
    chunks = load_and_chunk_knowledge_base()
    categories = {c.category for c in chunks}
    assert "skills" in categories
    assert "interview_questions" in categories
    assert "role_requirements" in categories
