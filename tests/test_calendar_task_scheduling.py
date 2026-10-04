from __future__ import annotations

import hashlib
from datetime import date, timedelta

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.calendar_task_scheduling import build_calendar_task_schedule
from exchange_info.models import (
    AccountCalendarEvent,
    AccountSessionRecord,
    UserAccount,
    utc_now,
)
from exchange_info.storage import save_account_sessions, save_user_accounts


def _event(
    event_id: str,
    deadline: str,
    preparation_days: int,
    *,
    status: str = "todo",
) -> AccountCalendarEvent:
    return AccountCalendarEvent(
        id=event_id,
        title=f"任務 {event_id}",
        date=deadline,
        school_name="A 大學",
        preparation_days=preparation_days,
        status=status,
    )


def _authenticated_client(tmp_path) -> tuple[TestClient, dict[str, str]]:
    account = UserAccount(email="schedule@example.com", display_name="排程學生")
    token = "calendar-schedule-token"
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


def test_schedule_uses_only_user_provided_preparation_days() -> None:
    report = build_calendar_task_schedule(
        [
            _event("future", "2027-06-15", 30),
            _event("start", "2027-05-10", 10, status="preparing"),
            _event("soon", "2027-05-03", 7),
            _event("late", "2027-04-20", 14),
            _event("done", "2027-05-20", 20, status="ready"),
            _event("no-estimate", "2027-05-10", 0),
            _event("invalid", "2027-99-99", 10),
        ],
        as_of=date(2027, 5, 1),
    )

    assert report.analyzed_event_count == 5
    assert report.incomplete_count == 4
    assert report.scheduled_count == 1
    assert report.start_now_count == 1
    assert report.due_soon_count == 1
    assert report.overdue_count == 1
    assert report.completed_count == 1
    by_id = {item.event_id: item for item in report.items}
    assert by_id["future"].suggested_start_date == date(2027, 5, 16)
    assert by_id["future"].recommended_reminder_days == [30, 15, 7, 3, 1, 0]
    assert by_id["done"].recommended_reminder_days == []
    assert "no-estimate" not in by_id
    assert "invalid" not in by_id


def test_schedule_deduplicates_events_and_ignores_generated_start_markers() -> None:
    generated = _event("generated", "2027-05-01", 5)
    generated = generated.model_copy(update={"generated_from_event_id": "base"})
    report = build_calendar_task_schedule(
        [
            _event("base", "2027-05-10", 5),
            _event("base", "2027-05-12", 6),
            generated,
        ],
        as_of=date(2027, 5, 1),
    )

    assert report.analyzed_event_count == 1
    assert report.items[0].event_id == "base"
    assert report.items[0].deadline_date == date(2027, 5, 12)
    assert report.items[0].preparation_days == 6


def test_schedule_api_is_entitled_read_only_and_no_store(tmp_path) -> None:
    client, headers = _authenticated_client(tmp_path)
    response = client.post(
        "/calendar/tasks/schedule",
        headers=headers,
        json={
            "as_of": "2027-05-01",
            "events": [_event("task", "2027-05-10", 5).model_dump(mode="json")],
        },
    )

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.json()["items"][0]["suggested_start_date"] == "2027-05-05"


def test_schedule_api_requires_login_and_subscription_in_public_mode(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("EXCHANGE_PRODUCT_RELEASE_MODE", "public")
    client, headers = _authenticated_client(tmp_path)
    payload = {
        "as_of": "2027-05-01",
        "events": [_event("task", "2027-05-10", 5).model_dump(mode="json")],
    }

    assert client.post("/calendar/tasks/schedule", json=payload).status_code == 401
    denied = client.post("/calendar/tasks/schedule", headers=headers, json=payload)
    assert denied.status_code == 403
    assert "進階功能" in denied.json()["detail"]
