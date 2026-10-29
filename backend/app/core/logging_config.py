"""
Application-wide logging setup.

IMPORTANT: never log raw resume/JD text or PII here or anywhere else in
the app. Log identifiers (e.g. resume_id) and metadata, not content.
"""

import logging
import sys

from app.core.config import get_settings


def configure_logging() -> None:
    settings = get_settings()

    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DEBUG else logging.WARNING
    )

    logging.getLogger(__name__).info(
        "Logging configured (level=%s, env=%s)", settings.LOG_LEVEL, settings.APP_ENV
    )
