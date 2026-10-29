"""
Internal RAG data structures.

These are NEVER passed to Gemini as a response_schema - they're our own
internal representations of chunks and retrieval results, constructed
entirely in Python. Normal Pydantic defaults are fine here.
"""

from pydantic import BaseModel


class KnowledgeChunk(BaseModel):
    chunk_id: str
    text: str
    source_file: str
    category: str
    title: str


class RetrievedChunk(BaseModel):
    chunk: KnowledgeChunk
    score: float
    retrieval_method: str = "hybrid"
