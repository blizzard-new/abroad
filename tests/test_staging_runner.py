"""The local test edition must stay isolated from production and must label every HTML page."""
from __future__ import annotations

import importlib.util
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.testclient import TestClient

_SPEC = importlib.util.spec_from_file_location(
    "staging_runner", Path(__file__).resolve().parents[1] / "scripts" / "staging_runner.py"
)
staging_runner = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(staging_runner)


def _client(label: str = "PR #1 abc1234") -> TestClient:
    app = FastAPI()

    @app.get("/page", response_class=HTMLResponse)
    def page() -> str:
        return "<html><body><main>內容</main></body></html>"

    @app.get("/data")
    def data() -> JSONResponse:
        return JSONResponse({"html": "</body>"})

    return TestClient(staging_runner.StagingStrip(app, label))


def test_html_pages_get_one_strip_before_body_end_and_a_correct_length() -> None:
    response = _client().get("/page")
    assert response.text.count('id="uw-staging-strip"') == 1
    assert response.text.index("測試版") < response.text.index("</body>")
    assert "PR #1 abc1234" in response.text
    assert int(response.headers["content-length"]) == len(response.content)


def test_api_responses_are_not_touched() -> None:
    response = _client().get("/data")
    assert response.json() == {"html": "</body>"}
    assert "uw-staging-strip" not in response.text


def test_label_is_escaped() -> None:
    assert "<script>" not in _client("<script>alert(1)</script>").get("/page").text


def test_production_variables_are_removed_before_the_app_starts(monkeypatch) -> None:
    import os

    monkeypatch.setattr(os, "environ", os.environ.copy())  # the runner edits os.environ; keep other tests unaffected
    for name in ("EXCHANGE_SUPABASE_URL", "EXCHANGE_ENVIRONMENT", "SUPABASE_KEY", "GOOGLE_OAUTH_CLIENT_ID", "RENDER_EXTERNAL_URL"):
        monkeypatch.setenv(name, "x")
    removed = staging_runner.scrub_environment()
    assert {"EXCHANGE_SUPABASE_URL", "EXCHANGE_ENVIRONMENT", "SUPABASE_KEY", "GOOGLE_OAUTH_CLIENT_ID", "RENDER_EXTERNAL_URL"} <= set(removed)
    assert "EXCHANGE_SUPABASE_URL" not in os.environ and "SUPABASE_KEY" not in os.environ
    assert os.environ["EXCHANGE_AUTH_METHODS"] == "email"
    assert "EXCHANGE_ENVIRONMENT" not in os.environ  # unset means the local development mode
