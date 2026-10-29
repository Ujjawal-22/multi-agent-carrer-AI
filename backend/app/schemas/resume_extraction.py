"""
Structured output contract for the Resume Analyzer Agent.

No default values on any field - Gemini's response_schema parameter
rejects Pydantic models containing defaults
("ValueError: Default value is not supported in the response schema for
the Gemini API"). Nullable fields use `| None` with no `= None`.
"""

from pydantic import BaseModel


class Education(BaseModel):
    degree: str | None
    field_of_study: str | None
    university: str | None
    graduation_year: str | None


class Project(BaseModel):
    name: str
    description: str | None
    technologies: list[str]


class Experience(BaseModel):
    title: str | None
    company: str | None
    duration: str | None
    description: str | None
    is_internship: bool


class TechnicalSkills(BaseModel):
    programming_languages: list[str]
    frameworks: list[str]
    tools: list[str]
    databases: list[str]
    cloud_technologies: list[str]
    ai_ml_skills: list[str]
    genai_skills: list[str]


class ResumeExtraction(BaseModel):
    name: str | None
    email: str | None
    phone: str | None
    education: list[Education]
    technical_skills: TechnicalSkills
    projects: list[Project]
    experience: list[Experience]
    certifications: list[str]
    achievements: list[str]
    soft_skills: list[str]
