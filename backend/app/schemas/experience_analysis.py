"""
Structured output contract for the Experience/Project Analysis Agent.

No default values on any field - required for Gemini response_schema
compatibility.
"""

from typing import Literal

from pydantic import BaseModel


class ProjectRelevance(BaseModel):
    project_name: str
    relevance_to_role: Literal["high", "medium", "low"]
    relevant_technologies: list[str]
    notes: str


class ExperienceAnalysisResult(BaseModel):
    overall_relevance_summary: str
    project_relevance: list[ProjectRelevance]
    technical_depth_assessment: str
    quantifiable_achievements_found: list[str]
    missing_evidence: list[str]
    weak_descriptions: list[str]
    improvement_suggestions: list[str]
