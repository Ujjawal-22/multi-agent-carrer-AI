"""
Tests for hybrid retrieval. Mocks the embedding API call and Qdrant
search (both real network calls) while using the REAL knowledge base
content for BM25, since that's pure local text processing with no
external dependency.
"""

from unittest.mock import patch

from app.rag.knowledge_base import load_and_chunk_knowledge_base
from app.rag.retriever import retrieve


def test_retrieve_finds_relevant_content_via_bm25_when_dense_unavailable() -> None:
    """
    With dense retrieval failing entirely, BM25 alone should still surface
    genuinely relevant content for a query that closely matches known
    knowledge base text (the LangChain reference doc).
    """
    with patch("app.rag.retriever.embed_query") as mock_embed_query:
        mock_embed_query.side_effect = Exception("embedding API unavailable")

        results = retrieve("LangChain prompt templates chains")

    assert len(results) > 0
    # At least one result should come from the langchain.md source file,
    # given how closely the query matches that document's actual content.
    source_files = {rc.chunk.source_file for rc in results}
    assert "langchain.md" in source_files


def test_retrieve_degrades_gracefully_without_raising() -> None:
    """
    Dense retrieval failing should never propagate as an exception out of
    retrieve() - this is the "vector database failure" graceful-handling
    behavior the spec requires.
    """
    with patch("app.rag.retriever.embed_query") as mock_embed_query:
        mock_embed_query.side_effect = Exception("embedding API unavailable")
        # Should not raise.
        results = retrieve("any query at all")
        assert isinstance(results, list)


def test_retrieve_respects_category_filter() -> None:
    with patch("app.rag.retriever.embed_query") as mock_embed_query:
        mock_embed_query.side_effect = Exception("no network in tests")

        results = retrieve("Python testing", category_filter="skills")

    for result in results:
        assert result.chunk.category == "skills"


def test_retrieve_fuses_dense_and_bm25_results() -> None:
    """
    A chunk that ONLY dense search finds (BM25 would miss it due to no
    keyword overlap) should still be returned when dense search is mocked
    to return it - proving fusion actually incorporates dense results, not
    just BM25.
    """
    real_chunks = load_and_chunk_knowledge_base()
    # Pick a real chunk from the data_scientist.md doc to simulate a dense
    # hit for a query that shares no keywords with it.
    target_chunk = next(
        c for c in real_chunks if c.source_file == "data_scientist.md"
    )

    with (
        patch("app.rag.retriever.embed_query") as mock_embed_query,
        patch("app.rag.retriever.dense_search") as mock_dense_search,
    ):
        mock_embed_query.return_value = [0.0] * 768
        mock_dense_search.return_value = [(target_chunk, 0.95)]

        results = retrieve("zzzznonsensequerywithnooverlap", top_k=10)

    result_source_files = {rc.chunk.source_file for rc in results}
    assert "data_scientist.md" in result_source_files
