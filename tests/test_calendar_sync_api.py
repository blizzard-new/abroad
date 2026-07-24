import hashlib
from datetime import timedelta

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.models import AccountSessionRecord, UserAccount, utc_now
from exchange_info.storage import (
    ensure_data_dirs,
    save_account_sessions,
    save_user_accounts,
)


def _authenticated_client(tmp_path) -> tuple[TestClient, dict[str, str]]:
    ensure_data_dirs(tmp_path)
    account = UserAccount(email="student@example.com", display_name="交換生")
    access_token = "calendar-test-access-token"
    session = AccountSessionRecord(
        account_id=account.id,
        token_hash=hashlib.sha256(access_token.encode("utf-8")).hexdigest(),
        expires_at=utc_now() + timedelta(days=1),
    )
    save_user_accounts([account], tmp_path)
    save_account_sessions([session], tmp_path)
    return TestClient(create_app(tmp_path)), {
        "Authorization": f"Bearer {access_token}"
    }


def test_calendar_subscription_syncs_events_and_can_be_revoked(tmp_path) -> None:
    client, headers = _authenticated_client(tmp_path)

    initial = client.get("/calendar-sync", headers=headers)
    assert initial.status_code == 200
    assert initial.json() == {
        "enabled": False,
        "subscription_url": None,
        "webcal_url": None,
        "event_count": 0,
        "last_synced_at": None,
    }

    enabled = client.post("/calendar-sync/enable", headers=headers)
    assert enabled.status_code == 200
    assert enabled.json()["enabled"] is True
    assert enabled.json()["subscription_url"].startswith(
        "http://testserver/calendar/feed/"
    )
    assert enabled.json()["webcal_url"].startswith("webcal://testserver/")

    synced = client.put(
        "/calendar-sync/events",
        headers=headers,
        json={
            "events": [
                {
                    "id": "official-2027-03-30",
                    "title": "林肯大學合作校申請截止",
                    "date": "2027-03-30",
                    "category": "partner",
                    "reminder_days": 14,
                    "note": "送件前再次核對公告。",
                    "source_url": "https://example.edu/exchange",
                    "origin": "official",
                }
            ]
        },
    )
    assert synced.status_code == 200
    assert synced.json()["event_count"] == 1
    assert synced.json()["last_synced_at"] is not None

    feed = client.get(synced.json()["subscription_url"])
    assert feed.status_code == 200
    assert feed.headers["content-type"].startswith("text/calendar")
    assert "BEGIN:VCALENDAR" in feed.text
    assert "[交換申請] 林肯大學合作校申請截止" in feed.text
    assert "https://example.edu/exchange" in feed.text

    revoked = client.delete("/calendar-sync", headers=headers)
    assert revoked.status_code == 200
    assert revoked.json()["enabled"] is False
    assert client.get(synced.json()["subscription_url"]).status_code == 404


def test_calendar_sync_requires_login(tmp_path) -> None:
    ensure_data_dirs(tmp_path)
    client = TestClient(create_app(tmp_path))

    assert client.get("/calendar-sync").status_code == 401
    assert client.post("/calendar-sync/enable").status_code == 401
    assert client.put("/calendar-sync/events", json={"events": []}).status_code == 401
