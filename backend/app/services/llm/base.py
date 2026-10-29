"""
Abstract LLM provider interface. Every agent depends on this, never on a
specific provider's SDK — swapping providers is a config change, not an
agent-code change.
"""

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMGenerationError(Exception):
    """Raised when a provider fails to produce valid structured output
    after exhausting retries."""


class LLMProvider(ABC):
    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        response_schema: type[T],
        *,
        temperature: float = 0.2,
    ) -> T:
        raise NotImplementedError
