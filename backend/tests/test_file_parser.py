import io

import pytest
from fastapi import UploadFile

from app.core.exceptions import EmptyDocumentError, UnsupportedFileTypeError
from app.services import file_parser


def _upload(name: str, content: bytes) -> tuple[UploadFile, bytes]:
    return UploadFile(filename=name, file=io.BytesIO(content)), content


def test_extract_txt_returns_text():
    file, content = _upload("resume.txt", b"Experienced data analyst.")
    assert file_parser.extract_text(file, content) == "Experienced data analyst."


def test_rejects_unsupported_extension():
    file, content = _upload("resume.exe", b"not a resume")
    with pytest.raises(UnsupportedFileTypeError):
        file_parser.extract_text(file, content)


def test_rejects_empty_document():
    file, content = _upload("resume.txt", b"   ")
    with pytest.raises(EmptyDocumentError):
        file_parser.extract_text(file, content)


def test_rejects_oversized_file(monkeypatch):
    from app.core import config

    config.get_settings.cache_clear()
    monkeypatch.setenv("MAX_UPLOAD_SIZE_MB", "0")
    config.get_settings.cache_clear()

    file, content = _upload("resume.txt", b"some content")
    from app.core.exceptions import FileTooLargeError

    with pytest.raises(FileTooLargeError):
        file_parser.extract_text(file, content)

    config.get_settings.cache_clear()
