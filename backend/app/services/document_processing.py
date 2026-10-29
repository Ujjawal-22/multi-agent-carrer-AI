"""
Document processing service. Zero LLM calls — pure parsing logic.

PDF extraction strategy: try direct text extraction (PyMuPDF) first; if it
yields suspiciously little text, fall back to OCR (render pages as images
via PyMuPDF, then Tesseract) since that likely means a scanned PDF.
"""

import io
import re
import uuid
from pathlib import Path

import docx
import fitz  # PyMuPDF
import pytesseract
from PIL import Image

from app.core.config import get_settings
from app.core.exceptions import (
    EmptyDocumentError,
    ExtractionFailedError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)

settings = get_settings()
pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD


def sanitize_filename(filename: str) -> str:
    name = Path(filename).name
    name = re.sub(r"[^A-Za-z0-9_.\-]", "_", name)
    return name or f"upload_{uuid.uuid4().hex}"


def validate_upload(filename: str, contents: bytes) -> None:
    extension = Path(filename).suffix.lower()
    if extension not in settings.ALLOWED_RESUME_EXTENSIONS:
        raise UnsupportedFileTypeError(
            f"File type '{extension}' is not supported. "
            f"Allowed types: {', '.join(settings.ALLOWED_RESUME_EXTENSIONS)}"
        )

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise FileTooLargeError(
            f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB}MB size limit."
        )

    if len(contents) == 0:
        raise EmptyDocumentError("Uploaded file is empty.")


def _extract_pdf_direct(contents: bytes) -> str:
    try:
        with fitz.open(stream=contents, filetype="pdf") as pdf:
            pages_text = [page.get_text() for page in pdf]  # type: ignore[attr-defined]
        return "\n".join(pages_text).strip()
    except Exception as exc:  # noqa: BLE001
        raise ExtractionFailedError(f"Failed to open PDF: {exc}") from exc


def _extract_pdf_via_ocr(contents: bytes) -> str:
    try:
        extracted_pages: list[str] = []
        with fitz.open(stream=contents, filetype="pdf") as pdf:
            for page in pdf:  # type: ignore[attr-defined]
                pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                image = Image.open(io.BytesIO(pixmap.tobytes("png")))
                extracted_pages.append(pytesseract.image_to_string(image))
        return "\n".join(extracted_pages).strip()
    except Exception as exc:  # noqa: BLE001
        raise ExtractionFailedError(f"OCR extraction failed: {exc}") from exc


def _extract_docx(contents: bytes) -> str:
    try:
        document = docx.Document(io.BytesIO(contents))
        paragraphs = [p.text for p in document.paragraphs]
        return "\n".join(paragraphs).strip()
    except Exception as exc:  # noqa: BLE001
        raise ExtractionFailedError(f"Failed to read DOCX file: {exc}") from exc


def extract_text_from_upload(filename: str, contents: bytes) -> tuple[str, str]:
    extension = Path(filename).suffix.lower()

    if extension == ".pdf":
        direct_text = _extract_pdf_direct(contents)
        if len(direct_text) >= settings.MIN_DIRECT_TEXT_LENGTH:
            return direct_text, "direct"
        ocr_text = _extract_pdf_via_ocr(contents)
        return ocr_text, "ocr"

    if extension == ".docx":
        return _extract_docx(contents), "docx"

    raise UnsupportedFileTypeError(f"Unsupported file type: {extension}")


def validate_extracted_text(text: str) -> None:
    if not text or not text.strip():
        raise EmptyDocumentError(
            "No readable text could be extracted from this document. "
            "It may be corrupted, empty, or an unsupported scan quality."
        )
