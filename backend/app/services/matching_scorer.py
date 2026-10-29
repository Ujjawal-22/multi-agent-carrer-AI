"""
Deterministic match scoring.

Zero LLM calls in this entire module — every sub-score is a plain
computation over already-structured data from earlier agents. This is a
deliberate design choice: the spec requires the match score to be
"explainable" and follow a "clearly defined methodology," which a formula
satisfies far better than asking an LLM to invent a number. Being able to
point at this file and say "here is the exact formula" is the point.

Honesty note: education_match and domain_match use shallow keyword-overlap
heuristics, not real semantic understanding. This is documented in
MATCHING_METHODOLOGY_NOTE and reflected in their low default weights —
we're not overselling what a substring check can tell you.
"""

from app.core.config import Settings
from app.schemas.ats_analysis import ATSAnalysisResult
from app.schemas.experience_analysis import ExperienceAnalysisResult
from app.schemas.job_extraction import JobExtraction
from app.schemas.resume_extraction import ResumeExtraction
from app.schemas.skill_gap import SkillGapResult
from app.schemas.matching import SubScoreBreakdown

_RELEVANCE_SCORES = {"high": 100.0, "medium": 60.0, "low": 20.0}


def _technical_skill_match(skill_gap: SkillGapResult) -> float:
    matching = len(skill_gap.matching_skills)
    partial = len(skill_gap.partially_matching_skills)
    missing = len(skill_gap.missing_skills)

    total_considered = matching + partial + missing
    if total_considered == 0:
        return 50.0  # no signal either way; neutral, not zero

    weighted_have = matching + (partial * 0.5)
    return round((weighted_have / total_considered) * 100, 1)


def _ats_keyword_match(ats_result: ATSAnalysisResult) -> float:
    # Reuse the ATS Agent's own score directly rather than recomputing
    # keyword coverage a second time — it's already the right measurement.
    return float(ats_result.ats_score)


def _experience_project_match(experience_result: ExperienceAnalysisResult) -> float:
    relevances = experience_result.project_relevance
    if not relevances:
        return 50.0  # no projects to assess; neutral

    scores = [_RELEVANCE_SCORES.get(p.relevance_to_role, 50.0) for p in relevances]
    return round(sum(scores) / len(scores), 1)


def _education_match(
    resume: ResumeExtraction, jd_extraction: JobExtraction
) -> float:
    requirement = jd_extraction.education_requirements
    if not requirement or not requirement.strip():
        return 100.0  # JD stated no specific requirement; trivially satisfied

    requirement_lower = requirement.lower()
    for edu in resume.education:
        candidate_terms = [edu.degree, edu.field_of_study]
        for term in candidate_terms:
            if term and term.lower() in requirement_lower:
                return 100.0
            if term:
                # Loose word-level overlap as a fallback for phrasing
                # differences (e.g. "B.Tech" vs "Bachelor's degree").
                term_words = set(term.lower().split())
                requirement_words = set(requirement_lower.split())
                if term_words & requirement_words:
                    return 70.0

    # A stated requirement exists but no overlap was found. This is a weak
    # heuristic, so we don't score this as a hard 0 — a real mismatch is
    # possible, but so is a phrasing difference our substring check missed.
    return 40.0


def _domain_match(resume_raw_text: str, jd_extraction: JobExtraction) -> float:
    domain = jd_extraction.domain
    if not domain or not domain.strip():
        return 100.0  # JD stated no specific domain; trivially satisfied

    domain_words = [w.lower() for w in domain.split() if len(w) > 2]
    resume_lower = resume_raw_text.lower()

    if any(word in resume_lower for word in domain_words):
        return 100.0

    # Weak signal either way — neutral rather than penalizing on a
    # heuristic this shallow.
    return 50.0


def compute_matching_scores(
    *,
    resume: ResumeExtraction,
    jd_extraction: JobExtraction,
    resume_raw_text: str,
    skill_gap: SkillGapResult,
    ats_result: ATSAnalysisResult,
    experience_result: ExperienceAnalysisResult,
    settings: Settings,
) -> tuple[float, SubScoreBreakdown, SubScoreBreakdown]:
    """
    Returns (overall_match_score, sub_scores, normalized_weights_used).
    """
    sub_scores = SubScoreBreakdown(
        technical_skill_match=_technical_skill_match(skill_gap),
        ats_keyword_match=_ats_keyword_match(ats_result),
        experience_project_match=_experience_project_match(experience_result),
        education_match=_education_match(resume, jd_extraction),
        domain_match=_domain_match(resume_raw_text, jd_extraction),
    )

    raw_weights = {
        "technical_skill_match": settings.MATCH_WEIGHT_TECHNICAL_SKILL,
        "ats_keyword_match": settings.MATCH_WEIGHT_ATS_KEYWORD,
        "experience_project_match": settings.MATCH_WEIGHT_EXPERIENCE_PROJECT,
        "education_match": settings.MATCH_WEIGHT_EDUCATION,
        "domain_match": settings.MATCH_WEIGHT_DOMAIN,
    }
    total_weight = sum(raw_weights.values())
    if total_weight <= 0:
        # Defensive fallback if weights are misconfigured to all-zero —
        # fall back to equal weighting rather than dividing by zero.
        normalized = {k: 1.0 / len(raw_weights) for k in raw_weights}
    else:
        normalized = {k: v / total_weight for k, v in raw_weights.items()}

    weights_used = SubScoreBreakdown(**normalized)

    overall = sum(
        getattr(sub_scores, key) * normalized[key] for key in normalized
    )

    return round(overall, 1), sub_scores, weights_used
