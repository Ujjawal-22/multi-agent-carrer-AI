"""
Structured output contract for the Job Description Analyzer Agent.

No default values on any field - Gemini's response_schema parameter
rejects Pydantic models containing defaults (see
CRITICAL note in principles/config). Nullable fields use `| None` with no
`= None`; list fields are required `list[str]`, not defaulted.
"""

from pydantic import BaseModel


class JobExtraction(BaseModel):
    job_title: str | None
    required_skills: list[str]
    preferred_skills: list[str]
    programming_languages: list[str]
    frameworks: list[str]
    tools: list[str]
    ai_ml_technologies: list[str]
    genai_technologies: list[str]
    cloud_requirements: list[str]
    database_requirements: list[str]
    experience_requirements: str | None
    education_requirements: str | None
    responsibilities: list[str]
    keywords: list[str]
    domain: str | None
    seniority_level: str | None
