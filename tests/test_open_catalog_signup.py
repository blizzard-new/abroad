"""Open catalogue launch: Google-only accounts whose school comes from a verified school address."""
from __future__ import annotations

from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

from exchange_info.legal_pages import TERMS_VERSION
from exchange_info.access_control import (
    HOME_UNIVERSITY_UNSET,
    SCHOOL_EMAIL_DOMAINS,
    catalog_home_university,
    school_basis,
    school_from_email,
)
from exchange_info.api import create_app
from exchange_info.models import UserAccount
from exchange_info.storage import ensure_data_dirs
from exchange_info.university_registry import SUPPORTED_UNIVERSITIES

CGU = "長庚大學"
NTPU = "國立臺北大學"


class _Json:
    def __init__(self, payload: object) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self.payload


@pytest.mark.parametrize("email,school", [
    ("b1128003@cgu.edu.tw", CGU),
    ("B1128003@CGU.EDU.TW", CGU),
    ("someone@mail.cgu.edu.tw", CGU),
    ("s410000001@gm.ntpu.edu.tw", NTPU),
    ("s410000001@ms.ntpu.edu.tw", NTPU),
    ("teacher@ntpu.edu.tw", NTPU),
    ("b10901001@ntu.edu.tw", "國立臺灣大學"),
    ("b10901001@g.ntu.edu.tw", "國立臺灣大學"),
    ("s610000001@ccu.edu.tw", "國立中正大學"),
    ("s610000001@alum.ccu.edu.tw", "國立中正大學"),
    ("110502001@cc.ncu.edu.tw", "國立中央大學"),
    ("110502001@g.ncu.edu.tw", "國立中央大學"),
    ("410000001@gms.tku.edu.tw", "淡江大學"),
    ("410000001@o365.tku.edu.tw", "淡江大學"),
    ("a@gmail.com", None),
    ("a@evilcgu.edu.tw", None),
    ("a@cgu.edu.tw.evil.example", None),
    ("cgu.edu.tw", None),
    ("", None),
    (None, None),
])
def test_only_a_real_school_domain_names_the_school(email, school):
    found = school_from_email(email)
    assert (found.school_name if found else None) == school


def test_every_supported_university_has_registered_email_domains():
    assert set(SCHOOL_EMAIL_DOMAINS) == {u.id for u in SUPPORTED_UNIVERSITIES}
    for university in SUPPORTED_UNIVERSITIES:
        domains = SCHOOL_EMAIL_DOMAINS[university.id]
        assert domains, university.id
        for domain in domains:
            assert school_from_email(f"student@{domain}") == university


def test_school_basis_separates_proof_from_inference_and_choice():
    base = {"display_name": "測試同學"}
    verified = UserAccount(**base, student_status_verified=True, verified_university=NTPU, home_university=CGU)
    assert (catalog_home_university(verified), school_basis(verified)) == (NTPU, "student_verified")
    by_mail = UserAccount(**base, email="b1128003@cgu.edu.tw", email_verified=True, home_university=CGU)
    assert school_basis(by_mail) == "school_email"
    # An unverified address proves nothing, and a school mail does not override a different choice.
    assert school_basis(UserAccount(**base, email="b1128003@cgu.edu.tw", home_university=CGU)) == "self_declared"
    assert school_basis(UserAccount(**base, email="b1128003@cgu.edu.tw", email_verified=True, home_university=NTPU)) == "self_declared"
    assert school_basis(UserAccount(**base, home_university="北大")) == "self_declared"
    unset = UserAccount(**base, home_university=HOME_UNIVERSITY_UNSET)
    assert (catalog_home_university(unset), school_basis(unset)) == (None, None)
    other = UserAccount(**base, home_university="國立某某大學")
    assert (catalog_home_university(other), school_basis(other)) == (None, None)


@pytest.fixture
def google(tmp_path, monkeypatch):
    ensure_data_dirs(tmp_path)
    monkeypatch.setenv("EXCHANGE_AUTH_METHODS", "google")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "google-client-id")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "google-client-secret")

    def sign_in(subject: str, email: str | None, *, verified: bool = True, client: TestClient | None = None):
        browser = client or TestClient(create_app(tmp_path))
        start = browser.get(f"/auth/oauth/google/start?terms={TERMS_VERSION}", follow_redirects=False)
        assert start.status_code == 302
        state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]
        user = {"sub": subject, "name": "測試同學", "email_verified": verified}
        if email is not None:
            user["email"] = email
        with (
            patch("exchange_info.api.requests.post", return_value=_Json({"access_token": "token"})),
            patch("exchange_info.api.requests.get", return_value=_Json(user)),
        ):
            done = browser.get(
                "/auth/oauth/google/callback",
                params={"state": state, "code": "authorization-code"},
                follow_redirects=False,
            )
        assert done.status_code == 303, done.text
        return browser, browser.get("/auth/session").json()

    return sign_in


def test_school_google_mail_opens_on_that_school_without_any_card_check(google):
    _, cgu = google("sub-cgu", "b1128003@cgu.edu.tw")
    assert cgu["home_university"] == CGU
    assert (cgu["catalog_home_university"], cgu["school_basis"]) == (CGU, "school_email")
    assert cgu["email_verified"] is True and cgu["student_status_verified"] is False
    _, ntpu = google("sub-ntpu", "s410000001@gm.ntpu.edu.tw")
    assert (ntpu["catalog_home_university"], ntpu["school_basis"]) == (NTPU, "school_email")


def test_ordinary_gmail_has_no_school_until_the_person_chooses_one(google):
    browser, profile = google("sub-gmail", "someone@gmail.com")
    assert profile["home_university"] == HOME_UNIVERSITY_UNSET
    assert (profile["catalog_home_university"], profile["school_basis"]) == (None, None)
    assert profile["email_verified"] is True and profile["student_status_verified"] is False
    assert browser.get("/student-dashboard").status_code == 200

    chosen = browser.patch("/auth/me", json={"home_university": "北大"})
    assert chosen.status_code == 200
    assert (chosen.json()["catalog_home_university"], chosen.json()["school_basis"]) == (NTPU, "self_declared")

    _, again = google("sub-gmail", "someone@gmail.com")
    assert again["catalog_home_university"] == NTPU, "signing in again keeps the school that was chosen"


def test_an_unverified_school_address_is_not_used_to_pick_the_school(google):
    _, profile = google("sub-unverified", "b1128003@cgu.edu.tw", verified=False)
    assert profile["home_university"] == HOME_UNIVERSITY_UNSET
    assert profile["email"] is None and profile["email_verified"] is False


def test_google_is_the_only_way_to_sign_up_unless_a_deployment_adds_more(tmp_path, monkeypatch):
    ensure_data_dirs(tmp_path)
    monkeypatch.delenv("EXCHANGE_AUTH_METHODS", raising=False)
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "google-client-id")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "google-client-secret")
    monkeypatch.setenv("FACEBOOK_APP_ID", "facebook-id")
    monkeypatch.setenv("FACEBOOK_APP_SECRET", "facebook-secret")
    client = TestClient(create_app(tmp_path))

    enabled = {row["provider"]: row["enabled"] for row in client.get("/auth/providers").json()}
    assert enabled == {"email": False, "google": True, "facebook": False, "apple": False}
    register = {
        "email": "someone@example.com", "password": "correct-horse-battery", "display_name": "測試同學",
        "email_verification_token": "x" * 32, "accept_terms": True,
    }
    assert client.post("/auth/register", json=register).status_code == 403
    assert client.post("/auth/login", json={"email": "someone@example.com", "password": "correct-horse-battery"}).status_code == 403
    assert client.post("/auth/email-verification/request", json={"email": "someone@example.com"}).status_code == 403
    assert client.get(f"/auth/oauth/facebook/start?terms={TERMS_VERSION}", follow_redirects=False).status_code == 403
    assert client.get(f"/auth/oauth/google/start?terms={TERMS_VERSION}", follow_redirects=False).status_code == 302

    monkeypatch.setenv("EXCHANGE_AUTH_METHODS", "email,google")
    both = {row["provider"]: row["enabled"] for row in TestClient(create_app(tmp_path)).get("/auth/providers").json()}
    assert both["email"] is True and both["google"] is True and both["facebook"] is False
