"""
ATS Analysis Agent.

Runs in parallel with the Experience/Project Agent (both depend only on
resume_extraction + jd_extraction, not on each other or on
skill_gap_result) — see orchestrator.py for the fan-out.

Also uses resume_raw_text directly (not just the structured extraction),
since section/structure judgments benefit from seeing the text as
originally laid out, not just the summarized fields.
"""

import logging

from app.agents.prompt_loader import load_prompt
from app.agents.state import AgentError, AnalysisState
from app.schemas.ats_analysis import ATS_METHODOLOGY_DISCLAIMER, ATSAnalysisResult
from app.services.llm import get_llm_provider
from app.services.llm.base import LLMGenerationError

logger = logging.getLogger(__name__)

AGENT_NAME = "ats_analysis"


def ats_agent_node(state: AnalysisState) -> dict:
    if state.resume_extraction is None or state.jd_extraction is None:
        logger.warning(
            "Skipping ATS Agent (analysis_id=%s): missing upstream extraction",
            state.analysis_id,
        )
        return {
            "errors": [
                AgentError(
                    agent=AGENT_NAME,
                    message=(
                        "Cannot run ATS analysis: resume or job description "
                        "extraction is missing (an upstream agent likely failed)."
                    ),
                )
            ]
        }

    prompt = load_prompt(
        "ats_analysis_v1",
        resume_text=state.resume_raw_text,
        resume_json=state.resume_extraction.model_dump_json(indent=2),
        jd_json=state.jd_extraction.model_dump_json(indent=2),
    )
    provider = get_llm_provider()

    try:
        result = provider.generate_structured(prompt, ATSAnalysisResult)
        # ALWAYS overwrite methodology_note in code, regardless of what the
        # model returned — this disclaimer must never depend on the LLM
        # remembering to include it correctly.
        result = result.model_copy(
            update={"methodology_note": ATS_METHODOLOGY_DISCLAIMER}
        )
        logger.info("ATS Agent succeeded (analysis_id=%s)", state.analysis_id)
        return {"ats_result": result}
    except LLMGenerationError as exc:
        logger.error("ATS Agent failed (analysis_id=%s): %s", state.analysis_id, exc)
        return {"errors": [AgentError(agent=AGENT_NAME, message=str(exc))]}
