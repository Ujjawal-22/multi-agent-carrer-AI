"""
Unit tests for the deterministic matching formulas in matching_scorer.py.
No LLM, no mocking - these are pure functions over structured data, which
is exactly the point of keeping the scoring logic deterministic.
"""

from app.core.config import Settings
from app.schemas.ats_analysis import ATSAnalysisResult, KeywordCoverage
from app.schemas.experience_analysis import ExperienceAnalysisResult, ProjectRelevance
from app.schemas.job_extraction import JobExtraction
from app.schemas.resume_extraction import Education, ResumeExtraction, TechnicalSkills
from app.schemas.skill_gap import MissingSkill, SkillGapResult
from app.services.matching_scorer import compute_matching_scores


def _empty_technical_skills() -> TechnicalSkills:
    return TechnicalSkills(
        programming_languages=[],
        frameworks=[],
        tools=[],
        databases=[],
        cloud_technologies=[],
        ai_ml_skills=[],
        genai_skills=[],
    )


def test_technical_skill_match_all_matching_scores_100() -> None:
    skill_gap = SkillGapResult(
        matching_skills=["Python", "SQL"],
        partially_matching_skills=[],
        transferable_skills=[],
        missing_skills=[],
    )
    resume = ResumeExtraction(
        name=None,
        email=None,
        phone=None,
        education=[],
        technical_skills=_empty_technical_skills(),
        projects=[],
        experience=[],
        certifications=[],
        achievements=[],
        soft_skills=[],
    )
    jd = JobExtraction(
        job_title=None,
        required_skills=[],
        preferred_skills=[],
        programming_languages=[],
        frameworks=[],
        tools=[],
        ai_ml_technologies=[],
        genai_technologies=[],
        cloud_requirements=[],
        database_requirements=[],
        experience_requirements=None,
        education_requirements=None,
        responsibilities=[],
        keywords=[],
        domain=None,
        seniority_level=None,
    )
    ats = ATSAnalysisResult(
        ats_score=90,
        score_explanation="x",
        keyword_coverage=KeywordCoverage(matched_keywords=[], missing_keywords=[]),
        section_structure_issues=[],
        formatting_issues=[],
        job_title_alignment_note=None,
        improvement_suggestions=[],
        methodology_note="x",
    )
    experience = ExperienceAnalysisResult(
        overall_relevance_summary="x",
        project_relevance=[],
        technical_depth_assessment="x",
        quantifiable_achievements_found=[],
        missing_evidence=[],
        weak_descriptions=[],
        improvement_suggestions=[],
    )

    overall, sub_scores, weights = compute_matching_scores(
        resume=resume,
        jd_extraction=jd,
        resume_raw_text="",
        skill_gap=skill_gap,
        ats_result=ats,
        experience_result=experience,
        settings=Settings(),
    )

    assert sub_scores.technical_skill_match == 100.0
    # ats_keyword_match should reuse the ATS score directly
    assert sub_scores.ats_keyword_match == 90.0
    # No projects -> neutral 50 for experience_project_match
    assert sub_scores.experience_project_match == 50.0
    # No education/domain requirements stated -> trivially satisfied (100)
    assert sub_scores.education_match == 100.0
    assert sub_scores.domain_match == 100.0
    # Weights should normalize to sum to 1.0
    assert abs(sum(weights.model_dump().values()) - 1.0) < 1e-6


def test_technical_skill_match_with_partial_and_missing() -> None:
    skill_gap = SkillGapResult(
        matching_skills=["Python"],
        partially_matching_skills=["SQL"],
        transferable_skills=[],
        missing_skills=[
            MissingSkill(
                skill_name="LangChain",
                importance="critical",
                reason="required",
                suggested_learning_priority="high",
            )
        ],
    )
    # matching=1, partial=1 (0.5 credit), missing=1 -> total=3
    # weighted_have = 1 + 0.5 = 1.5 -> 1.5/3 * 100 = 50.0
    from app.services.matching_scorer import _technical_skill_match

    assert _technical_skill_match(skill_gap) == 50.0


def test_experience_project_match_averages_relevance() -> None:
    experience = ExperienceAnalysisResult(
        overall_relevance_summary="x",
        project_relevance=[
            ProjectRelevance(
                project_name="A",
                relevance_to_role="high",
                relevant_technologies=[],
                notes="x",
            ),
            ProjectRelevance(
                project_name="B",
                relevance_to_role="low",
                relevant_technologies=[],
                notes="x",
            ),
        ],
        technical_depth_assessment="x",
        quantifiable_achievements_found=[],
        missing_evidence=[],
        weak_descriptions=[],
        improvement_suggestions=[],
    )
    from app.services.matching_scorer import _experience_project_match

    # high=100, low=20 -> average 60
    assert _experience_project_match(experience) == 60.0


def test_education_match_exact_degree_overlap_scores_100() -> None:
    resume = ResumeExtraction(
        name=None,
        email=None,
        phone=None,
        education=[
            Education(
                degree="B.Tech",
                field_of_study="Computer Science",
                university=None,
                graduation_year=None,
            )
        ],
        technical_skills=_empty_technical_skills(),
        projects=[],
        experience=[],
        certifications=[],
        achievements=[],
        soft_skills=[],
    )
    jd = JobExtraction(
        job_title=None,
        required_skills=[],
        preferred_skills=[],
        programming_languages=[],
        frameworks=[],
        tools=[],
        ai_ml_technologies=[],
        genai_technologies=[],
        cloud_requirements=[],
        database_requirements=[],
        experience_requirements=None,
        education_requirements="Bachelor's degree in Computer Science required",
        responsibilities=[],
        keywords=[],
        domain=None,
        seniority_level=None,
    )
    from app.services.matching_scorer import _education_match

    assert _education_match(resume, jd) == 100.0
