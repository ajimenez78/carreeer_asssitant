import socket
import threading
import time

import pytest
import uvicorn

from career_assistant.config import Settings
from career_assistant.main import create_app


@pytest.fixture(scope="session")
def live_server():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        server = uvicorn.Server(
            uvicorn.Config(create_app(Settings(_env_file=None)), log_level="warning")
        )
        thread = threading.Thread(
            target=server.run, kwargs={"sockets": [listener]}, daemon=True
        )
        thread.start()
        try:
            deadline = time.monotonic() + 10
            while not server.started:
                if not thread.is_alive() or time.monotonic() > deadline:
                    pytest.fail("Local test server failed to start")
                time.sleep(0.01)
            yield f"http://127.0.0.1:{port}"
        finally:
            server.should_exit = True
            thread.join(timeout=10)
