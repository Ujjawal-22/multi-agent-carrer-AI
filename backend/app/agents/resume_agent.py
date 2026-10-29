"""
Resume Analyzer Agent — LangGraph node.
"""

import logging

from app.agents.prompt_loader import load_prompt
from app.agents.state import AgentError, AnalysisState
from app.schemas.resume_extraction import ResumeExtraction
from app.services.llm import get_llm_provider
from app.services.llm.base import LLMGenerationError

logger = logging.getLogger(__name__)

AGENT_NAME = "resume_analyzer"


def resume_agent_node(state: AnalysisState) -> dict:
    prompt = load_prompt("resume_analyzer_v1", resume_text=state.resume_raw_text)
    provider = get_llm_provider()

    try:
        extraction = provider.generate_structured(prompt, ResumeExtraction)
        logger.info("Resume Analyzer Agent succeeded (analysis_id=%s)", state.analysis_id)
        return {"resume_extraction": extraction}
    except LLMGenerationError as exc:
        logger.error(
            "Resume Analyzer Agent failed (analysis_id=%s): %s",
            state.analysis_id,
            exc,
        )
        return {"errors": [AgentError(agent=AGENT_NAME, message=str(exc))]}
