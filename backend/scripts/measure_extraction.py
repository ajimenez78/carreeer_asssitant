"""Synthetic parser benchmark; run in a fresh 512 MiB / 1 CPU container per case."""

import argparse
import io
import json
import resource
import time
import zipfile
from pathlib import Path

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from career_assistant.config import Settings
from career_assistant.documents import MAX_FILE_BYTES, SourceProcessor
from career_assistant.main import create_app


def sample(kind: str, large: bool) -> bytes:
    text = "Synthetic Staff engineer. Historical Python.\n" * (1000 if large else 1)
    if kind == "md":
        content = text.encode()
        return content.ljust(MAX_FILE_BYTES, b" ") if large else content
    if kind == "doc":
        content = (
            Path(__file__).parents[1] / "tests/fixtures/synthetic.doc"
        ).read_bytes()
        return content.ljust(MAX_FILE_BYTES, b"\x00") if large else content
    output = io.BytesIO()
    if kind == "docx":
        with zipfile.ZipFile(output, "w", zipfile.ZIP_STORED) as archive:
            archive.writestr("[Content_Types].xml", "<Types/>")
            archive.writestr(
                "word/document.xml",
                '<w:document xmlns:w="http://schemas.openxmlformats.org/'
                'wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>'
                + text
                + "</w:t></w:r></w:p></w:body></w:document>",
            )
            if large:
                archive.writestr(
                    "word/synthetic-padding",
                    b"x" * (MAX_FILE_BYTES - len(text.encode()) - 1024),
                )
    else:
        writer = PdfWriter()
        page = writer.add_blank_page(width=600, height=800)
        font = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }
        )
        page[NameObject("/Resources")] = DictionaryObject(
            {
                NameObject("/Font"): DictionaryObject(
                    {NameObject("/F1"): writer._add_object(font)}
                )
            }
        )
        stream = DecodedStreamObject()
        stream.set_data(f"BT /F1 12 Tf 50 700 Td ({text}) Tj ET".encode())
        page[NameObject("/Contents")] = writer._add_object(stream)
        if large:
            writer.add_metadata(
                {"/Subject": "x" * (MAX_FILE_BYTES - len(text.encode()) - 2048)}
            )
        writer.write(output)
    return output.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("format", choices=["pdf", "docx", "doc", "md"])
    parser.add_argument("--large", action="store_true")
    args = parser.parse_args()
    # Load the actual application and its runtime libraries; never connect providers.
    app = create_app(Settings(_env_file=None))
    content = sample(args.format, args.large)
    started = time.monotonic()
    text = SourceProcessor().extract("synthetic." + args.format, content)
    elapsed = time.monotonic() - started
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    cgroup = Path("/sys/fs/cgroup")
    print(
        json.dumps(
            {
                "format": args.format,
                "large": args.large,
                "bytes": len(content),
                "extracted_characters": len(text),
                "seconds": round(elapsed, 4),
                "worker_cpu_seconds": round(usage.ru_utime + usage.ru_stime, 4),
                "application_peak_mib": round(
                    resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 2
                ),
                "container_peak_mib": round(
                    int((cgroup / "memory.peak").read_text()) / 1024**2, 2
                ),
                "memory_max": (cgroup / "memory.max").read_text().strip(),
                "cpu_max": (cgroup / "cpu.max").read_text().strip(),
                "oom_kill": int(
                    dict(
                        line.split()
                        for line in (cgroup / "memory.events").read_text().splitlines()
                    )["oom_kill"]
                ),
            }
        )
    )
    app.state.sessions.kw["bind"].dispose()


if __name__ == "__main__":
    main()
