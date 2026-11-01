import os
import subprocess
from pathlib import Path

import pytest

from career_assistant import documents
from career_assistant.documents import SourceProcessor, checked_text, validate_file
from career_assistant.errors import AppError
from career_assistant.source_worker import ParseError, parse_document


@pytest.mark.parametrize(
    "filename,content,code",
    [
        ("a.txt", b"text", "unsupported_format"),
        ("a.pdf", b"", "empty_file"),
        ("a.md", b"x" * (10 * 1024 * 1024 + 1), "file_too_large"),
        ("\x00.md", b"text", "invalid_filename"),
    ],
)
def test_upload_validation(filename, content, code):
    with pytest.raises(AppError) as error:
        validate_file(filename, content)
    assert error.value.code == code


def test_filenames_never_become_paths_and_actual_content_is_parsed():
    assert validate_file("../../private/CV.PDF", b"bad") == (
        "CV.PDF",
        "application/pdf",
    )
    with pytest.raises(ParseError):
        parse_document("CV.PDF", b"not a pdf")


def test_supported_formats_preserve_text_and_docx_tables(pdf_bytes, docx_bytes):
    processor = SourceProcessor()
    assert "Staff engineer" in processor.extract("synthetic.pdf", pdf_bytes())
    assert "Historical Python" in processor.extract("synthetic.docx", docx_bytes())
    assert (
        processor.extract("synthetic.md", "# Ingeniería española".encode())
        == "# Ingeniería española"
    )
    legacy = Path(__file__).parent / "fixtures" / "synthetic.doc"
    assert "Staff engineer" in processor.extract(legacy.name, legacy.read_bytes())


@pytest.mark.parametrize(
    "kind",
    [
        "empty_pdf",
        "encrypted_pdf",
        "too_many_pages",
        "bad_docx",
        "bad_doc",
        "bad_markdown",
        "long_text",
        "zip_bomb",
        "xml_entity",
    ],
)
def test_unusable_documents_fail_safely(kind, pdf_bytes, docx_bytes):
    files = {
        "empty_pdf": ("a.pdf", lambda: pdf_bytes("")),
        "encrypted_pdf": ("a.pdf", lambda: pdf_bytes(encrypted=True)),
        "too_many_pages": ("a.pdf", lambda: pdf_bytes(pages=201)),
        "bad_docx": ("a.docx", lambda: b"not a ZIP"),
        "bad_doc": ("a.doc", lambda: b"not OLE"),
        "bad_markdown": ("a.md", lambda: b"\xff\xfe"),
        "long_text": ("a.md", lambda: b"x" * 60_001),
        "zip_bomb": ("a.docx", lambda: docx_bytes(extra_size=21 * 1024 * 1024)),
        "xml_entity": (
            "a.docx",
            lambda: docx_bytes(declaration='<!DOCTYPE x [<!ENTITY x "fake">]>'),
        ),
    }
    name, content = files[kind]
    with pytest.raises(AppError) as error:
        SourceProcessor().extract(name, content())
    assert error.value.code in {"invalid_document", "no_text"}
    if kind == "empty_pdf":
        assert "OCR" in str(error.value)


def test_empty_and_excessive_text_is_rejected_without_truncation():
    assert checked_text("  hola\x00  ") == "hola"
    for text in (" ", "x" * 60_001):
        with pytest.raises(AppError):
            checked_text(text)


def test_worker_is_serialized_and_never_receives_credentials(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-secret")
    monkeypatch.setenv("DATABASE_URL", "synthetic-dsn")
    captured = {}

    class Process:
        returncode = 0

        def __init__(self, *args, **kwargs):
            captured.update(kwargs)

        def communicate(self, *args, **kwargs):
            return b'{"text":"Safe text"}', b""

    monkeypatch.setattr(subprocess, "Popen", Process)
    assert SourceProcessor().extract("a.md", b"Safe text") == "Safe text"
    assert "OPENAI_API_KEY" not in captured["env"]
    assert "DATABASE_URL" not in captured["env"]
    with documents._worker_lock:
        with pytest.raises(AppError, match="Another source"):
            SourceProcessor().extract("a.md", b"safe")


def test_timeout_kills_the_entire_worker_group(monkeypatch):
    killed = []

    class Process:
        pid = 12345
        calls = 0

        def __init__(self, *args, **kwargs):
            pass

        def communicate(self, *args, **kwargs):
            self.calls += 1
            if self.calls == 1:
                raise subprocess.TimeoutExpired("worker", 15)
            return b"", b""

    monkeypatch.setattr(subprocess, "Popen", Process)
    monkeypatch.setattr(os, "killpg", lambda *args: killed.append(args))
    with pytest.raises(AppError) as error:
        SourceProcessor().extract("a.md", b"safe")
    assert error.value.code == "processing_timeout"
    assert killed[0][0] == 12345


def test_worker_resource_termination_is_actionable(monkeypatch):
    class Process:
        returncode = -9

        def __init__(self, *args, **kwargs):
            pass

        def communicate(self, *args, **kwargs):
            return b"", b""

    monkeypatch.setattr(subprocess, "Popen", Process)
    with pytest.raises(AppError) as error:
        SourceProcessor().extract("a.md", b"safe")
    assert error.value.code == "processing_limit"
