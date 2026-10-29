"""
Background analysis runner.

Runs the LangGraph pipeline via graph.stream(..., stream_mode="values")
rather than graph.invoke(), so we can persist GENUINE per-node progress to
the database as the pipeline actually executes - not a simulated/animated
progress indicator. stream_mode="values" yields the full merged state
after each step completes, which is simpler to work with than the
"updates" mode (which yields only partial per-node diffs and would
require re-implementing LangGraph's own reducer merging logic ourselves).

Runs inside a FastAPI BackgroundTasks callback, so it opens and manages
its own DB session rather than reusing the original request's session
(which is closed by the time this callback actually executes).

Scope note: this streams and persists the `current_step` LABEL live, but
the actual structured agent results (resume_extraction, skill_gap_result,
etc.) are still persisted as one atomic batch at the very end, once the
full pipeline completes - not incrementally per node. This was a
deliberate scope decision: live step labels give the frontend genuine
progress feedback without requiring a larger refactor to incrementally
commit each agent's structured output mid-run.
"""

import logging
import uuid
from datetime import datetime, timezone

from app.agents.orchestrator import analysis_graph
from app.agents.state import AnalysisState
from app.db.session import SessionLocal
from app.models.analysis import (
    Analysis,
    ATSAnalysisRecord,
    ExperienceAnalysisRecord,
    InterviewQuestionRecord,
    JobExtractionRecord,
    MatchingResultRecord,
    RecommendationRecord,
    ResumeExtractionRecord,
    SkillGapRecord,
)

logger = logging.getLogger(__name__)

# Maps a state field name to a human-readable progress label. Only fields
# in this mapping are watched for "just became populated" transitions.
_STEP_LABELS = {
    "resume_extraction": "Analyzing resume",
    "jd_extraction": "Analyzing job description",
    "skill_gap_result": "Computing skill gap",
    "ats_result": "Running ATS analysis",
    "experience_result": "Analyzing experience & projects",
    "matching_result": "Calculating match score",
    "recommendation_result": "Generating recommendations",
    "interview_result": "Generating interview questions",
}

_TRACKED_FIELDS = tuple(_STEP_LABELS.keys())


def _update_current_step(db, analysis_id: uuid.UUID, step_label: str) -> None:
    analysis = db.get(Analysis, analysis_id)
    if analysis is not None:
        analysis.current_step = step_label
        db.commit()


def run_analysis_in_background(
    analysis_id: uuid.UUID,
    resume_raw_text: str,
    jd_raw_text: str,
) -> None:
    db = SessionLocal()
    try:
        initial_state = AnalysisState(
            analysis_id=str(analysis_id),
            resume_raw_text=resume_raw_text,
            jd_raw_text=jd_raw_text,
        )

        previous_state: dict = initial_state.model_dump()
        final_state: dict = previous_state

        _update_current_step(db, analysis_id, "Starting analysis")

        for state_snapshot in analysis_graph.stream(
            initial_state, stream_mode="values"
        ):
            newly_populated = [
                field
                for field in _TRACKED_FIELDS
                if state_snapshot.get(field) is not None
                and previous_state.get(field) is None
            ]
            if newly_populated:
                # Nodes that completed in the same step (e.g. Resume + JD
                # running in parallel) are joined into one label, so
                # genuine simultaneous completion is shown as such, not
                # hidden behind an arbitrary single label.
                label = " + ".join(_STEP_LABELS[f] for f in newly_populated)
                logger.info("Analysis %s progress: %s", analysis_id, label)
                _update_current_step(db, analysis_id, label)

            previous_state = state_snapshot
            final_state = state_snapshot

        _persist_results(db, analysis_id, final_state)

    except Exception as exc:  # noqa: BLE001
        # A truly unexpected failure (not an individual agent's handled
        # error, which already shows up in final_state["errors"]) - e.g.
        # a bug in the graph itself, or the DB going away mid-run.
        logger.exception(
            "Analysis %s failed with an unhandled error", analysis_id
        )
        analysis = db.get(Analysis, analysis_id)
        if analysis is not None:
            analysis.status = "failed"
            analysis.current_step = f"Failed: {exc}"
            analysis.completed_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()


def _persist_results(db, analysis_id: uuid.UUID, final_state: dict) -> None:
    analysis = db.get(Analysis, analysis_id)
    if analysis is None:
        return

    resume_extraction = final_state.get("resume_extraction")
    jd_extraction = final_state.get("jd_extraction")
    skill_gap_result = final_state.get("skill_gap_result")
    ats_result = final_state.get("ats_result")
    experience_result = final_state.get("experience_result")
    matching_result = final_state.get("matching_result")
    recommendation_result = final_state.get("recommendation_result")
    interview_result = final_state.get("interview_result")
    errors = final_state.get("errors", [])

    if resume_extraction is not None:
        existing = (
            db.query(ResumeExtractionRecord)
            .filter_by(resume_id=analysis.resume_id)
            .one_or_none()
        )
        if existing is not None:
            existing.data = resume_extraction.model_dump(mode="json")
        else:
            db.add(
                ResumeExtractionRecord(
                    id=uuid.uuid4(),
                    resume_id=analysis.resume_id,
                    data=resume_extraction.model_dump(mode="json"),
                )
            )

    if jd_extraction is not None:
        existing = (
            db.query(JobExtractionRecord)
            .filter_by(job_description_id=analysis.job_description_id)
            .one_or_none()
        )
        if existing is not None:
            existing.data = jd_extraction.model_dump(mode="json")
        else:
            db.add(
                JobExtractionRecord(
                    id=uuid.uuid4(),
                    job_description_id=analysis.job_description_id,
                    data=jd_extraction.model_dump(mode="json"),
                )
            )

    if skill_gap_result is not None:
        db.add(
            SkillGapRecord(
                id=uuid.uuid4(),
                analysis_id=analysis.id,
                data=skill_gap_result.model_dump(mode="json"),
            )
        )

    if ats_result is not None:
        db.add(
            ATSAnalysisRecord(
                id=uuid.uuid4(),
                analysis_id=analysis.id,
                data=ats_result.model_dump(mode="json"),
            )
        )

    if experience_result is not None:
        db.add(
            ExperienceAnalysisRecord(
                id=uuid.uuid4(),
                analysis_id=analysis.id,
                data=experience_result.model_dump(mode="json"),
            )
        )

    if matching_result is not None:
        db.add(
            MatchingResultRecord(
                id=uuid.uuid4(),
                analysis_id=analysis.id,
                data=matching_result.model_dump(mode="json"),
            )
        )

    if recommendation_result is not None:
        db.add(
            RecommendationRecord(
                id=uuid.uuid4(),
                analysis_id=analysis.id,
                data=recommendation_result.model_dump(mode="json"),
            )
        )

    if interview_result is not None:
        db.add(
            InterviewQuestionRecord(
                id=uuid.uuid4(),
                analysis_id=analysis.id,
                data=interview_result.model_dump(mode="json"),
            )
        )

    analysis.status = "completed" if not errors else "failed"
    analysis.current_step = "Completed" if not errors else "Completed with errors"
    analysis.completed_at = datetime.now(timezone.utc)
    db.commit()
