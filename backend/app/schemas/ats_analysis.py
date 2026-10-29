"""
Structured output contract for the ATS Analysis Agent.

No default values on any field passed to Gemini - required for
response_schema compatibility. `ats_score`'s `Field(ge=0, le=100)` is
fine since ge/le are validation constraints, not defaults.

Design note on `methodology_note`: this field is NEVER filled by the LLM
in practice - it's always overwritten in code (see ats_agent.py) with the
fixed ATS_METHODOLOGY_DISCLAIMER below, immediately after the LLM
response is received. It's still a required (non-default) string field
here for Gemini schema compatibility, but its value is fully controlled
by our own code, not trusted from the model.
"""

from pydantic import BaseModel, Field

ATS_METHODOLOGY_DISCLAIMER = (
    "This ATS score is an LLM-based heuristic estimate, not the output of "
    "any real commercial ATS system (e.g. Workday, Greenhouse, Taleo). It "
    "is computed from extracted resume text and structured comparisons "
    "against the job description's keywords and requirements - it does "
    "not have access to the resume's actual visual layout, so formatting "
    "findings reflect text-detectable issues (e.g. missing section "
    "headers) rather than true visual/PDF formatting problems."
)


class KeywordCoverage(BaseModel):
    matched_keywords: list[str]
    missing_keywords: list[str]


class ATSAnalysisResult(BaseModel):
    ats_score: int = Field(ge=0, le=100)
    score_explanation: str
    keyword_coverage: KeywordCoverage
    section_structure_issues: list[str]
    formatting_issues: list[str]
    job_title_alignment_note: str | None
    improvement_suggestions: list[str]
    methodology_note: str
