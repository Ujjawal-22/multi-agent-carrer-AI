"""
Resume upload endpoint.
"""

import uuid
from pathlib import Path

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
from app.models.resume import Resume
from app.schemas.resume import ResumeUploadResponse
from app.services.document_processing import (
    extract_text_from_upload,
    sanitize_filename,
    validate_extracted_text,
    validate_upload,
)

router = APIRouter(prefix="/api/resumes", tags=["resumes"])
settings = get_settings()


@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ResumeUploadResponse:
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

    safe_filename = sanitize_filename(file.filename or "resume")
    file_id = uuid.uuid4()

    try:
        raw_text, extraction_method = extract_text_from_upload(
            safe_filename, contents
        )
        validate_extracted_text(raw_text)
    except ExtractionFailedError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except EmptyDocumentError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    storage_dir = Path(settings.DATA_DIR) / "resumes"
    storage_dir.mkdir(parents=True, exist_ok=True)
    storage_path = storage_dir / f"{file_id}_{safe_filename}"
    storage_path.write_bytes(contents)

    resume = Resume(
        id=file_id,
        original_filename=safe_filename,
        storage_path=str(storage_path),
        raw_text=raw_text,
        extraction_method=extraction_method,
        char_count=len(raw_text),
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    return ResumeUploadResponse.model_validate(resume)
