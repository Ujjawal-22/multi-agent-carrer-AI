"""
Job description endpoints: paste text or upload a file.
"""

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import (
    EmptyDocumentError,
    ExtractionFailedError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from app.db.session import get_db
from app.models.job_description import JobDescription
from app.schemas.job_description import JobDescriptionCreate, JobDescriptionResponse
from app.services.document_processing import (
    extract_text_from_upload,
    sanitize_filename,
    validate_extracted_text,
    validate_upload,
)

router = APIRouter(prefix="/api/jobs", tags=["jobs"])
settings = get_settings()


@router.post(
    "",
    response_model=JobDescriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_job_from_text(
    payload: JobDescriptionCreate,
    db: Session = Depends(get_db),
) -> JobDescriptionResponse:
    job = JobDescription(
        id=uuid.uuid4(),
        title=payload.title,
        raw_text=payload.text,
        source="paste",
        char_count=len(payload.text),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return JobDescriptionResponse.model_validate(job)


@router.post(
    "/upload",
    response_model=JobDescriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_job_from_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> JobDescriptionResponse:
    contents = await file.read()

    try:
        validate_upload(file.filename or "", contents)
    except UnsupportedFileTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(exc)
        ) from exc
    except FileTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc)
        ) from exc
    except EmptyDocumentError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    safe_filename = sanitize_filename(file.filename or "job_description")

    try:
        raw_text, _ = extract_text_from_upload(safe_filename, contents)
        validate_extracted_text(raw_text)
    except (ExtractionFailedError, EmptyDocumentError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    job = JobDescription(
        id=uuid.uuid4(),
        title=None,
        raw_text=raw_text,
        source="upload",
        char_count=len(raw_text),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return JobDescriptionResponse.model_validate(job)
