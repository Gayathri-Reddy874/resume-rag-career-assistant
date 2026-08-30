"""
Resume file parsing.

Handles extraction of plain text from .pdf, .docx and .txt uploads, with
validation of file extension and size up front so bad input fails fast with
a clear error instead of an obscure downstream stack trace.
"""
from io import BytesIO

import PyPDF2
from docx import Document
from fastapi import UploadFile

from app.core.config import get_settings
from app.core.exceptions import (
    EmptyDocumentError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def _validate(file: UploadFile, content: bytes) -> None:
    settings = get_settings()
    name = (file.filename or "").lower()

    if not name.endswith(settings.allowed_upload_extensions):
        raise UnsupportedFileTypeError(
            f"'{file.filename}' has an unsupported extension. "
            f"Allowed types: {', '.join(settings.allowed_upload_extensions)}"
        )

    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.max_upload_size_mb:
        raise FileTooLargeError(
            f"'{file.filename}' is {size_mb:.1f}MB, which exceeds the "
            f"{settings.max_upload_size_mb}MB limit."
        )


def _extract_txt(content: bytes) -> str:
    return content.decode(errors="ignore")


def _extract_docx(content: bytes) -> str:
    doc = Document(BytesIO(content))
    return "\n".join(p.text for p in doc.paragraphs)


def _extract_pdf(content: bytes) -> str:
    reader = PyPDF2.PdfReader(BytesIO(content))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n".join(pages)


def extract_text(file: UploadFile, content: bytes) -> str:
    """Validate and extract plain text from an uploaded resume file.

    Args:
        file: The FastAPI UploadFile (used for filename/content-type).
        content: The raw bytes already read from the file.

    Returns:
        Extracted plain text.

    Raises:
        UnsupportedFileTypeError, FileTooLargeError, EmptyDocumentError
    """
    _validate(file, content)
    name = file.filename.lower()

    if name.endswith(".txt"):
        text = _extract_txt(content)
    elif name.endswith(".docx"):
        text = _extract_docx(content)
    else:  # .pdf
        text = _extract_pdf(content)

    text = text.strip()
    if not text:
        raise EmptyDocumentError(
            f"No extractable text found in '{file.filename}'. "
            "If it's a scanned/image-based PDF, try a text-based export instead."
        )

    logger.info("Extracted %d characters from %s", len(text), file.filename)
    return text
