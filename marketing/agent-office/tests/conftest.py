from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from office.config import Settings
from office.office import Office


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings.from_env(env={"OFFICE_HOME": str(tmp_path / "var"), "OFFICE_BRAINS": "offline"})


@pytest.fixture
def make_office(tmp_path: Path):
    def build(**overrides) -> Office:
        env = {"OFFICE_HOME": str(tmp_path / "var"), "OFFICE_BRAINS": "offline", "OFFICE_RENDER_MEDIA": "0"}
        env.update({k: str(v) for k, v in overrides.items()})
        return Office(Settings.from_env(env=env))

    return build


def pytest_sessionfinish(session, exitstatus):
    """Let the office's background threads finish before Python shuts down.

    The chief does long work (redrawing a picture in Chromium, a school patrol) on daemon threads. A test that does not wait
    for one leaves it mid-render when the interpreter exits, which can crash the whole run (exit code 139) after every test
    has passed. A minute is far more than any of them needs; a thread that is truly stuck is left behind as before.
    """
    deadline = time.monotonic() + 60
    for thread in threading.enumerate():
        if thread is not threading.main_thread() and thread.daemon:
            thread.join(max(0.0, deadline - time.monotonic()))
