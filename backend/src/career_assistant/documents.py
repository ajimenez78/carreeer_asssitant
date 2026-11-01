"""Bounded document parsing in a credential-free child process."""

import json
import os
import signal
import subprocess
import sys
from pathlib import Path
from threading import Lock

from career_assistant.errors import AppError

MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_TEXT_CHARS = 60_000
WORKER_SECONDS = 15
WORKER_MEMORY_BYTES = 256 * 1024 * 1024
MEDIA_TYPES = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".md": "text/markdown",
    ".markdown": "text/markdown",
}
_worker_lock = Lock()


def validate_file(filename: str, content: bytes) -> tuple[str, str]:
    name = filename.replace("\\", "/").rsplit("/", 1)[-1].strip()
    if not name or len(name) > 200 or any(ord(char) < 32 for char in name):
        raise AppError(
            "invalid_filename", "Use a filename of 1–200 visible characters.", 422
        )
    extension = Path(name).suffix.lower()
    if extension not in MEDIA_TYPES:
        raise AppError(
            "unsupported_format", "Upload a PDF, .doc, .docx, or Markdown file.", 415
        )
    if not content:
        raise AppError("empty_file", "The uploaded file is empty.", 422)
    if len(content) > MAX_FILE_BYTES:
        raise AppError("file_too_large", "Upload a file no larger than 10 MiB.", 413)
    return name, MEDIA_TYPES[extension]


def checked_text(text: str) -> str:
    text = text.replace("\x00", "").strip()
    if len(text) > MAX_TEXT_CHARS:
        raise AppError(
            "text_too_large",
            "Use a shorter source (at most 60,000 extracted characters).",
            413,
        )
    if not text:
        raise AppError(
            "no_text",
            "No text extracted. Upload a text-based file or paste text; "
            "scanned PDFs need OCR.",
            422,
        )
    return text


class SourceProcessor:
    def extract(self, filename: str, content: bytes) -> str:
        return self._run("file", filename, content)

    def fetch(self, url: str) -> str:
        return self._run("url", url, b"")

    def _run(self, kind: str, name: str, content: bytes) -> str:
        if not _worker_lock.acquire(blocking=False):
            raise AppError(
                "processing_busy", "Another source is processing. Retry shortly.", 409
            )
        try:
            # Never pass API keys, connection strings, or storage credentials.
            env = {
                key: os.environ[key]
                for key in ("PATH", "LANG", "CATDOCRC")
                if key in os.environ
            }
            # Support installed packages and local source trees.
            env["PYTHONPATH"] = str(Path(__file__).resolve().parent.parent)
            process = subprocess.Popen(
                [sys.executable, "-m", "career_assistant.source_worker", kind, name],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                env=env,
                start_new_session=True,
            )
            try:
                output, _ = process.communicate(content, timeout=WORKER_SECONDS)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.communicate()
                raise AppError(
                    "processing_timeout",
                    "Processing timed out. Upload a simpler document or paste text.",
                    504,
                ) from None
            if process.returncode != 0:
                raise AppError(
                    "processing_limit",
                    "Processing failed or exceeded its limits. "
                    "Upload a simpler document or paste text.",
                    422,
                )
            result = json.loads(output)
            if "error" in result:
                raise AppError(**result["error"])
            return checked_text(result["text"])
        finally:
            _worker_lock.release()
