"""
Text chunking for the RAG pipeline.

Uses LangChain's RecursiveCharacterTextSplitter rather than a hand-rolled
splitter - correct chunking (preferring paragraph/sentence boundaries
over mid-word cuts) has more edge cases than it first appears, and this
is a well-tested utility for exactly that problem. We only depend on
langchain-text-splitters, not the full LangChain framework.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings


def chunk_text(text: str) -> list[str]:
    settings = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.RAG_CHUNK_SIZE,
        chunk_overlap=settings.RAG_CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_text(text)
    return [c.strip() for c in chunks if c.strip()]
