"""
Provider factory — the only place that decides which concrete
LLMProvider to instantiate, based on config.
"""

from functools import lru_cache

from app.core.config import get_settings
from app.services.llm.base import LLMProvider
from app.services.llm.gemini_provider import GeminiProvider


@lru_cache
def get_llm_provider() -> LLMProvider:
    settings = get_settings()

    if settings.LLM_PROVIDER == "gemini":
        return GeminiProvider()

    raise ValueError(
        f"Unsupported LLM_PROVIDER: '{settings.LLM_PROVIDER}'. "
        "Add a new provider class and register it here to support it."
    )
