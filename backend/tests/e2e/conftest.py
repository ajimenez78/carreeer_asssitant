import socket
import threading
import time
from contextlib import contextmanager
from pathlib import Path

import pytest
import uvicorn
from workflow_fixtures import PASSWORD, WorkflowAI, WorkflowProcessor

from career_assistant.auth import PASSWORDS
from career_assistant.config import Settings
from career_assistant.main import create_app
from career_assistant.models import Owner
from career_assistant.storage import LocalDocumentStore


@pytest.fixture
def serve():
    @contextmanager
    def start(factory, port=0):
        listener = socket.socket()
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", port))
        origin = f"http://127.0.0.1:{listener.getsockname()[1]}"
        app = factory(origin)
        server = uvicorn.Server(
            uvicorn.Config(app, log_level="warning", access_log=False)
        )
        thread = threading.Thread(
            target=server.run, kwargs={"sockets": [listener]}, daemon=True
        )
        thread.start()
        try:
            deadline = time.monotonic() + 10
            while not server.started:
                if not thread.is_alive() or time.monotonic() > deadline:
                    pytest.fail("Local application test server failed to start")
                time.sleep(0.01)
            yield origin, app
        finally:
            server.should_exit = True
            thread.join(timeout=10)
            listener.close()

    return start


@pytest.fixture
def workflow(sessions, tmp_path, serve):
    with sessions.begin() as session:
        session.get(Owner, 1).password_hash = PASSWORDS.hash(PASSWORD)
    ai = WorkflowAI()
    store = LocalDocumentStore(tmp_path / "originals")

    def factory(origin, extra_origins=()):
        return create_app(
            Settings(
                _env_file=None,
                session_secret="synthetic-session-secret-" * 3,
                allowed_origins=[origin, *extra_origins],
                frontend_directory=Path("frontend/out"),
            ),
            sessions=sessions,
            ai_client=ai,
            store=store,
            processor=WorkflowProcessor(),
        )

    with serve(factory) as (origin, app):
        yield origin, app, ai, factory


def pytest_addoption(parser):
    parser.addoption(
        "--live-openai",
        action="store_true",
        help="Allow the explicit paid synthetic Part 9 workflow",
    )
