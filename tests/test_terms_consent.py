"""Nobody can start signing in (and so nobody can create an account) without ticking the current terms."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.legal_pages import TERMS_VERSION

STATIC = Path(__file__).resolve().parents[1] / "src" / "exchange_info" / "static"


class RecordingStore:
    backend_name = "memory"

    def __init__(self) -> None:
        self.started = 0

    def start_oauth_state(self, record, **kwargs):
        self.started += 1
        return record


@pytest.fixture()
def browser(monkeypatch):
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "id-for-test")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "secret-for-test")
    store = RecordingStore()
    client = TestClient(create_app(transient_auth_store=store), follow_redirects=False)
    return client, store


@pytest.mark.parametrize("query", ["", "?terms=", "?terms=0", "?terms=true", "?terms=2020-01-01", "?terms=" + TERMS_VERSION + "x"])
def test_without_the_current_version_nothing_starts_and_the_dialog_is_reopened(browser, query):
    client, store = browser
    response = client.get("/auth/oauth/google/start" + query)
    assert response.status_code == 303 and response.headers["location"] == "/#auth=terms"
    assert store.started == 0, "no sign-in state was created"
    assert "set-cookie" not in response.headers, "no flow cookie either"


def test_with_the_current_version_the_visitor_is_sent_on_to_google(browser):
    client, store = browser
    response = client.get(f"/auth/oauth/google/start?terms={TERMS_VERSION}")
    assert response.status_code == 302 and response.headers["location"].startswith("https://accounts.google.com/")
    assert store.started == 1


def test_an_unconfigured_provider_still_reports_that_before_asking_about_terms(monkeypatch):
    monkeypatch.delenv("GOOGLE_OAUTH_CLIENT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_OAUTH_CLIENT_SECRET", raising=False)
    client = TestClient(create_app(), follow_redirects=False)
    assert client.get("/auth/oauth/google/start").status_code == 503


def test_the_sign_in_dialog_has_the_checkbox_and_links_to_both_documents():
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    assert 'id="terms-consent"' in html and f'data-terms-version="{TERMS_VERSION}"' in html
    start = html.index('id="terms-consent"')
    row = html[start - 300 : start + 900]
    assert 'href="/terms"' in row and 'href="/privacy"' in row, "the visitor can read both before ticking"
    assert 'id="terms-consent-hint"' in html
    assert html.index('id="terms-consent"') < html.index('id="oauth-provider-list"'), "the checkbox comes before the sign-in buttons"


def test_the_page_script_refuses_to_leave_until_ticked_and_sends_the_version():
    script = (STATIC / "app.js").read_text(encoding="utf-8")
    assert "terms-consent" in script and "?terms=" in script
    assert "#auth=terms" in script, "the reminder redirect from the server is handled"


def test_both_documents_carry_the_version_the_server_demands():
    for name in ("privacy.html", "terms.html"):
        assert f"更新日期：{TERMS_VERSION}" in (STATIC / name).read_text(encoding="utf-8"), name


def test_the_contract_documents_the_new_parameter(browser):
    client, _ = browser
    spec = client.get("/openapi.json").json()
    params = {p["name"] for p in spec["paths"]["/auth/oauth/{provider}/start"]["get"]["parameters"]}
    assert "terms" in params
