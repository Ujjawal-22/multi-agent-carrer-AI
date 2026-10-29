"""
Structured output contract for the Recommendation Agent.

No default values on any field - Gemini response_schema compatibility.

Design intent: every recommendation here must trace back to something
already established by earlier agents (skill_gap_result's missing_skills,
ats_result/experience_result's improvement_suggestions) - this agent
synthesizes and prioritizes those findings into an actionable plan, it
does not independently invent new gaps or claims about the candidate.
"""

from pydantic import BaseModel


class RecommendationResult(BaseModel):
    skills_to_learn: list[str]
    technologies_to_practice: list[str]
    project_ideas: list[str]
    resume_improvements: list[str]
    relevant_certifications: list[str]
    interview_prep_focus_areas: list[str]
    short_term_roadmap: list[str]
