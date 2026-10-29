"""
Tests for the text chunking utility. Pure function, no network/mocking.
"""

from app.rag.chunking import chunk_text


def test_chunk_text_splits_long_text_into_multiple_chunks() -> None:
    long_text = "This is a sentence. " * 100  # well over the default chunk size
    chunks = chunk_text(long_text)
    assert len(chunks) > 1


def test_chunk_text_does_not_lose_content() -> None:
    text = "Short text that fits in one chunk easily."
    chunks = chunk_text(text)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_strips_empty_pieces() -> None:
    text = "Paragraph one.\n\n\n\nParagraph two."
    chunks = chunk_text(text)
    assert all(c.strip() == c and c for c in chunks)
