"""Tests for the resume optimization API."""

import uuid
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.db.session import get_db
from app.models.optimization import OptimizationResultRecord
from app.schemas.optimization import OptimizationResult
from app.services.llm.base import LLMGenerationError

client = TestClient(app)

RESUME_ID = uuid.uuid4()
JOB_ID = uuid.uuid4()


class _FakeQuery:
    def __init__(self, db, model):
        self.db = db
        self.model = model
        self._filters: dict = {}

    def filter_by(self, **kwargs):
        self._filters = kwargs
        return self

    def one_or_none(self):
        if self.model is not OptimizationResultRecord:
            return None
        candidates = list(self.db.added_records)
        if self.db.optimization_record is not None:
            candidates.append(self.db.optimization_record)
        for record in candidates:
            if (
                record.resume_id == self._filters.get("resume_id")
                and record.job_description_id == self._filters.get("job_description_id")
            ):
                return record
        return None


class FakeDB:
    """Minimal database-session fake for endpoint tests."""

    def __init__(self, resume=None, job=None, optimization_record=None):
        self.resume = resume
        self.job = job
        self.optimization_record = optimization_record
        self.added_records: list = []
        self.committed = False

    def get(self, model, record_id):
        from app.models.job_description import JobDescription
        from app.models.resume import Resume

        if model is Resume:
            return self.resume if record_id == RESUME_ID else None

        if model is JobDescription:
            return self.job if record_id == JOB_ID else None

        return None

    def add(self, obj):
        self.added_records.append(obj)

    def commit(self):
        self.committed = True

    def query(self, model):
        return _FakeQuery(self, model)


def make_resume():
    return SimpleNamespace(
        id=RESUME_ID,
        raw_text="Built a Python project using OpenCV.",
    )


def make_job():
    return SimpleNamespace(
        id=JOB_ID,
        raw_text="Seeking Python and OpenCV experience.",
    )


def make_result():
    return OptimizationResult(
        summary="Improve project wording and job keyword alignment.",
        suggestions=[
            {
                "section": "Projects",
                "original_text": "Built a Python project using OpenCV.",
                "suggested_text": (
                    "Developed a Python-based project using OpenCV."
                ),
                "reason": "Uses clearer action-oriented wording.",
                "supporting_evidence": (
                    "The job description requests Python and OpenCV."
                ),
                "keywords": ["Python", "OpenCV"],
                "priority": "high",
            }
        ],
        missing_information=[],
        warnings=[],
    )


def override_db(db):
    def _get_db():
        yield db

    app.dependency_overrides[get_db] = _get_db


def teardown_function():
    app.dependency_overrides.clear()


def test_optimization_success():
    override_db(FakeDB(make_resume(), make_job()))

    with patch(
        "app.api.routes.optimization.optimize_resume",
        return_value=make_result(),
    ) as mock_optimize:
        response = client.post(
            "/api/optimization",
            json={
                "resume_id": str(RESUME_ID),
                "job_description_id": str(JOB_ID),
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["resume_id"] == str(RESUME_ID)
    assert body["job_description_id"] == str(JOB_ID)
    assert body["result"]["suggestions"][0]["keywords"] == [
        "Python",
        "OpenCV",
    ]
    mock_optimize.assert_called_once_with(
        resume_text="Built a Python project using OpenCV.",
        job_description_text="Seeking Python and OpenCV experience.",
    )


def test_optimization_returns_404_when_resume_is_missing():
    override_db(FakeDB(resume=None, job=make_job()))

    response = client.post(
        "/api/optimization",
        json={
            "resume_id": str(RESUME_ID),
            "job_description_id": str(JOB_ID),
        },
    )

    assert response.status_code == 404
    assert "Resume" in response.json()["detail"]


def test_optimization_returns_404_when_job_is_missing():
    override_db(FakeDB(resume=make_resume(), job=None))

    response = client.post(
        "/api/optimization",
        json={
            "resume_id": str(RESUME_ID),
            "job_description_id": str(JOB_ID),
        },
    )

    assert response.status_code == 404
    assert "Job description" in response.json()["detail"]


def test_optimization_returns_502_when_llm_fails():
    override_db(FakeDB(make_resume(), make_job()))

    with patch(
        "app.api.routes.optimization.optimize_resume",
        side_effect=LLMGenerationError("simulated provider failure"),
    ):
        response = client.post(
            "/api/optimization",
            json={
                "resume_id": str(RESUME_ID),
                "job_description_id": str(JOB_ID),
            },
        )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "Resume optimization could not be generated. Please try again."
    )
    assert "simulated provider failure" not in response.text


def test_optimization_rejects_invalid_uuid():
    response = client.post(
        "/api/optimization",
        json={
            "resume_id": "not-a-uuid",
            "job_description_id": str(JOB_ID),
        },
    )

    assert response.status_code == 422


def test_optimization_persists_new_result():
    fake_db = FakeDB(make_resume(), make_job())
    override_db(fake_db)

    with patch(
        "app.api.routes.optimization.optimize_resume",
        return_value=make_result(),
    ):
        response = client.post(
            "/api/optimization",
            json={
                "resume_id": str(RESUME_ID),
                "job_description_id": str(JOB_ID),
            },
        )

    assert response.status_code == 200
    assert fake_db.committed is True
    assert len(fake_db.added_records) == 1
    stored = fake_db.added_records[0]
    assert stored.resume_id == RESUME_ID
    assert stored.job_description_id == JOB_ID
    assert stored.data["summary"] == "Improve project wording and job keyword alignment."


def test_optimization_upserts_existing_result_instead_of_duplicating():
    existing_record = OptimizationResultRecord(
        id=uuid.uuid4(),
        resume_id=RESUME_ID,
        job_description_id=JOB_ID,
        data={"summary": "stale previous result", "suggestions": [], "missing_information": [], "warnings": []},
    )
    fake_db = FakeDB(make_resume(), make_job(), optimization_record=existing_record)
    override_db(fake_db)

    with patch(
        "app.api.routes.optimization.optimize_resume",
        return_value=make_result(),
    ):
        response = client.post(
            "/api/optimization",
            json={
                "resume_id": str(RESUME_ID),
                "job_description_id": str(JOB_ID),
            },
        )

    assert response.status_code == 200
    # No new record added - the existing one was updated in place.
    assert len(fake_db.added_records) == 0
    assert existing_record.data["summary"] == "Improve project wording and job keyword alignment."


def test_get_optimization_returns_persisted_result():
    existing_record = OptimizationResultRecord(
        id=uuid.uuid4(),
        resume_id=RESUME_ID,
        job_description_id=JOB_ID,
        data=make_result().model_dump(mode="json"),
    )
    override_db(FakeDB(optimization_record=existing_record))

    response = client.get(f"/api/optimization/{RESUME_ID}/{JOB_ID}")

    assert response.status_code == 200
    body = response.json()
    assert body["result"]["summary"] == "Improve project wording and job keyword alignment."


def test_get_optimization_returns_404_when_not_found():
    override_db(FakeDB())

    response = client.get(f"/api/optimization/{RESUME_ID}/{JOB_ID}")

    assert response.status_code == 404