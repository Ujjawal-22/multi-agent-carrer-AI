"""
Skill Gap Agent.

Unlike Resume/JD Analyzer agents, this agent doesn't read raw text — it
reasons over two already-structured objects (resume_extraction and
jd_extraction) that must both exist in state before this node can
meaningfully run. Because of that dependency, this node sits AFTER the
Resume+JD fan-in in the graph, not in parallel with them (see
orchestrator.py).
"""

import logging

from app.agents.prompt_loader import load_prompt
from app.agents.state import AgentError, AnalysisState
from app.schemas.skill_gap import SkillGapResult
from app.services.llm import get_llm_provider
from app.services.llm.base import LLMGenerationError

logger = logging.getLogger(__name__)

AGENT_NAME = "skill_gap"


def skill_gap_agent_node(state: AnalysisState) -> dict:
    if state.resume_extraction is None or state.jd_extraction is None:
        # One or both upstream agents failed. Don't call the LLM with
        # incomplete/garbage input — record a clear, honest error instead.
        logger.warning(
            "Skipping Skill Gap Agent (analysis_id=%s): missing upstream extraction",
            state.analysis_id,
        )
        return {
            "errors": [
                AgentError(
                    agent=AGENT_NAME,
                    message=(
                        "Cannot run skill gap analysis: resume or job "
                        "description extraction is missing (an upstream "
                        "agent likely failed)."
                    ),
                )
            ]
        }

    prompt = load_prompt(
        "skill_gap_v1",
        resume_json=state.resume_extraction.model_dump_json(indent=2),
        jd_json=state.jd_extraction.model_dump_json(indent=2),
    )
    provider = get_llm_provider()

    try:
        result = provider.generate_structured(prompt, SkillGapResult)
        logger.info("Skill Gap Agent succeeded (analysis_id=%s)", state.analysis_id)
        return {"skill_gap_result": result}
    except LLMGenerationError as exc:
        logger.error(
            "Skill Gap Agent failed (analysis_id=%s): %s", state.analysis_id, exc
        )
        return {"errors": [AgentError(agent=AGENT_NAME, message=str(exc))]}
