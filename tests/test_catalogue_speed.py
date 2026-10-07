"""The first-time work the free host used to repeat for every visitor is done once and kept."""
from __future__ import annotations

import threading
import time
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from exchange_info import api, public_translation
from exchange_info.models import PartnerUniversity, StudentDashboard
from exchange_info.storage import data_paths, ensure_data_dirs

CGU = "長庚大學"
NTPU = "國立臺北大學"
PARTNER = PartnerUniversity(program_type="交換學生", school_name="測試合作校", country="日本", source_url="https://example.edu/x")


@pytest.fixture
def counted(tmp_path, monkeypatch):
    """An app whose slow catalogue builders are replaced by counters."""
    ensure_data_dirs(tmp_path)
    calls = {"dashboard": 0}

    def build_dashboard(*args, **kwargs):
        calls["dashboard"] += 1
        return StudentDashboard(school_name=CGU, partner_universities=[PARTNER])

    monkeypatch.setattr(api, "fetch_partner_universities", lambda: [PARTNER])
    monkeypatch.setattr(api, "fetch_ntpu_partner_universities", lambda: [PARTNER])
    monkeypatch.setattr(api, "build_student_dashboard", build_dashboard)
    monkeypatch.setattr(api, "build_ntpu_student_dashboard", lambda **kwargs: StudentDashboard(school_name=NTPU, partner_universities=[PARTNER]))
    return tmp_path, calls


def test_the_cgu_dashboard_is_built_once_for_everyone_within_the_window(counted) -> None:
    data_dir, calls = counted
    client = TestClient(api.create_app(data_dir))
    for _ in range(4):
        assert client.get("/student-dashboard", params={"school": CGU}).status_code == 200
    assert calls["dashboard"] == 1


def test_the_dashboard_is_built_again_when_its_data_is_rewritten_or_the_window_ends(counted, monkeypatch) -> None:
    data_dir, calls = counted
    client = TestClient(api.create_app(data_dir))
    client.get("/student-dashboard", params={"school": CGU})
    pages = data_paths(data_dir)["processed_pages"]
    pages.parent.mkdir(parents=True, exist_ok=True)
    pages.write_text("", encoding="utf-8")
    client.get("/student-dashboard", params={"school": CGU})
    assert calls["dashboard"] == 2, "a refreshed data file is picked up at once"

    monkeypatch.setattr(api, "DASHBOARD_CACHE_SECONDS", 0.0)
    client.get("/student-dashboard", params={"school": CGU})
    assert calls["dashboard"] == 3, "and nothing is kept past the window"


def test_a_caller_cannot_change_what_the_next_visitor_gets(counted) -> None:
    data_dir, calls = counted
    client = TestClient(api.create_app(data_dir))
    first = client.get("/student-dashboard", params={"school": CGU}).json()
    first["partner_universities"].clear()
    second = client.get("/student-dashboard", params={"school": CGU}).json()
    assert len(second["partner_universities"]) == 1 and calls["dashboard"] == 1


def _warm_threads():
    return [thread for thread in threading.enumerate() if thread.name == "warm-caches"]


def test_the_warm_up_is_off_unless_asked_for(counted, monkeypatch) -> None:
    data_dir, calls = counted
    monkeypatch.delenv("EXCHANGE_WARM_CACHES", raising=False)
    with TestClient(api.create_app(data_dir)):
        assert not _warm_threads()
    assert calls["dashboard"] == 0


def test_the_warm_up_builds_the_dashboards_before_the_first_visitor_asks(counted, monkeypatch) -> None:
    data_dir, calls = counted
    monkeypatch.setenv("EXCHANGE_WARM_CACHES", "1")
    for name in ("_reference_translations", "_bundled_machine_translations", "_display_patterns", "_identifier_pattern"):
        monkeypatch.setattr(public_translation, name, lambda: None)
    monkeypatch.setattr(api, "time", SimpleNamespace(monotonic=time.monotonic, sleep=lambda seconds: None))
    with TestClient(api.create_app(data_dir)) as client:
        for thread in _warm_threads():
            thread.join(timeout=30)
        assert calls["dashboard"] == 1, "the warm-up built the CGU dashboard"
        assert client.get("/student-dashboard", params={"school": CGU}).status_code == 200
        assert calls["dashboard"] == 1, "so the first visitor did not have to"


def test_a_failing_warm_up_step_does_not_stop_the_site(counted, monkeypatch) -> None:
    data_dir, calls = counted
    monkeypatch.setenv("EXCHANGE_WARM_CACHES", "1")
    monkeypatch.setattr(public_translation, "_reference_translations", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    for name in ("_bundled_machine_translations", "_display_patterns", "_identifier_pattern"):
        monkeypatch.setattr(public_translation, name, lambda: None)
    monkeypatch.setattr(api, "time", SimpleNamespace(monotonic=time.monotonic, sleep=lambda seconds: None))
    with TestClient(api.create_app(data_dir)) as client:
        for thread in _warm_threads():
            thread.join(timeout=30)
        assert client.get("/health").status_code == 200
        assert calls["dashboard"] == 1, "the steps after the failing one still ran"
