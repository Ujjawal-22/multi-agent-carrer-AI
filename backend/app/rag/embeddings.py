"""
Embedding generation via Gemini's embedding model.

Uses `task_type` to distinguish document embeddings (what gets indexed)
from query embeddings (what gets searched with). Gemini's embedding model
is asymmetric: it performs meaningfully better when queries and documents
are embedded with the matching task type rather than treated identically,
so this distinction is load-bearing, not cosmetic.
"""

from google import genai
from google.genai import types

from app.core.config import get_settings

_settings = get_settings()
_client = genai.Client(api_key=_settings.GEMINI_API_KEY)


def embed_documents(texts: list[str]) -> list[list[float]]:
    """Embeds a batch of texts for INDEXING (document side)."""
    response = _client.models.embed_content(
        model=_settings.EMBEDDING_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=_settings.EMBEDDING_DIMENSIONS,
        ),
    )
    return [embedding.values for embedding in response.embeddings]


def embed_query(text: str) -> list[float]:
    """Embeds a single query text for SEARCHING (query side)."""
    response = _client.models.embed_content(
        model=_settings.EMBEDDING_MODEL,
        contents=[text],
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=_settings.EMBEDDING_DIMENSIONS,
        ),
    )
    return response.embeddings[0].values
