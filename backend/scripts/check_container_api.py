"""Synthetic packaged API smoke test; requires the local Compose DB and image.

Creates and drops only a generated local test database/container. Makes no AI calls.
Run from the repository root.
"""

import json
import secrets
import subprocess
import time
from pathlib import Path
from uuid import uuid4

import httpx2 as httpx
import psycopg
from psycopg import sql
from sqlalchemy.orm import sessionmaker

from career_assistant.auth import PASSWORDS
from career_assistant.config import Settings
from career_assistant.database import (
    database_engine,
    database_url,
    ensure_local_database,
    migrate_database,
)
from career_assistant.models import Owner
from career_assistant.persistence import ensure_owner


def docker(*args):
    return subprocess.check_output(
        ["docker", *args], text=True, stderr=subprocess.DEVNULL
    ).strip()


url = database_url(Settings()).set(database="career_test_" + uuid4().hex)
name = "career-part7-check-" + uuid4().hex[:12]
ensure_local_database(url)
engine = database_engine(url)
try:
    migrate_database(url)
    with sessionmaker(engine).begin() as session:
        ensure_owner(session)
        session.get(Owner, 1).password_hash = PASSWORDS.hash(
            "synthetic-container-password"
        )
    docker(
        "run",
        "--detach",
        "--rm",
        "--name",
        name,
        "--memory=512m",
        "--cpus=1",
        "--network=career-assistant-local_default",
        "--publish",
        "127.0.0.1::8000",
        "--env",
        "DATABASE_URL=" + url.set(host="db").render_as_string(hide_password=False),
        "--env",
        "CAREER_SESSION_SECRET=" + secrets.token_urlsafe(48),
        "--env",
        "CAREER_DOCUMENT_DIRECTORY=/data/documents",
        "career-assistant-local-backend",
    )
    port = docker("port", name, "8000").rsplit(":", 1)[1]
    with httpx.Client(
        base_url="http://127.0.0.1:" + port,
        headers={"Origin": "http://127.0.0.1:8000"},
        timeout=30,
    ) as client:
        for _ in range(40):
            try:
                if client.get("/api/health").status_code == 200:
                    break
            except httpx.TransportError:
                pass
            time.sleep(0.2)
        root = "/api/job-definition"
        assert client.get(root).status_code == 401
        assert (
            client.post(
                "/api/session",
                json={"username": "owner", "password": "synthetic-container-password"},
            ).status_code
            == 200
        )
        draft = {
            "description": "Synthetic Staff scope; unknown salary.",
            "preferences": [],
        }
        assert client.put(root, json=draft).status_code == 200
        timings = []
        for _ in range(3):
            started = time.monotonic()
            assert client.get(root).status_code == 200
            assert client.put(root, json=draft).status_code == 200
            timings.append(time.monotonic() - started)
        content = (
            Path("backend/tests/fixtures/synthetic.doc")
            .read_bytes()
            .ljust(10 * 1024 * 1024, b"\x00")
        )
        started = time.monotonic()
        response = client.post(
            root + "/sources", files={"file": ("synthetic.doc", content)}
        )
        upload_seconds = time.monotonic() - started
        assert response.status_code == 201, response.status_code
        row = response.json()
        assert row["extraction_state"] == "ready" and row["original_stored"]
        sid = row["id"]
        assert "Staff engineer" in row["extracted_text"]
        assert client.get(f"{root}/sources/{sid}/original").content == content
        assert (
            client.patch(
                f"{root}/sources/{sid}",
                json={"facts": ["Synthetic historical Staff engineer"]},
            ).status_code
            == 200
        )
        peak = int(docker("exec", name, "cat", "/sys/fs/cgroup/memory.peak")) / 1024**2
        assert not client.delete(root).json()["cleanup_pending"]
        assert client.get(root).status_code == 404
        assert client.delete("/api/session").status_code == 204
        assert client.get("/api/session").status_code == 401
        report = {
            "passed": True,
            "synthetic_only": True,
            "max_get_plus_save_seconds": round(max(timings), 4),
            "legacy_doc_bytes": len(content),
            "legacy_upload_seconds": round(upload_seconds, 4),
            "container_peak_mib": round(peak, 2),
            "memory_max_bytes": 536870912,
            "cpus": 1,
        }
        Path(
            "doc/features/job-definition/evidence/PART7_CONTAINER_CHECK.json"
        ).write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report))
finally:
    subprocess.run(
        ["docker", "rm", "--force", name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    engine.dispose()
    with psycopg.connect(
        url.set(drivername="postgresql", database="postgres").render_as_string(
            hide_password=False
        ),
        autocommit=True,
    ) as connection:
        connection.execute(
            sql.SQL("DROP DATABASE {}").format(sql.Identifier(url.database))
        )
