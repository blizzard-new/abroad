from __future__ import annotations

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
