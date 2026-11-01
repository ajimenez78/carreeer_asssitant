"""Disposable parser/fetcher. Linux limits apply before importing parsers."""

import io
import json
import logging
import resource
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree

MAX_TEXT = 60_000


class ParseError(ValueError):
    pass


def parse_document(filename: str, content: bytes) -> str:
    extension = Path(filename).suffix.lower()
    if extension in {".md", ".markdown"}:
        return content.decode("utf-8-sig")
    if extension == ".pdf":
        from pypdf import PdfReader

        if not content.startswith(b"%PDF-"):
            raise ParseError("The file is not a valid PDF.")
        reader = PdfReader(io.BytesIO(content))
        if reader.is_encrypted:
            raise ParseError("Upload a PDF without password protection.")
        if len(reader.pages) > 200:
            raise ParseError("Use a PDF with no more than 200 pages.")
        parts = []
        length = 0
        for page in reader.pages:
            text = page.extract_text() or ""
            length += len(text)
            if length > MAX_TEXT:
                raise ParseError(
                    "Use a source with at most 60,000 extracted characters."
                )
            parts.append(text)
        return "\n".join(parts)
    if extension == ".docx":
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            entries = archive.infolist()
            if (
                len(entries) > 2000
                or sum(item.file_size for item in entries) > 20 * 1024 * 1024
            ):
                raise ParseError(
                    "The expanded DOCX exceeds the 20 MiB processing limit."
                )
            xml = archive.read("word/document.xml")
            if b"<!DOCTYPE" in xml.upper() or b"<!ENTITY" in xml.upper():
                raise ParseError("The DOCX contains unsupported XML declarations.")
            root = ElementTree.fromstring(xml)
            ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
            # Paragraphs include body text and table cells in document order.
            return "\n".join("".join(node.itertext()) for node in root.iter(ns + "p"))
    if extension == ".doc":
        if not content.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
            raise ParseError("Invalid binary Word .doc. Upload .docx or paste text.")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.doc"
            path.write_bytes(content)
            result = subprocess.run(
                ["catdoc", "-w", "-d", "utf-8", str(path)],
                capture_output=True,
                timeout=10,
            )
        if result.returncode != 0:
            raise ParseError(
                "The Word document could not be read. Upload .docx or paste its text."
            )
        return result.stdout.decode("utf-8")
    raise ParseError("Unsupported document format.")


def main():
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024,) * 2)
    resource.setrlimit(resource.RLIMIT_CPU, (8, 8))
    resource.setrlimit(resource.RLIMIT_FSIZE, (12 * 1024 * 1024,) * 2)
    logging.disable(logging.CRITICAL)
    try:
        if sys.argv[1] == "url":
            from career_assistant.public_links import fetch_public

            text = fetch_public(sys.argv[2])
        else:
            text = parse_document(
                sys.argv[2], sys.stdin.buffer.read(10 * 1024 * 1024 + 1)
            )
        text = text.replace("\x00", "").strip()
        if len(text) > MAX_TEXT:
            raise ParseError("Use a source with at most 60,000 extracted characters.")
        if not text:
            print(
                json.dumps(
                    {
                        "error": {
                            "code": "no_text",
                            "message": "No extractable text. Upload a text-based "
                            "alternative or paste text; scanned PDFs need OCR.",
                            "status": 422,
                        }
                    }
                )
            )
        else:
            print(json.dumps({"text": text}))
    except Exception as error:
        # Only deliberately content-free parser messages may leave this process.
        from career_assistant.public_links import LinkError

        message = (
            str(error)
            if isinstance(error, (ParseError, LinkError))
            else "The source could not be processed within its limits."
        )
        message += " Upload a text-based document or paste text instead."
        print(
            json.dumps(
                {
                    "error": {
                        "code": "source_unavailable"
                        if sys.argv[1] == "url"
                        else "invalid_document",
                        "message": message,
                        "status": 422,
                    }
                }
            )
        )


if __name__ == "__main__":
    main()
