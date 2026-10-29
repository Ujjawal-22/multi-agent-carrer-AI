"""
Recommendation Agent.

Runs after Matching in the graph. Its hard dependencies are
resume_extraction, jd_extraction, and skill_gap_result - if any of those
are missing (an earlier agent failed), it skips its own LLM call and
records a clear error, same pattern as every other agent.

Phase 4 update: now retrieves two kinds of reference material before
calling the LLM:
1. Skill/technology reference docs relevant to the candidate's missing
   skills - grounds certification/learning suggestions in real reference
   facts instead of pure LLM recall.
2. General role-requirement context - explicitly labeled in the prompt as
   TYPICAL industry expectations, not this specific job's requirements,
   so it can't be misused to invent gaps beyond what skill_gap_result
   already determined.

Retrieval failures degrade gracefully (app.rag.retriever.retrieve() never
raises - it falls back to BM25-only or empty results internally), so a
Qdrant outage doesn't block this agent, it just runs with less context.
"""

import logging

from app.agents.prompt_loader import load_prompt
from app.agents.state import AgentError, AnalysisState
from app.rag.retriever import retrieve
from app.schemas.recommendation import RecommendationResult
from app.services.llm import get_llm_provider
from app.services.llm.base import LLMGenerationError

logger = logging.getLogger(__name__)

AGENT_NAME = "recommendation"

_NO_CONTEXT_PLACEHOLDER = "No specific reference material retrieved."


def _format_chunks(chunks) -> str:
    if not chunks:
        return _NO_CONTEXT_PLACEHOLDER
    return "\n\n".join(
        f"[Source: {rc.chunk.source_file} - {rc.chunk.title}]\n{rc.chunk.text}"
        for rc in chunks
    )


def recommendation_agent_node(state: AnalysisState) -> dict:
    if (
        state.resume_extraction is None
        or state.jd_extraction is None
        or state.skill_gap_result is None
    ):
        logger.warning(
            "Skipping Recommendation Agent (analysis_id=%s): missing upstream data",
            state.analysis_id,
        )
        return {
            "errors": [
                AgentError(
                    agent=AGENT_NAME,
                    message=(
                        "Cannot generate recommendations: resume extraction, "
                        "job extraction, or skill gap result is missing (an "
                        "earlier agent likely failed)."
                    ),
                )
            ]
        }

    matching_narrative = (
        state.matching_result.narrative_summary
        if state.matching_result is not None
        else "Not available."
    )

    missing_skill_names = [
        m.skill_name for m in state.skill_gap_result.missing_skills
    ]
    retrieval_query = " ".join(
        filter(None, [state.jd_extraction.job_title, *missing_skill_names])
    ) or "software engineering skills"

    skill_chunks = retrieve(retrieval_query, category_filter="skills")
    role_chunks = retrieve(retrieval_query, category_filter="role_requirements")
    sources = sorted(
        {rc.chunk.source_file for rc in (*skill_chunks, *role_chunks)}
    )

    prompt = load_prompt(
        "recommendation_v2",
        skill_gap_json=state.skill_gap_result.model_dump_json(indent=2),
        matching_narrative=matching_narrative,
        resume_json=state.resume_extraction.model_dump_json(indent=2),
        jd_json=state.jd_extraction.model_dump_json(indent=2),
        skill_reference_context=_format_chunks(skill_chunks),
        role_reference_context=_format_chunks(role_chunks),
    )
    provider = get_llm_provider()

    try:
        result = provider.generate_structured(prompt, RecommendationResult)
        logger.info(
            "Recommendation Agent succeeded (analysis_id=%s, %d sources used)",
            state.analysis_id,
            len(sources),
        )
        return {"recommendation_result": result, "recommendation_sources": sources}
    except LLMGenerationError as exc:
        logger.error(
            "Recommendation Agent failed (analysis_id=%s): %s",
            state.analysis_id,
            exc,
        )
        return {"errors": [AgentError(agent=AGENT_NAME, message=str(exc))]}
