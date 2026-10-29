"""
Interview Preparation Agent.

Runs in parallel with the Recommendation Agent (both depend only on
resume_extraction, jd_extraction, and skill_gap_result).

Phase 4 update: retrieves two kinds of reference material before calling
the LLM:
1. Reference question patterns from the interview_questions category -
   used as inspiration for question style/depth, explicitly NOT to be
   copied verbatim (the prompt instructs personalization).
2. Skill/technology reference docs - used to ask more technically precise
   questions about claimed or missing skills.
"""

import logging

from app.agents.prompt_loader import load_prompt
from app.agents.state import AgentError, AnalysisState
from app.rag.retriever import retrieve
from app.schemas.interview import InterviewPrepResult
from app.services.llm import get_llm_provider
from app.services.llm.base import LLMGenerationError

logger = logging.getLogger(__name__)

AGENT_NAME = "interview_prep"

_NO_CONTEXT_PLACEHOLDER = "No specific reference material retrieved."


def _format_chunks(chunks) -> str:
    if not chunks:
        return _NO_CONTEXT_PLACEHOLDER
    return "\n\n".join(
        f"[Source: {rc.chunk.source_file} - {rc.chunk.title}]\n{rc.chunk.text}"
        for rc in chunks
    )


def interview_agent_node(state: AnalysisState) -> dict:
    if (
        state.resume_extraction is None
        or state.jd_extraction is None
        or state.skill_gap_result is None
    ):
        logger.warning(
            "Skipping Interview Prep Agent (analysis_id=%s): missing upstream data",
            state.analysis_id,
        )
        return {
            "errors": [
                AgentError(
                    agent=AGENT_NAME,
                    message=(
                        "Cannot generate interview questions: resume "
                        "extraction, job extraction, or skill gap result "
                        "is missing (an earlier agent likely failed)."
                    ),
                )
            ]
        }

    missing_skill_names = [
        m.skill_name for m in state.skill_gap_result.missing_skills
    ]
    retrieval_query = " ".join(
        filter(None, [state.jd_extraction.job_title, *missing_skill_names])
    ) or "software engineering interview"

    question_chunks = retrieve(retrieval_query, category_filter="interview_questions")
    skill_chunks = retrieve(retrieval_query, category_filter="skills")
    sources = sorted(
        {rc.chunk.source_file for rc in (*question_chunks, *skill_chunks)}
    )

    prompt = load_prompt(
        "interview_prep_v2",
        jd_json=state.jd_extraction.model_dump_json(indent=2),
        resume_json=state.resume_extraction.model_dump_json(indent=2),
        skill_gap_json=state.skill_gap_result.model_dump_json(indent=2),
        question_bank_context=_format_chunks(question_chunks),
        skill_reference_context=_format_chunks(skill_chunks),
    )
    provider = get_llm_provider()

    try:
        result = provider.generate_structured(prompt, InterviewPrepResult)
        logger.info(
            "Interview Prep Agent succeeded (analysis_id=%s, %d questions, "
            "%d sources used)",
            state.analysis_id,
            len(result.questions),
            len(sources),
        )
        return {"interview_result": result, "interview_sources": sources}
    except LLMGenerationError as exc:
        logger.error(
            "Interview Prep Agent failed (analysis_id=%s): %s",
            state.analysis_id,
            exc,
        )
        return {"errors": [AgentError(agent=AGENT_NAME, message=str(exc))]}
