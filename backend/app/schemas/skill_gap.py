"""
Structured output contract for the Skill Gap Agent.

No default values on any field - required for Gemini response_schema
compatibility. matching/partial/transferable skills are required
list[str]; missing_skills is a required list of a required-field
sub-model.
"""

from typing import Literal

from pydantic import BaseModel


class MissingSkill(BaseModel):
    skill_name: str
    importance: Literal["critical", "important", "nice_to_have"]
    reason: str
    suggested_learning_priority: Literal["high", "medium", "low"]


class SkillGapResult(BaseModel):
    matching_skills: list[str]
    partially_matching_skills: list[str]
    transferable_skills: list[str]
    missing_skills: list[MissingSkill]
