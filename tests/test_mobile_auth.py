from datetime import timedelta
import hashlib
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.legal_pages import TERMS_VERSION
from exchange_info.mobile_auth import MOBILE_PROVIDER, mobile_handoff_url, pkce_challenge
from exchange_info.models import UserAccount, utc_now
from exchange_info.transient_auth import TransientAuthState, TransientAuthStateKind


def test_mobile_handoff_binds_verifier_is_single_use_and_issues_same_account(tmp_path):
    app = create_app(tmp_path)
    account = UserAccount(display_name="Mobile test")
    app.state.account_repository.save_account(account)
    verifier = "v" * 64
    url = mobile_handoff_url(app, account.id, pkce_challenge(verifier), "s" * 43)
    params = parse_qs(urlparse(url).query)
    assert url.startswith("tw.uniway.app://auth?")
    assert "access_token" not in params
    client = TestClient(app)
    bad = client.post("/auth/mobile/exchange", json={"code": params["code"][0], "code_verifier": "x" * 64})
    assert bad.status_code == 401
    good = client.post("/auth/mobile/exchange", json={"code": params["code"][0], "code_verifier": verifier})
    assert good.status_code == 200
    assert good.json()["profile"]["id"] == account.id
    assert good.headers["cache-control"] == "no-store"
    session = good.json()["access_token"]
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {session}"}).json()["id"] == account.id
    assert client.post("/auth/mobile/exchange", json={"code": params["code"][0], "code_verifier": verifier}).status_code == 401


def test_mobile_handoff_rejects_expired_code(tmp_path):
    app = create_app(tmp_path)
    code = "c" * 43
    app.state.transient_auth_store.save_state(TransientAuthState(
        state_hash=hashlib.sha256(code.encode()).hexdigest(),
        kind=TransientAuthStateKind.OAUTH_LOGIN, provider_id=MOBILE_PROVIDER,
        session_id=pkce_challenge("v" * 64), expires_at=utc_now() + timedelta(seconds=1),
    ))
    with patch("exchange_info.transient_auth.utc_now", return_value=utc_now() + timedelta(minutes=5)):
        assert TestClient(app).post("/auth/mobile/exchange", json={"code": code, "code_verifier": "v" * 64}).status_code == 401


class JsonResponse:
    def __init__(self, value): self.value = value
    def raise_for_status(self): pass
    def json(self): return self.value


def test_google_mobile_login_returns_bound_code_and_normal_web_login_still_works(tmp_path, monkeypatch):
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "test-secret")
    app = create_app(tmp_path)
    client = TestClient(app)
    verifier = "v" * 64
    response = client.get("/auth/oauth/google/start", params={"terms": TERMS_VERSION,
        "mobile_challenge": pkce_challenge(verifier), "mobile_state": "s" * 43}, follow_redirects=False)
    assert response.status_code == 302
    state = parse_qs(urlparse(response.headers["location"]).query)["state"][0]
    with patch("exchange_info.api.requests.post", return_value=JsonResponse({"access_token": "google-token"})), \
         patch("exchange_info.api.requests.get", return_value=JsonResponse({"sub": "google-student", "email": "student@example.com", "email_verified": True, "name": "Student"})):
        callback = client.get("/auth/oauth/google/callback", params={"state": state, "code": "oauth-code"}, follow_redirects=False)
    assert callback.status_code == 303
    params = parse_qs(urlparse(callback.headers["location"]).query)
    assert params["state"] == ["s" * 43]
    exchanged = client.post("/auth/mobile/exchange", json={"code": params["code"][0], "code_verifier": verifier})
    assert exchanged.status_code == 200
    assert exchanged.json()["profile"]["id"] == client.get("/auth/me").json()["id"]


def test_mobile_oauth_parameters_and_terms_are_required(tmp_path, monkeypatch):
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "test-secret")
    client = TestClient(create_app(tmp_path))
    assert client.get("/auth/mobile/config").json()["terms_version"] == TERMS_VERSION
    assert client.get("/auth/oauth/google/start", params={"terms": TERMS_VERSION, "mobile_state": "s" * 43}, follow_redirects=False).status_code == 422
    assert client.get("/auth/oauth/google/start", params={"mobile_challenge": "c" * 43, "mobile_state": "s" * 43}, follow_redirects=False).headers["location"] == "/#auth=terms"
