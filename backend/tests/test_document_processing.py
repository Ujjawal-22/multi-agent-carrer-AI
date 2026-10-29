import pytest

from app.core.exceptions import (
    EmptyDocumentError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from app.services.document_processing import (
    sanitize_filename,
    validate_extracted_text,
    validate_upload,
)


def test_sanitize_filename_strips_path_traversal() -> None:
    assert sanitize_filename("../../etc/passwd") == "passwd"


def test_sanitize_filename_replaces_unsafe_characters() -> None:
    result = sanitize_filename("my resume (final)!!.pdf")
    assert " " not in result
    assert "(" not in result


def test_validate_upload_rejects_unsupported_extension() -> None:
    with pytest.raises(UnsupportedFileTypeError):
        validate_upload("resume.exe", b"some bytes")


def test_validate_upload_rejects_empty_file() -> None:
    with pytest.raises(EmptyDocumentError):
        validate_upload("resume.pdf", b"")


def test_validate_upload_rejects_oversized_file() -> None:
    from app.core.config import get_settings

    settings = get_settings()
    oversized = b"x" * (settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024 + 1)
    with pytest.raises(FileTooLargeError):
        validate_upload("resume.pdf", oversized)


def test_validate_extracted_text_rejects_blank_text() -> None:
    with pytest.raises(EmptyDocumentError):
        validate_extracted_text("   ")


def test_validate_extracted_text_accepts_real_text() -> None:
    validate_extracted_text("John Doe, Software Engineer with 5 years experience.")
