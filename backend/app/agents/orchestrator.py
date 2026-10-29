"""
LangGraph orchestrator - final graph for the core 9-agent pipeline
(Resume Optimization remains a separate, optional, user-triggered
feature in Phase 6, not part of this graph).

Graph shape:

    START --> resume_analyzer --\
    START --> jd_analyzer -------> skill_gap --> ats_analysis ---------\
                                              \-> experience_analysis --> matching --> recommendation --------\
                                                                                    \-> interview_prep --------> END

Three genuine parallel fan-outs in this graph:
1. Resume + JD Analyzer (from START) - neither depends on the other.
2. ATS Analysis + Experience Analysis (from skill_gap) - both depend only
   on resume_extraction + jd_extraction.
3. Recommendation + Interview Prep (from matching) - both depend only on
   resume_extraction, jd_extraction, and skill_gap_result, not on each
   other or on matching_result itself (matching_result is used as soft
   extra context by Recommendation when available, not a hard dependency).

Matching itself fans in on ATS + Experience, computes a deterministic
weighted score (zero LLM calls - see matching_scorer.py), then makes one
LLM call for a narrative explanation of its own already-computed numbers.

Every node guards against missing upstream data and records a structured
error instead of crashing - this cascades correctly through the entire
chain: a Resume Agent failure means every downstream node detects the gap
and records its own error without calling its own LLM.
"""

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agents.ats_agent import ats_agent_node
from app.agents.experience_agent import experience_agent_node
from app.agents.interview_agent import interview_agent_node
from app.agents.jd_agent import jd_agent_node
from app.agents.matching_agent import matching_agent_node
from app.agents.recommendation_agent import recommendation_agent_node
from app.agents.resume_agent import resume_agent_node
from app.agents.skill_gap_agent import skill_gap_agent_node
from app.agents.state import AnalysisState


def build_analysis_graph() -> CompiledStateGraph:
    graph = StateGraph(AnalysisState)

    graph.add_node("resume_analyzer", resume_agent_node)
    graph.add_node("jd_analyzer", jd_agent_node)
    graph.add_node("skill_gap", skill_gap_agent_node)
    graph.add_node("ats_analysis", ats_agent_node)
    graph.add_node("experience_analysis", experience_agent_node)
    graph.add_node("matching", matching_agent_node)
    graph.add_node("recommendation", recommendation_agent_node)
    graph.add_node("interview_prep", interview_agent_node)

    graph.add_edge(START, "resume_analyzer")
    graph.add_edge(START, "jd_analyzer")

    graph.add_edge("resume_analyzer", "skill_gap")
    graph.add_edge("jd_analyzer", "skill_gap")

    graph.add_edge("skill_gap", "ats_analysis")
    graph.add_edge("skill_gap", "experience_analysis")

    graph.add_edge("ats_analysis", "matching")
    graph.add_edge("experience_analysis", "matching")

    graph.add_edge("matching", "recommendation")
    graph.add_edge("matching", "interview_prep")

    graph.add_edge("recommendation", END)
    graph.add_edge("interview_prep", END)

    return graph.compile()


analysis_graph = build_analysis_graph()
