"""
Gemini implementation of LLMProvider, using the google-genai SDK's native
Pydantic response_schema support.
"""

import logging
from typing import TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel, ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.services.llm.base import LLMGenerationError, LLMProvider

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class GeminiProvider(LLMProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self._model = settings.GEMINI_MODEL

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=20),
        reraise=True,
    )
    def generate_structured(
        self,
        prompt: str,
        response_schema: type[T],
        *,
        temperature: float = 0.2,
    ) -> T:
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=temperature,
            ),
        )

        if response.parsed is not None:
            return response.parsed  # type: ignore[return-value]

        try:
            return response_schema.model_validate_json(response.text)
        except (ValidationError, ValueError) as exc:
            logger.warning(
                "Structured output validation failed for %s: %s",
                response_schema.__name__,
                exc,
            )
            raise LLMGenerationError(
                f"Model did not return valid {response_schema.__name__} JSON."
            ) from exc
