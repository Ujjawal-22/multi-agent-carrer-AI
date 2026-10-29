"""
Matching Agent.

Unlike every other agent so far, the core of this one is NOT an LLM call —
it's a deterministic weighted formula (see matching_scorer.py) over the
outputs of Skill Gap, ATS, and Experience/Project agents. The only LLM
call this agent makes is for a short narrative explanation of the
already-computed numbers, and that call is treated as best-effort: if it
fails, the agent still returns the full (fully valid, deterministically
computed) MatchingResult with a plain fallback narrative, rather than
failing the whole agent over a nice-to-have piece of prose.
"""

import logging

from app.agents.prompt_loader import load_prompt
from app.agents.state import AgentError, AnalysisState
from app.core.config import get_settings
from app.schemas.matching import MatchingResult, MatchNarrative
from app.services.llm import get_llm_provider
from app.services.llm.base import LLMGenerationError
from app.services.matching_scorer import compute_matching_scores

logger = logging.getLogger(__name__)

AGENT_NAME = "matching"


def matching_agent_node(state: AnalysisState) -> dict:
    missing = [
        name
        for name, value in (
            ("resume_extraction", state.resume_extraction),
            ("jd_extraction", state.jd_extraction),
            ("skill_gap_result", state.skill_gap_result),
            ("ats_result", state.ats_result),
            ("experience_result", state.experience_result),
        )
        if value is None
    ]
    if missing:
        logger.warning(
            "Skipping Matching Agent (analysis_id=%s): missing %s",
            state.analysis_id,
            ", ".join(missing),
        )
        return {
            "errors": [
                AgentError(
                    agent=AGENT_NAME,
                    message=(
                        "Cannot compute match score: missing upstream "
                        f"result(s): {', '.join(missing)} (an earlier "
                        "agent likely failed)."
                    ),
                )
            ]
        }

    settings = get_settings()
    overall_score, sub_scores, weights_used = compute_matching_scores(
        resume=state.resume_extraction,
        jd_extraction=state.jd_extraction,
        resume_raw_text=state.resume_raw_text,
        skill_gap=state.skill_gap_result,
        ats_result=state.ats_result,
        experience_result=state.experience_result,
        settings=settings,
    )

    critical_missing = [
        m.skill_name
        for m in state.skill_gap_result.missing_skills
        if m.importance == "critical"
    ]

    prompt = load_prompt(
        "matching_narrative_v1",
        overall_score=overall_score,
        technical_skill_match=sub_scores.technical_skill_match,
        ats_keyword_match=sub_scores.ats_keyword_match,
        experience_project_match=sub_scores.experience_project_match,
        education_match=sub_scores.education_match,
        domain_match=sub_scores.domain_match,
        matching_skills=", ".join(state.skill_gap_result.matching_skills) or "none",
        critical_missing_skills=", ".join(critical_missing) or "none",
        ats_explanation=state.ats_result.score_explanation,
    )

    provider = get_llm_provider()
    errors: list[AgentError] = []

    try:
        narrative_response = provider.generate_structured(prompt, MatchNarrative)
        narrative = narrative_response.narrative_summary
    except LLMGenerationError as exc:
        logger.warning(
            "Matching Agent narrative generation failed (analysis_id=%s): %s "
            "- falling back to a plain generated summary.",
            state.analysis_id,
            exc,
        )
        narrative = (
            f"Overall match score: {overall_score}/100, computed from a "
            "weighted combination of technical skill match, ATS keyword "
            "match, experience/project relevance, education match, and "
            "domain match sub-scores."
        )
        errors.append(
            AgentError(
                agent=AGENT_NAME,
                message=(
                    f"Narrative generation failed, used fallback summary: {exc}"
                ),
            )
        )

    result = MatchingResult(
        overall_match_score=overall_score,
        sub_scores=sub_scores,
        weights_used=weights_used,
        narrative_summary=narrative,
    )

    logger.info(
        "Matching Agent completed (analysis_id=%s, score=%s)",
        state.analysis_id,
        overall_score,
    )
    return {"matching_result": result, "errors": errors}
