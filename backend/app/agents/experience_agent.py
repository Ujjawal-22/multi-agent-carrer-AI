"""
Experience/Project Analysis Agent.

Runs in parallel with the ATS Agent — see orchestrator.py.
"""

import logging

from app.agents.prompt_loader import load_prompt
from app.agents.state import AgentError, AnalysisState
from app.schemas.experience_analysis import ExperienceAnalysisResult
from app.services.llm import get_llm_provider
from app.services.llm.base import LLMGenerationError

logger = logging.getLogger(__name__)

AGENT_NAME = "experience_analysis"


def experience_agent_node(state: AnalysisState) -> dict:
    if state.resume_extraction is None or state.jd_extraction is None:
        logger.warning(
            "Skipping Experience Agent (analysis_id=%s): missing upstream extraction",
            state.analysis_id,
        )
        return {
            "errors": [
                AgentError(
                    agent=AGENT_NAME,
                    message=(
                        "Cannot run experience analysis: resume or job "
                        "description extraction is missing (an upstream "
                        "agent likely failed)."
                    ),
                )
            ]
        }

    prompt = load_prompt(
        "experience_analysis_v1",
        resume_json=state.resume_extraction.model_dump_json(indent=2),
        jd_json=state.jd_extraction.model_dump_json(indent=2),
    )
    provider = get_llm_provider()

    try:
        result = provider.generate_structured(prompt, ExperienceAnalysisResult)
        logger.info("Experience Agent succeeded (analysis_id=%s)", state.analysis_id)
        return {"experience_result": result}
    except LLMGenerationError as exc:
        logger.error(
            "Experience Agent failed (analysis_id=%s): %s", state.analysis_id, exc
        )
        return {"errors": [AgentError(agent=AGENT_NAME, message=str(exc))]}
