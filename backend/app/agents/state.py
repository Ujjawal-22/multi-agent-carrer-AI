"""
Shared state that flows through the LangGraph orchestration graph.

Each agent node reads only the fields it needs and returns a partial
update (a dict) — LangGraph merges this into the running state. The
`errors` field uses `operator.add` as its reducer so that when multiple
agent nodes run in parallel (as Resume + JD analysis do) and both fail,
both errors are preserved rather than one overwriting the other.
"""

import operator
from typing import Annotated

from pydantic import BaseModel, Field

from app.schemas.ats_analysis import ATSAnalysisResult
from app.schemas.experience_analysis import ExperienceAnalysisResult
from app.schemas.interview import InterviewPrepResult
from app.schemas.job_extraction import JobExtraction
from app.schemas.matching import MatchingResult
from app.schemas.recommendation import RecommendationResult
from app.schemas.resume_extraction import ResumeExtraction
from app.schemas.skill_gap import SkillGapResult


class AgentError(BaseModel):
    agent: str
    message: str


class AnalysisState(BaseModel):
    analysis_id: str
    resume_raw_text: str
    jd_raw_text: str

    resume_extraction: ResumeExtraction | None = None
    jd_extraction: JobExtraction | None = None
    skill_gap_result: SkillGapResult | None = None
    ats_result: ATSAnalysisResult | None = None
    experience_result: ExperienceAnalysisResult | None = None
    matching_result: MatchingResult | None = None
    recommendation_result: RecommendationResult | None = None
    interview_result: InterviewPrepResult | None = None

    # Phase 4 (RAG): source metadata for retrieved reference material used
    # by each agent. Populated directly from the retriever's return value
    # in code - NEVER trusted from the LLM's own output, same principle as
    # ATS's methodology_note and Matching's deterministic fields. This is
    # the concrete implementation of the spec's "system should return
    # source metadata where applicable" requirement.
    recommendation_sources: list[str] = Field(default_factory=list)
    interview_sources: list[str] = Field(default_factory=list)

    errors: Annotated[list[AgentError], operator.add] = Field(default_factory=list)
