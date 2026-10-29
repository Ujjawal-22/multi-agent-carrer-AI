"""
Tests the LangGraph orchestration wiring - node registration, edge
routing, and state merging - WITHOUT making real Gemini API calls.

This is the final version of this test file for the core 9-agent
pipeline: 8 graph nodes (Resume, JD, Skill Gap, ATS, Experience, Matching,
Recommendation, Interview Prep). Resume Optimization is a separate,
optional, user-triggered feature (Phase 6), not part of this graph.

IMPORTANT: none of the Gemini-facing schemas (ResumeExtraction,
JobExtraction, SkillGapResult, ATSAnalysisResult, ExperienceAnalysisResult,
RecommendationResult, InterviewPrepResult) have default values on their
fields, so every fixture below explicitly supplies every required field.

Remember: use .get(key, default) when reading LangGraph result dicts,
never direct indexing. A field only exists in the result once some node
actually returns it during that run.
"""

from unittest.mock import patch

from app.agents.orchestrator import build_analysis_graph
from app.agents.state import AnalysisState
from app.schemas.ats_analysis import ATSAnalysisResult, KeywordCoverage
from app.schemas.experience_analysis import ExperienceAnalysisResult
from app.schemas.interview import InterviewPrepResult
from app.schemas.job_extraction import JobExtraction
from app.schemas.matching import MatchNarrative
from app.schemas.recommendation import RecommendationResult
from app.schemas.resume_extraction import ResumeExtraction, TechnicalSkills
from app.schemas.skill_gap import SkillGapResult

ALL_AGENT_PATCHES = (
    "app.agents.resume_agent.get_llm_provider",
    "app.agents.jd_agent.get_llm_provider",
    "app.agents.skill_gap_agent.get_llm_provider",
    "app.agents.ats_agent.get_llm_provider",
    "app.agents.experience_agent.get_llm_provider",
    "app.agents.matching_agent.get_llm_provider",
    "app.agents.recommendation_agent.get_llm_provider",
    "app.agents.interview_agent.get_llm_provider",
)


def _fake_resume_extraction() -> ResumeExtraction:
    return ResumeExtraction(
        name="Jane Doe",
        email="jane@example.com",
        phone=None,
        education=[],
        technical_skills=TechnicalSkills(
            programming_languages=["Python"],
            frameworks=[],
            tools=[],
            databases=[],
            cloud_technologies=[],
            ai_ml_skills=[],
            genai_skills=[],
        ),
        projects=[],
        experience=[],
        certifications=[],
        achievements=[],
        soft_skills=[],
    )


def _fake_jd_extraction(job_title: str = "Software Engineer") -> JobExtraction:
    return JobExtraction(
        job_title=job_title,
        required_skills=["Python"],
        preferred_skills=[],
        programming_languages=["Python"],
        frameworks=[],
        tools=[],
        ai_ml_technologies=[],
        genai_technologies=[],
        cloud_requirements=[],
        database_requirements=[],
        experience_requirements=None,
        education_requirements=None,
        responsibilities=[],
        keywords=["Python"],
        domain=None,
        seniority_level=None,
    )


def _fake_skill_gap() -> SkillGapResult:
    return SkillGapResult(
        matching_skills=["Python"],
        partially_matching_skills=[],
        transferable_skills=[],
        missing_skills=[],
    )


def _fake_ats_result() -> ATSAnalysisResult:
    return ATSAnalysisResult(
        ats_score=80,
        score_explanation="Good keyword coverage.",
        keyword_coverage=KeywordCoverage(
            matched_keywords=["Python"], missing_keywords=[]
        ),
        section_structure_issues=[],
        formatting_issues=[],
        job_title_alignment_note=None,
        improvement_suggestions=[],
        methodology_note="placeholder - overwritten by agent code",
    )


def _fake_experience_result() -> ExperienceAnalysisResult:
    return ExperienceAnalysisResult(
        overall_relevance_summary="Strong fit.",
        project_relevance=[],
        technical_depth_assessment="Solid depth.",
        quantifiable_achievements_found=[],
        missing_evidence=[],
        weak_descriptions=[],
        improvement_suggestions=[],
    )


def _fake_recommendation_result() -> RecommendationResult:
    return RecommendationResult(
        skills_to_learn=[],
        technologies_to_practice=[],
        project_ideas=[],
        resume_improvements=[],
        relevant_certifications=[],
        interview_prep_focus_areas=[],
        short_term_roadmap=[],
    )


def _fake_interview_result() -> InterviewPrepResult:
    return InterviewPrepResult(questions=[])


def _patch_all_providers():
    return (patch(p) for p in ALL_AGENT_PATCHES)


def test_graph_runs_all_eight_nodes_and_merges_state() -> None:
    with (
        patch(ALL_AGENT_PATCHES[0]) as mock_resume,
        patch(ALL_AGENT_PATCHES[1]) as mock_jd,
        patch(ALL_AGENT_PATCHES[2]) as mock_skill_gap,
        patch(ALL_AGENT_PATCHES[3]) as mock_ats,
        patch(ALL_AGENT_PATCHES[4]) as mock_experience,
        patch(ALL_AGENT_PATCHES[5]) as mock_matching,
        patch(ALL_AGENT_PATCHES[6]) as mock_recommendation,
        patch(ALL_AGENT_PATCHES[7]) as mock_interview,
    ):
        mock_resume.return_value.generate_structured.return_value = (
            _fake_resume_extraction()
        )
        mock_jd.return_value.generate_structured.return_value = _fake_jd_extraction()
        mock_skill_gap.return_value.generate_structured.return_value = (
            _fake_skill_gap()
        )
        mock_ats.return_value.generate_structured.return_value = _fake_ats_result()
        mock_experience.return_value.generate_structured.return_value = (
            _fake_experience_result()
        )
        mock_matching.return_value.generate_structured.return_value = (
            MatchNarrative(narrative_summary="Strong overall match.")
        )
        mock_recommendation.return_value.generate_structured.return_value = (
            _fake_recommendation_result()
        )
        mock_interview.return_value.generate_structured.return_value = (
            _fake_interview_result()
        )

        graph = build_analysis_graph()
        initial_state = AnalysisState(
            analysis_id="test-123",
            resume_raw_text="Jane Doe, Software Engineer with Python experience.",
            jd_raw_text="We are hiring a Software Engineer with Python skills.",
        )
        result = graph.invoke(initial_state)

    assert result.get("resume_extraction").name == "Jane Doe"
    assert result.get("jd_extraction").job_title == "Software Engineer"
    assert result.get("skill_gap_result").matching_skills == ["Python"]
    assert result.get("ats_result").ats_score == 80
    assert result.get("experience_result").overall_relevance_summary == "Strong fit."
    assert result.get("matching_result") is not None
    assert result.get("recommendation_result") is not None
    assert result.get("interview_result") is not None
    assert result.get("errors", []) == []


def test_downstream_agents_skip_and_record_errors_when_resume_agent_fails() -> None:
    """
    When Resume Agent fails, every downstream node (skill_gap,
    ats_analysis, experience_analysis, matching, recommendation,
    interview_prep) should detect the missing data and record its own
    error WITHOUT calling its own LLM - no wasted API calls on a request
    that can't succeed.
    """
    from app.services.llm.base import LLMGenerationError

    with (
        patch(ALL_AGENT_PATCHES[0]) as mock_resume,
        patch(ALL_AGENT_PATCHES[1]) as mock_jd,
        patch(ALL_AGENT_PATCHES[2]) as mock_skill_gap,
        patch(ALL_AGENT_PATCHES[3]) as mock_ats,
        patch(ALL_AGENT_PATCHES[4]) as mock_experience,
        patch(ALL_AGENT_PATCHES[5]) as mock_matching,
        patch(ALL_AGENT_PATCHES[6]) as mock_recommendation,
        patch(ALL_AGENT_PATCHES[7]) as mock_interview,
    ):
        mock_resume.return_value.generate_structured.side_effect = (
            LLMGenerationError("model returned malformed JSON")
        )
        mock_jd.return_value.generate_structured.return_value = _fake_jd_extraction(
            "Data Scientist"
        )

        graph = build_analysis_graph()
        initial_state = AnalysisState(
            analysis_id="test-456",
            resume_raw_text="some resume text",
            jd_raw_text="some JD text",
        )
        result = graph.invoke(initial_state)

    assert result.get("resume_extraction") is None
    assert result.get("jd_extraction").job_title == "Data Scientist"
    assert result.get("skill_gap_result") is None
    assert result.get("ats_result") is None
    assert result.get("experience_result") is None
    assert result.get("matching_result") is None
    assert result.get("recommendation_result") is None
    assert result.get("interview_result") is None

    mock_skill_gap.return_value.generate_structured.assert_not_called()
    mock_ats.return_value.generate_structured.assert_not_called()
    mock_experience.return_value.generate_structured.assert_not_called()
    mock_matching.return_value.generate_structured.assert_not_called()
    mock_recommendation.return_value.generate_structured.assert_not_called()
    mock_interview.return_value.generate_structured.assert_not_called()

    errors = result.get("errors", [])
    error_agents = {err.agent for err in errors}
    assert "resume_analyzer" in error_agents
    assert "skill_gap" in error_agents
    assert "ats_analysis" in error_agents
    assert "experience_analysis" in error_agents
    assert "matching" in error_agents
    assert "recommendation" in error_agents
    assert "interview_prep" in error_agents


def test_matching_narrative_failure_does_not_block_recommendation_or_interview() -> None:
    """
    If the Matching Agent's narrative LLM call fails, it still returns a
    full, valid MatchingResult (fallback narrative + soft error).
    Recommendation and Interview Prep both depend on resume/jd/skill_gap,
    not on matching_result's narrative specifically, so both should still
    run normally.
    """
    from app.services.llm.base import LLMGenerationError

    with (
        patch(ALL_AGENT_PATCHES[0]) as mock_resume,
        patch(ALL_AGENT_PATCHES[1]) as mock_jd,
        patch(ALL_AGENT_PATCHES[2]) as mock_skill_gap,
        patch(ALL_AGENT_PATCHES[3]) as mock_ats,
        patch(ALL_AGENT_PATCHES[4]) as mock_experience,
        patch(ALL_AGENT_PATCHES[5]) as mock_matching,
        patch(ALL_AGENT_PATCHES[6]) as mock_recommendation,
        patch(ALL_AGENT_PATCHES[7]) as mock_interview,
    ):
        mock_resume.return_value.generate_structured.return_value = (
            _fake_resume_extraction()
        )
        mock_jd.return_value.generate_structured.return_value = _fake_jd_extraction()
        mock_skill_gap.return_value.generate_structured.return_value = (
            _fake_skill_gap()
        )
        mock_ats.return_value.generate_structured.return_value = _fake_ats_result()
        mock_experience.return_value.generate_structured.return_value = (
            _fake_experience_result()
        )
        mock_matching.return_value.generate_structured.side_effect = (
            LLMGenerationError("narrative generation failed")
        )
        mock_recommendation.return_value.generate_structured.return_value = (
            _fake_recommendation_result()
        )
        mock_interview.return_value.generate_structured.return_value = (
            _fake_interview_result()
        )

        graph = build_analysis_graph()
        initial_state = AnalysisState(
            analysis_id="test-789",
            resume_raw_text="Jane Doe resume text",
            jd_raw_text="Software Engineer JD text",
        )
        result = graph.invoke(initial_state)

    matching_result = result.get("matching_result")
    assert matching_result is not None
    assert "Overall match score" in matching_result.narrative_summary
    assert result.get("recommendation_result") is not None
    assert result.get("interview_result") is not None

    errors = result.get("errors", [])
    error_agents = {err.agent for err in errors}
    assert "matching" in error_agents
    assert "recommendation" not in error_agents
    assert "interview_prep" not in error_agents
