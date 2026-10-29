"""
FastAPI application entrypoint.

Run locally with: uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    analysis,
    health,
    jobs,
    optimization,
    resume_versions,
    resumes,
)
from app.core.config import get_settings
from app.core.logging_config import configure_logging

configure_logging()
settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Multi-Agent Job & Resume Intelligence System API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:4173",
    "http://localhost:4173",
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(resumes.router)
app.include_router(jobs.router)
app.include_router(analysis.router)
app.include_router(optimization.router)
app.include_router(resume_versions.router)

@app.get("/")
def root() -> dict:
    return {"message": f"{settings.APP_NAME} API is running", "docs": "/docs"}
