"""The student-card check is gone: the school an account picked is shown, and cannot be changed again for three days."""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from exchange_info.access_control import (
    HOME_UNIVERSITY_UNSET,
    SCHOOL_CHANGE_LOCK,
    school_change_locked_until,
)
from exchange_info.api import create_app
from exchange_info.community_repositories import JsonlCommunityRepository, PublicCommunityPublicationStatus
from exchange_info.models import AccountSessionRecord, CommunityIdentityMode, UserAccount, utc_now

CGU = "長庚大學"
NTPU = "國立臺北大學"


def _account(app, *, home_university: str = HOME_UNIVERSITY_UNSET, changed_at=None, email="pick@example.com"):
    account = UserAccount(
        email=email,
        email_verified=True,
        display_name="選學校的學生",
        home_university=home_university,
        home_university_changed_at=changed_at,
    )
    token = f"school-choice-token-{account.id}"
    app.state.account_repository.save_account(account)
    app.state.account_repository.save_session(
        AccountSessionRecord(
            account_id=account.id,
            token_hash=hashlib.sha256(token.encode("utf-8")).hexdigest(),
            expires_at=utc_now() + timedelta(hours=1),
        )
    )
    return account, {"Authorization": f"Bearer {token}"}


def _client(tmp_path: Path):
    app = create_app(tmp_path)
    return app, TestClient(app)


def test_the_first_pick_is_free_and_starts_the_lock(tmp_path: Path) -> None:
    app, client = _client(tmp_path)
    _, headers = _account(app)

    before = client.get("/auth/me", headers=headers).json()
    assert before["catalog_home_university"] is None and before["school_change_locked_until"] is None

    picked = client.patch("/auth/me", headers=headers, json={"home_university": CGU})
    assert picked.status_code == 200
    body = picked.json()
    assert body["catalog_home_university"] == CGU
    assert body["school_basis"] == "self_declared"
    locked_until = body["school_change_locked_until"]
    assert locked_until, "the lock starts when the school is picked"
    assert abs((utc_now() + SCHOOL_CHANGE_LOCK) - datetime.fromisoformat(locked_until)).total_seconds() < 60


def test_changing_the_school_inside_three_days_is_refused_and_leaves_it_unchanged(tmp_path: Path) -> None:
    app, client = _client(tmp_path)
    _, headers = _account(app)
    client.patch("/auth/me", headers=headers, json={"home_university": CGU})

    refused = client.patch("/auth/me", headers=headers, json={"home_university": NTPU})

    assert refused.status_code == 409
    assert "3 天內不能更換" in refused.json()["detail"]
    assert client.get("/auth/me", headers=headers).json()["catalog_home_university"] == CGU


def test_saving_the_same_school_again_is_not_a_change_and_does_not_restart_the_clock(tmp_path: Path) -> None:
    app, client = _client(tmp_path)
    account, headers = _account(app)
    first = client.patch("/auth/me", headers=headers, json={"home_university": CGU}).json()

    again = client.patch("/auth/me", headers=headers, json={"home_university": CGU, "display_name": "改個暱稱"})

    assert again.status_code == 200
    assert again.json()["display_name"] == "改個暱稱"
    assert again.json()["school_change_locked_until"] == first["school_change_locked_until"]


def test_after_three_days_the_school_can_be_changed_and_the_lock_starts_again(tmp_path: Path) -> None:
    app, client = _client(tmp_path)
    old = utc_now() - SCHOOL_CHANGE_LOCK - timedelta(minutes=1)
    _, headers = _account(app, home_university=CGU, changed_at=old)

    assert client.get("/auth/me", headers=headers).json()["school_change_locked_until"] is None
    changed = client.patch("/auth/me", headers=headers, json={"home_university": NTPU})

    assert changed.status_code == 200
    assert changed.json()["catalog_home_university"] == NTPU
    assert changed.json()["school_change_locked_until"], "changing it starts a new lock"
    assert client.patch("/auth/me", headers=headers, json={"home_university": CGU}).status_code == 409


def test_an_account_from_before_the_lock_existed_may_change_once(tmp_path: Path) -> None:
    app, client = _client(tmp_path)
    _, headers = _account(app, home_university=CGU, changed_at=None)

    assert client.patch("/auth/me", headers=headers, json={"home_university": NTPU}).status_code == 200
    assert client.patch("/auth/me", headers=headers, json={"home_university": CGU}).status_code == 409


def test_the_lock_helper_ignores_unset_schools_and_naive_timestamps() -> None:
    now = utc_now()
    unset = UserAccount(display_name="a", home_university=HOME_UNIVERSITY_UNSET, home_university_changed_at=now)
    assert school_change_locked_until(unset) is None
    assert school_change_locked_until(None) is None
    naive = UserAccount(display_name="a", home_university=CGU, home_university_changed_at=now.replace(tzinfo=None))
    assert school_change_locked_until(naive) is not None


def test_the_student_card_endpoints_are_gone(tmp_path: Path) -> None:
    _, client = _client(tmp_path)
    assert client.post("/auth/student-verification").status_code in (404, 405)
    assert client.post("/auth/student-verification/confirm", json={"verification_token": "x" * 20}).status_code in (404, 405)
    paths = client.get("/openapi.json").json()["paths"]
    assert not [path for path in paths if "student-verification" in path]


def test_the_school_identity_option_needs_a_school_not_a_verified_student(tmp_path: Path) -> None:
    app, client = _client(tmp_path)
    _, no_school = _account(app, email="none@example.com")
    _, with_school = _account(app, home_university=CGU, email="has@example.com")

    def option(headers):
        options = client.get("/auth/community-identity-options", headers=headers).json()["options"]
        return next(item for item in options if item["mode"] == "verified_school")

    assert option(no_school)["enabled"] is False
    assert option(with_school)["enabled"] is True
    assert option(with_school)["label"] == f"{CGU}學生"


def test_school_bound_posts_follow_the_picked_school(tmp_path: Path) -> None:
    pick = UserAccount(display_name="a", email_verified=True, home_university=NTPU)
    none = UserAccount(display_name="b", email_verified=True, home_university=HOME_UNIVERSITY_UNSET)

    assert JsonlCommunityRepository._verified_for_school(pick, NTPU) is True
    assert JsonlCommunityRepository._verified_for_school(pick, CGU) is False, "a school's Q&A is for that school's people"
    assert JsonlCommunityRepository._verified_for_school(none, NTPU) is False
    assert JsonlCommunityRepository._display_name_status(pick, CommunityIdentityMode.VERIFIED_SCHOOL) == (None, f"{NTPU}學生")
    status, name = JsonlCommunityRepository._display_name_status(none, CommunityIdentityMode.VERIFIED_SCHOOL)
    assert status == PublicCommunityPublicationStatus.STUDENT_VERIFICATION_REQUIRED and name is None


def test_the_profile_schema_publishes_the_lock(tmp_path: Path) -> None:
    _, client = _client(tmp_path)
    schema = client.get("/openapi.json").json()["components"]["schemas"]["AccountProfile"]["properties"]
    assert "school_change_locked_until" in schema
