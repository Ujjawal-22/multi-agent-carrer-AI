"""
Centralized application configuration.

All environment-dependent values live here. Nothing in the rest of the
codebase should read os.environ directly - always go through get_settings()
so there is exactly one source of truth, and so tests can override settings
cleanly.

IMPORTANT: .env resolution. uvicorn is run from inside backend/, but .env
lives at the project root (one level up), so a plain relative "​.env" string
would look in the wrong place. We resolve it explicitly relative to this
file's location so it works regardless of the process's working directory
or where the repo is checked out.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py -> parents[0]=core, [1]=app, [2]=backend,
# [3]=project root.
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_ENV_FILE_PATH = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- App ---
    APP_NAME: str = "Multi-Agent Career AI"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # --- Database ---
    DATABASE_URL: str = (
        "postgresql+psycopg2://career_ai:career_ai@localhost:5432/career_ai"
    )

    # --- LLM Provider ---
    LLM_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash-lite"

    # --- Vector DB ---
    QDRANT_URL: str = "http://localhost:6333"

    # --- Observability ---
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    # --- Logging ---
    LOG_LEVEL: str = "INFO"

    # --- File upload / document processing (Phase 2) ---
    MAX_UPLOAD_SIZE_MB: int = 5
    ALLOWED_RESUME_EXTENSIONS: tuple[str, ...] = (".pdf", ".docx")
    DATA_DIR: str = "../data"

    MIN_DIRECT_TEXT_LENGTH: int = 50
    TESSERACT_CMD: str = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    # --- RAG (Phase 4) ---
    QDRANT_COLLECTION_NAME: str = "career_ai_knowledge_base"
    EMBEDDING_MODEL: str = "gemini-embedding-2"
    # 768 is one of Gemini's recommended output dimensions (128-3072 via
    # Matryoshka Representation Learning) - a good quality/storage balance
    # for a small knowledge base; no need for the full 3072 here.
    EMBEDDING_DIMENSIONS: int = 768
    # Character-based chunk size (not tokens) - simple and good enough for
    # markdown reference docs, avoids needing a tokenizer dependency.
    RAG_CHUNK_SIZE: int = 800
    RAG_CHUNK_OVERLAP: int = 100
    RAG_TOP_K: int = 5

    # --- Matching Agent weights (Phase 3, Matching slice) ---
    # These need not sum to exactly 1.0 - the scorer normalizes them at
    # use time - but keeping them summing to 1.0 makes the raw values
    # directly readable as "percent of the overall score."
    MATCH_WEIGHT_TECHNICAL_SKILL: float = 0.35
    MATCH_WEIGHT_ATS_KEYWORD: float = 0.20
    MATCH_WEIGHT_EXPERIENCE_PROJECT: float = 0.25
    MATCH_WEIGHT_EDUCATION: float = 0.10
    MATCH_WEIGHT_DOMAIN: float = 0.10


@lru_cache
def get_settings() -> Settings:
    return Settings()
