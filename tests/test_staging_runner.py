"""The local test edition must stay isolated from production and must label every HTML page."""
from __future__ import annotations

import importlib.util
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
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


def test_pages_get_an_account_switcher_that_works_without_script() -> None:
    page = _client().get("/page").text
    assert 'id="uw-staging-accounts"' in page and "<script" not in page
    for alias in ("super", "a", "b", "c"):
        assert f"/__staging/login?as={alias}" in page
    assert "/__staging/logout" in page


def test_one_click_login_uses_the_apps_own_cookie_and_cannot_be_shadowed_by_a_catch_all() -> None:
    app = FastAPI()

    @app.get("/{path:path}")
    def spa(path: str) -> PlainTextResponse:
        return PlainTextResponse("spa")

    staging_runner.add_login_routes(app, lambda email: [f"exchange_guide_session=token-for-{email}; HttpOnly; Path=/; SameSite=lax"])
    client = TestClient(app, follow_redirects=False)

    login = client.get("/__staging/login?as=super")
    assert login.status_code == 303 and login.headers["location"] == "/#my-application"
    assert "exchange_guide_session=token-for-super@staging.test" in login.headers["set-cookie"]
    assert client.get("/__staging/login?as=nobody").status_code == 404
    # only same-site paths are accepted as the landing page
    assert client.get("/__staging/login?as=a&to=//evil.example").headers["location"] == "/#my-application"
    assert client.get("/__staging/login?as=a&to=https://evil.example").headers["location"] == "/#my-application"
    assert client.get("/anything-else").text == "spa"
    logout = client.get("/__staging/logout")
    assert logout.status_code == 303 and "exchange_guide_session" in logout.headers["set-cookie"] and "Max-Age=0" in logout.headers["set-cookie"]


def test_login_fails_loudly_when_the_real_login_gives_no_session() -> None:
    app = FastAPI()
    staging_runner.add_login_routes(app, lambda email: [])
    assert TestClient(app, follow_redirects=False).get("/__staging/login?as=super").status_code == 502


def test_super_account_is_listed_first_and_is_a_content_admin(monkeypatch) -> None:
    import os

    monkeypatch.setattr(os, "environ", os.environ.copy())
    assert staging_runner.STUDENTS[0][0] == "super"
    staging_runner.scrub_environment()
    assert os.environ["EXCHANGE_CONTENT_ADMIN_EMAILS"] == staging_runner.SUPER_EMAIL
    assert set(staging_runner.ALIASES) == {"super", "a", "b", "c"}
