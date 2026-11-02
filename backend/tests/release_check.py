"""Local combined-image browser/replacement check; disposable SQL and Docker volume."""

import json
import os
import socket
import subprocess
import tempfile
import time
from pathlib import Path
from uuid import uuid4

import psycopg
from playwright.sync_api import expect, sync_playwright
from psycopg import sql
from sqlalchemy.orm import sessionmaker
from workflow_fixtures import BACKGROUND, PASSWORD

from career_assistant.ai_evaluation import REFERENCE_DESCRIPTION
from career_assistant.auth import PASSWORDS
from career_assistant.config import Settings
from career_assistant.database import (
    database_engine,
    database_url,
    ensure_local_database,
)
from career_assistant.models import Owner


def docker(*args, check=True):
    result = subprocess.run(
        ["docker", *args], check=check, capture_output=True, text=True
    )
    return result.stdout.strip()


def main():
    suffix = uuid4().hex
    name, volume = f"career-part9-{suffix}", f"career-part9-docs-{suffix}"
    image = os.environ.get("CAREER_RELEASE_IMAGE", "career-assistant:part9")
    report_path = Path(
        os.environ.get("CAREER_RELEASE_REPORT", "doc/PART9_RELEASE_CHECK.json")
    )
    url = database_url(Settings()).set(database=f"career_release_{suffix}")
    ensure_local_database(url)
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    origin = f"http://127.0.0.1:{port}"
    engine = database_engine(url)
    records = {}
    try:
        # Docker Desktop shares the checkout, while host /tmp may not be shared.
        Path(".cache").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="release-", dir=".cache") as directory:
            root = Path(directory).resolve()
            env_file = root / "runtime.env"
            container_url = url.set(host="db").render_as_string(hide_password=False)
            env_file.write_text(
                "\n".join(
                    [
                        f"DATABASE_URL={container_url}",
                        f"CAREER_SESSION_SECRET={uuid4().hex}{uuid4().hex}",
                        "CAREER_SESSION_SECURE=false",
                        f"CAREER_ALLOWED_ORIGINS={json.dumps([origin])}",
                        "CAREER_DOCUMENT_DIRECTORY=/data/documents",
                        "OPENAI_API_KEY=",
                    ]
                )
                + "\n"
            )
            env_file.chmod(0o600)
            common = [
                "--network",
                "career-assistant-local_default",
                "--env-file",
                str(env_file),
            ]
            # Run packaged migrations twice before serving; no startup migrations.
            for _ in range(2):
                docker(
                    "run",
                    "--rm",
                    *common,
                    image,
                    "python",
                    "-m",
                    "career_assistant.db_cli",
                    "migrate",
                )
            sessions = sessionmaker(engine, expire_on_commit=False)
            with sessions.begin() as session:
                session.get(Owner, 1).password_hash = PASSWORDS.hash(PASSWORD)
            launcher = root / "server.py"
            launcher.write_text(
                "import uvicorn\n"
                "from career_assistant.main import create_app\n"
                "from workflow_fixtures import WorkflowAI, WorkflowProcessor\n"
                "app=create_app(ai_client=WorkflowAI(), "
                "processor=WorkflowProcessor())\n"
                "uvicorn.run(app, "
                "host='0.0.0.0', port=8000, access_log=False, log_level='warning')\n"
            )
            launcher.chmod(0o644)
            # Only this read-only test launcher/provider is mounted. The image has
            # no fake-AI toggle and the replacement runs its normal production CMD.
            fixture = Path("backend/tests/workflow_fixtures.py").resolve()

            def start(fake):
                mounts = [
                    "--mount",
                    f"type=volume,source={volume},target=/data/documents",
                ]
                command = []
                if fake:
                    mounts += [
                        "--mount",
                        f"type=bind,source={launcher},target=/validation/server.py,readonly",
                        "--mount",
                        f"type=bind,source={fixture},target=/validation/workflow_fixtures.py,readonly",
                    ]
                    command = ["python", "/validation/server.py"]
                docker(
                    "run",
                    "--rm",
                    "-d",
                    "--name",
                    name,
                    *common,
                    "--memory",
                    "512m",
                    "--cpus",
                    "1",
                    "-p",
                    f"127.0.0.1:{port}:8000",
                    *mounts,
                    image,
                    *command,
                )

            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                try:
                    page = browser.new_page()
                    errors = []
                    page.on("pageerror", lambda error: errors.append(error.message))

                    def ready():
                        for _ in range(100):
                            try:
                                if page.request.get(
                                    origin + "/api/health", timeout=1000
                                ).ok:
                                    return
                            except Exception:
                                pass
                            time.sleep(0.1)
                        raise RuntimeError("Release container failed health check")

                    start(True)
                    ready()
                    page.goto(origin)
                    page.get_by_label("Username", exact=True).fill("owner")
                    page.get_by_label("Password", exact=True).fill(PASSWORD)
                    page.get_by_role("button", name="Sign in", exact=True).click()
                    description = page.get_by_role(
                        "textbox", name="The role you’re looking for", exact=True
                    )
                    description.fill(REFERENCE_DESCRIPTION)
                    page.get_by_role("button", name="Save draft", exact=True).click()
                    expect(page.get_by_role("status")).to_contain_text(
                        "Definition saved"
                    )
                    navigation = page.get_by_role("navigation", name="Definition steps")
                    navigation.get_by_role("button", name="02 Background").click()
                    page.get_by_label("Document", exact=True).set_input_files(
                        {
                            "name": "synthetic-cv.md",
                            "mimeType": "text/markdown",
                            "buffer": BACKGROUND.encode(),
                        }
                    )
                    page.get_by_role("button", name="Add source", exact=True).click()
                    page.get_by_role(
                        "button", name="Suggest background facts", exact=True
                    ).click()
                    page.get_by_label("Reviewed facts, one per line").fill(
                        "Reviewed historical Python experience"
                    )
                    page.get_by_role(
                        "button", name="Accept reviewed facts", exact=True
                    ).click()
                    expect(page.get_by_role("status")).to_contain_text(
                        "Background facts accepted"
                    )
                    page.get_by_label("Source type").select_option("url")
                    page.get_by_label("Source name").fill("Synthetic public profile")
                    page.get_by_label("Public URL").fill("https://example.com/profile")
                    page.get_by_role("button", name="Add source", exact=True).click()
                    navigation.get_by_role("button", name="03 Clarify").click()
                    page.get_by_role(
                        "button", name="Request clarification & suggestions", exact=True
                    ).click()
                    navigation.get_by_role("button", name="04 Review & save").click()
                    page.get_by_role(
                        "button", name="Apply reviewed suggestions & save"
                    ).click()
                    expect(page.get_by_role("status")).to_contain_text(
                        "Definition saved"
                    )
                    page.reload()
                    expect(description).to_have_value(REFERENCE_DESCRIPTION)
                    description.fill(REFERENCE_DESCRIPTION + " Flexible hours matter.")
                    page.get_by_role("button", name="Save draft", exact=True).click()
                    expect(page.get_by_role("status")).to_contain_text(
                        "Definition saved"
                    )
                    navigation.get_by_role("button", name="03 Clarify").click()
                    page.get_by_role(
                        "button", name="Request clarification & suggestions", exact=True
                    ).click()
                    navigation.get_by_role("button", name="05 Summary").click()
                    summary = page.get_by_role(
                        "article", name="Saved role summary", exact=True
                    )
                    expect(summary).to_be_visible()
                    summary_text = summary.text_content()
                    navigation.get_by_role("button", name="04 Review & save").click()
                    page.get_by_role(
                        "button", name="Discard suggestions", exact=True
                    ).click()
                    page.get_by_role(
                        "button", name="Stop clarification", exact=True
                    ).click()
                    expect(page.get_by_role("status")).to_contain_text(
                        "Clarification stopped"
                    )
                    before = page.request.get(origin + "/api/job-definition").json()
                    assert len(before["sources"]) == 2 and before["preferences"]
                    assert before["assessment"] and before["clarification_paused"]
                    records["runtime_memory"] = docker(
                        "stats", "--no-stream", "--format", "{{.MemUsage}}", name
                    )
                    docker("rm", "-f", name)
                    start(False)
                    ready()
                    page.reload()
                    expect(description).to_have_value(before["description"])
                    expect(
                        page.get_by_role(
                            "button", name="Resume clarification", exact=True
                        )
                    ).to_be_visible()
                    navigation.get_by_role("button", name="05 Summary").click()
                    expect(summary).to_have_text(summary_text)
                    after = page.request.get(origin + "/api/job-definition").json()
                    assert after == before
                    sid = next(s["id"] for s in after["sources"] if s["kind"] == "file")
                    original = page.request.get(
                        origin + f"/api/job-definition/sources/{sid}/original"
                    )
                    assert original.ok and original.body() == BACKGROUND.encode()
                    runtime = docker(
                        "exec",
                        name,
                        "python",
                        "-c",
                        "import os,shutil; from pathlib import Path; "
                        "assert shutil.which('node') is None; "
                        "assert os.getuid() == 10001; "
                        "assert not Path('/app/.env').exists(); "
                        "assert not Path('/validation').exists(); "
                        "print('Python-only non-root runtime; no test mount or .env')",
                    )
                    records["runtime_check"] = runtime
                    assert page.request.get(origin + "/api/not-a-route").status == 404
                    assert page.request.get(origin + "/.env").status == 404
                    assert errors == []
                    records["image_id"] = docker(
                        "image", "inspect", "--format", "{{.Id}}", image
                    )
                    records["passed"] = True
                    records["checks"] = [
                        "packaged migrations repeat safely",
                        "complete browser workflow with test-only injected AI",
                        "same-origin HttpOnly sessions",
                        "real Markdown extraction",
                        "save/reload/refine",
                        "production replacement preserves SQL, session and originals",
                        "natural-language summary and pause survive replacement",
                        "private files excluded",
                        "Python-only non-root runtime",
                        "512 MiB and 1 CPU limits",
                    ]
                finally:
                    browser.close()
        report_path.write_text(json.dumps(records, indent=2) + "\n")
        print(f"Combined-image workflow and replacement passed; report: {report_path}")
    finally:
        docker("rm", "-f", name, check=False)
        docker("volume", "rm", volume, check=False)
        engine.dispose()
        with psycopg.connect(
            url.set(drivername="postgresql", database="postgres").render_as_string(
                hide_password=False
            ),
            autocommit=True,
        ) as connection:
            connection.execute(
                sql.SQL("DROP DATABASE {} WITH (FORCE)").format(
                    sql.Identifier(url.database)
                )
            )


if __name__ == "__main__":
    main()
