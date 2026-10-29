"""
Health check endpoint — checks actual dependencies, not just "process alive."
"""

import time

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.rag.vector_store import is_healthy as qdrant_is_healthy

router = APIRouter(prefix="/api", tags=["health"])

_START_TIME = time.time()


@router.get("/health")
def health_check(db: Session = Depends(get_db)) -> dict:
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        db_status = f"error: {exc}"

    qdrant_status = "ok" if qdrant_is_healthy() else "unreachable"

    overall_ok = db_status == "ok" and qdrant_status == "ok"

    return {
        "status": "ok" if overall_ok else "degraded",
        "uptime_seconds": round(time.time() - _START_TIME, 2),
        "dependencies": {
            "database": db_status,
            "qdrant": qdrant_status,
        },
    }
