"""Тесты парсинга и чанкинга (без внешних сервисов)."""

import pytest

from app.services.document_service import (
    EmptyDocumentError,
    UnsupportedFileTypeError,
    chunk_text,
    extract_text,
)


def test_extract_txt():
    assert extract_text("note.txt", "Привет мир".encode("utf-8")) == "Привет мир"


def test_extract_unsupported_type():
    with pytest.raises(UnsupportedFileTypeError):
        extract_text("archive.zip", b"data")


def test_extract_empty_document():
    with pytest.raises(EmptyDocumentError):
        extract_text("blank.txt", b"   \n  ")


def test_chunk_text_returns_chunks():
    chunks = chunk_text("Это предложение. " * 500)
    assert len(chunks) >= 1
    assert all(isinstance(c, str) and c for c in chunks)
