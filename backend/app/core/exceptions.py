"""
Domain-specific exceptions for document handling.

Kept separate from generic Python exceptions so API routes can catch them
specifically and map each one to the correct HTTP status code.
"""


class DocumentProcessingError(Exception):
    """Base class for all document-processing failures."""


class UnsupportedFileTypeError(DocumentProcessingError):
    """Raised when an uploaded file's extension isn't allowed."""


class FileTooLargeError(DocumentProcessingError):
    """Raised when an uploaded file exceeds the configured size limit."""


class EmptyDocumentError(DocumentProcessingError):
    """Raised when a document is uploaded but contains no usable text."""


class ExtractionFailedError(DocumentProcessingError):
    """Raised when text extraction (direct or OCR) fails entirely."""
