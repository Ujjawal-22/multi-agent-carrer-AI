"""
Structured output contract for the Interview Preparation Agent.

No default values on any field - Gemini response_schema compatibility.

Design note: a flat list of questions with a `category` tag per question,
rather than fixed per-category lists. This is deliberate - forcing every
category (e.g. RAG questions) to be populated regardless of role relevance
would produce filler questions for roles where that category doesn't
apply. The agent is instructed to only generate categories genuinely
relevant to this specific role.
"""

from typing import Literal

from pydantic import BaseModel

QuestionCategory = Literal[
    "technical",
    "genai",
    "python",
    "ml",
    "rag",
    "agents",
    "project",
    "behavioral",
]


class InterviewQuestion(BaseModel):
    question: str
    category: QuestionCategory
    # Why this specific question was chosen - ties it back to the
    # candidate's actual resume, the JD, or a detected skill gap, so the
    # question is demonstrably personalized rather than generic.
    rationale: str


class InterviewPrepResult(BaseModel):
    questions: list[InterviewQuestion]
