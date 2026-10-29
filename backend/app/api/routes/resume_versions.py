
"""API endpoints for managing saved tailored resume versions."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.job_description import JobDescription
from app.models.resume import Resume
from app.services.resume_pdf import generate_resume_pdf
from app.models.resume_version import ResumeVersion
from app.schemas.optimization import (
    ResumeVersionCreate,
    ResumeVersionListResponse,
    ResumeVersionRename,
    ResumeVersionResponse,
)

router = APIRouter(
    prefix="/api/resume-versions",
    tags=["resume-versions"],
)


@router.post(
    "",
    response_model=ResumeVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_resume_version(
    payload: ResumeVersionCreate,
    db: Session = Depends(get_db),
) -> ResumeVersionResponse:
    """Save a new tailored resume version."""

    resume = db.get(Resume, payload.resume_id)
    if resume is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found.",
        )

    job = db.get(JobDescription, payload.job_description_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job description not found.",
        )

    name = payload.name.strip()
    tailored_text = payload.tailored_text.strip()

    if not name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Version name cannot be blank.",
        )

    if not tailored_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Tailored resume text cannot be blank.",
        )

    version = ResumeVersion(
        id=uuid.uuid4(),
        resume_id=resume.id,
        job_description_id=job.id,
        name=name,
        tailored_text=tailored_text,
    )

    try:
        db.add(version)
        db.commit()
        db.refresh(version)
    except Exception:
        db.rollback()
        raise

    return ResumeVersionResponse.model_validate(version)


@router.get(
    "",
    response_model=ResumeVersionListResponse,
)
def list_resume_versions(
    resume_id: uuid.UUID,
    job_description_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> ResumeVersionListResponse:
    """List saved versions for a resume and job description."""

    # Fetch versions matching both IDs.
    versions = (
        db.query(ResumeVersion)
        .filter(
            ResumeVersion.resume_id == resume_id,
            ResumeVersion.job_description_id == job_description_id,
        )
        .order_by(
            ResumeVersion.created_at.desc(),
            ResumeVersion.id.desc(),
        )
        .all()
    )

    return ResumeVersionListResponse(
        versions=[
            ResumeVersionResponse.model_validate(version)
            for version in versions
        ],
        total=len(versions),
    )


@router.get(
    "/{version_id}",
    response_model=ResumeVersionResponse,
)
def get_resume_version(
    version_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> ResumeVersionResponse:
    """Retrieve one saved version."""

    version = db.get(ResumeVersion, version_id)

    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume version not found.",
        )

    return ResumeVersionResponse.model_validate(version)


@router.patch(
    "/{version_id}",
    response_model=ResumeVersionResponse,
)
def rename_resume_version(
    version_id: uuid.UUID,
    payload: ResumeVersionRename,
    db: Session = Depends(get_db),
) -> ResumeVersionResponse:
    """Rename a saved version without changing its contents."""

    version = db.get(ResumeVersion, version_id)

    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume version not found.",
        )

    name = payload.name.strip()

    if not name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Version name cannot be blank.",
        )

    version.name = name

    try:
        db.commit()
        db.refresh(version)
    except Exception:
        db.rollback()
        raise

    return ResumeVersionResponse.model_validate(version)


@router.delete(
    "/{version_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_resume_version(
    version_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> Response:
    """Delete a saved version."""

    version = db.get(ResumeVersion, version_id)

    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume version not found.",
        )

    try:
        db.delete(version)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get(
    "/{version_id}/pdf",
    response_class=Response,
)
def download_resume_version_pdf(
    version_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> Response:
    """Download a PDF generated from a saved tailored resume version."""

    version = db.get(ResumeVersion, version_id)

    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume version not found.",
        )

    try:
        pdf_bytes = generate_resume_pdf(version.tailored_text)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    safe_name = "".join(
        character if character.isalnum() or character in "-_" else "_"
        for character in version.name
    ).strip("_")

    filename = f"{safe_name or 'tailored_resume'}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            )
        },
    )
