"""
Job Description Analyzer Agent — LangGraph node.
"""

import logging

from app.agents.prompt_loader import load_prompt
from app.agents.state import AgentError, AnalysisState
from app.schemas.job_extraction import JobExtraction
from app.services.llm import get_llm_provider
from app.services.llm.base import LLMGenerationError

logger = logging.getLogger(__name__)

AGENT_NAME = "jd_analyzer"


def jd_agent_node(state: AnalysisState) -> dict:
    prompt = load_prompt("jd_analyzer_v1", jd_text=state.jd_raw_text)
    provider = get_llm_provider()

    try:
        extraction = provider.generate_structured(prompt, JobExtraction)
        logger.info("JD Analyzer Agent succeeded (analysis_id=%s)", state.analysis_id)
        return {"jd_extraction": extraction}
    except LLMGenerationError as exc:
        logger.error(
            "JD Analyzer Agent failed (analysis_id=%s): %s",
            state.analysis_id,
            exc,
        )
        return {"errors": [AgentError(agent=AGENT_NAME, message=str(exc))]}
