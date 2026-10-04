from __future__ import annotations

import hashlib
from datetime import timedelta

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.calendar_conflicts import build_calendar_conflict_report
from exchange_info.models import (
    AccountCalendarEvent,
    AccountSessionRecord,
    UserAccount,
    utc_now,
)
from exchange_info.storage import (
    load_user_accounts,
    save_account_sessions,
    save_user_accounts,
)


def _event(
    event_id: str,
    school_name: str | None,
    event_date: str,
    *,
    title: str | None = None,
) -> AccountCalendarEvent:
    return AccountCalendarEvent(
        id=event_id,
        title=title or f"{school_name or '一般'}任務",
        date=event_date,
        school_name=school_name,
    )


def _authenticated_client(tmp_path) -> tuple[TestClient, dict[str, str]]:
    account = UserAccount(
        email="conflicts@example.com",
        display_name="衝突測試學生",
    )
    token = "calendar-conflict-test-token"
    save_user_accounts([account], tmp_path)
    save_account_sessions(
        [
            AccountSessionRecord(
                account_id=account.id,
                token_hash=hashlib.sha256(token.encode("utf-8")).hexdigest(),
                expires_at=utc_now() + timedelta(days=1),
            )
        ],
        tmp_path,
    )
    return TestClient(create_app(tmp_path)), {"Authorization": f"Bearer {token}"}


def test_same_day_conflict_requires_two_distinct_application_schools() -> None:
    report = build_calendar_conflict_report(
        [
            _event("a-documents", "A 大學", "2027-03-10"),
            _event("a-submit", "A 大學", "2027-03-10"),
            _event("b-submit", "B 大學", "2027-03-10"),
            _event("general", None, "2027-03-10"),
        ]
    )

    assert report.analyzed_event_count == 3
    assert report.plan_count == 2
    assert report.conflict_count == 1
    assert report.conflicting_event_count == 3
    assert report.same_day_conflict_count == 1
    assert report.tight_window_conflict_count == 0
    group = report.groups[0]
    assert group.kind == "same_day"
    assert group.start_date == group.end_date == "2027-03-10"
    assert group.day_gap == 0
    assert group.school_names == ["A 大學", "B 大學"]
    assert {event.id for event in group.events} == {
        "a-documents",
        "a-submit",
        "b-submit",
    }
    assert "同一天" in group.resolution_hint


def test_tight_window_detects_cross_plan_deadlines_up_to_three_days_apart() -> None:
    report = build_calendar_conflict_report(
        [
            _event("a", "A 大學", "2027-04-01"),
            _event("b", "B 大學", "2027-04-04"),
            _event("c", "C 大學", "2027-04-08"),
        ]
    )

    assert report.plan_count == 3
    assert report.conflict_count == 1
    assert report.same_day_conflict_count == 0
    assert report.tight_window_conflict_count == 1
    group = report.groups[0]
    assert group.kind == "tight_window"
    assert group.start_date == "2027-04-01"
    assert group.end_date == "2027-04-04"
    assert group.day_gap == 3
    assert "相距 3 天" in group.resolution_hint


def test_conflict_analysis_ignores_same_plan_invalid_dates_and_duplicate_ids() -> None:
    report = build_calendar_conflict_report(
        [
            _event("same-a", "A 大學", "2027-05-01"),
            _event("same-b", "A 大學", "2027-05-02"),
            _event("invalid", "B 大學", "2027-99-99"),
            _event("duplicate", "B 大學", "2027-05-02"),
            _event("duplicate", "A 大學", "2027-05-02"),
        ]
    )

    assert report.analyzed_event_count == 3
    assert report.plan_count == 1
    assert report.conflict_count == 0
    assert report.groups == []


def test_calendar_conflict_api_is_entitled_read_only_and_no_store(
    tmp_path,
) -> None:
    client, headers = _authenticated_client(tmp_path)
    accounts_before = [row.model_dump_json() for row in load_user_accounts(tmp_path)]
    payload = {
        "events": [
            _event("a", "A 大學", "2027-06-01").model_dump(mode="json"),
            _event("b", "B 大學", "2027-06-01").model_dump(mode="json"),
        ]
    }

    response = client.post(
        "/calendar/conflicts/analyze",
        headers=headers,
        json=payload,
    )

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.json()["conflict_count"] == 1
    assert response.json()["groups"][0]["kind"] == "same_day"
    assert [row.model_dump_json() for row in load_user_accounts(tmp_path)] == (
        accounts_before
    )


def test_calendar_conflict_api_requires_login_and_public_subscription_access(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("EXCHANGE_PRODUCT_RELEASE_MODE", "public")
    client, headers = _authenticated_client(tmp_path)
    payload = {
        "events": [
            _event("a", "A 大學", "2027-06-01").model_dump(mode="json"),
            _event("b", "B 大學", "2027-06-01").model_dump(mode="json"),
        ]
    }

    assert client.post("/calendar/conflicts/analyze", json=payload).status_code == 401
    denied = client.post(
        "/calendar/conflicts/analyze",
        headers=headers,
        json=payload,
    )
    assert denied.status_code == 403
    assert "進階功能" in denied.json()["detail"]
