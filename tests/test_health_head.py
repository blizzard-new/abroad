"""An uptime monitor asks /health with HEAD; it must get 200, cheaply, without changing the published API."""
from __future__ import annotations

from fastapi.testclient import TestClient

from exchange_info.api import create_app


def test_head_on_health_answers_200_with_no_body() -> None:
    client = TestClient(create_app())
    head = client.head("/health")
    assert head.status_code == 200 and head.content == b""
    assert client.get("/health").json()["status"] == "ok", "the normal answer is unchanged"


def test_the_published_api_is_not_changed_by_it() -> None:
    paths = TestClient(create_app()).get("/openapi.json").json()["paths"]
    assert set(paths["/health"]) == {"get"}


def test_other_methods_on_health_are_still_refused() -> None:
    client = TestClient(create_app())
    assert client.post("/health").status_code == 405 and client.delete("/health").status_code == 405


def test_the_pings_are_not_counted_as_visits_or_as_api_load() -> None:
    from exchange_info.analytics import UNMEASURED_PATHS
    assert "/health" in UNMEASURED_PATHS
