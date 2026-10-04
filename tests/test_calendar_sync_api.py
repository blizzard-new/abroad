import hashlib
from datetime import timedelta

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.models import (
    AccountSessionRecord,
    ProductAccessTier,
    UserAccount,
    utc_now,
)
from exchange_info.repositories import JsonlAccountRepository
from exchange_info.storage import (
    ensure_data_dirs,
    save_account_sessions,
    save_user_accounts,
)


def _authenticated_client(
    tmp_path,
    *,
    product_tier: ProductAccessTier = ProductAccessTier.FREE,
) -> tuple[TestClient, dict[str, str]]:
    ensure_data_dirs(tmp_path)
    account = UserAccount(
        email="student@example.com",
        display_name="交換生",
        product_tier=product_tier,
    )
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
    assert initial.headers["cache-control"] == "no-store"
    assert initial.headers["x-content-type-options"] == "nosniff"
    assert initial.json() == {
        "enabled": False,
        "subscription_url": None,
        "webcal_url": None,
        "event_count": 0,
        "last_synced_at": None,
    }

    enabled = client.post("/calendar-sync/enable", headers=headers)
    assert enabled.status_code == 200
    assert enabled.headers["cache-control"] == "no-store"
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
                    "school_name": "林肯大學 Lincoln University",
                    "preparation_days": 21,
                    "status": "preparing",
                    "origin": "official",
                },
                {
                    "id": "schedule-start-official-2027-03-30",
                    "title": "開始準備：林肯大學合作校申請截止",
                    "date": "2027-03-09",
                    "category": "documents",
                    "reminder_days": 0,
                    "school_name": "林肯大學 Lincoln University",
                    "generated_from_event_id": "official-2027-03-30",
                    "origin": "personal",
                }
            ]
        },
    )
    assert synced.status_code == 200
    assert synced.headers["cache-control"] == "no-store"
    assert synced.json()["event_count"] == 2
    assert synced.json()["last_synced_at"] is not None

    feed = client.get(synced.json()["subscription_url"])
    assert feed.status_code == 200
    assert feed.headers["content-type"].startswith("text/calendar")
    assert "BEGIN:VCALENDAR" in feed.text
    assert "[交換申請] 林肯大學合作校申請截止" in feed.text
    assert "[交換申請] 開始準備：林肯大學合作校申請截止" in feed.text
    assert "https://example.edu/exchange" in feed.text
    assert feed.text.count("BEGIN:VALARM") == 6
    assert "TRIGGER:PT0M" in feed.text
    for trigger in ["-P30D", "-P14D", "-P7D", "-P3D", "-P1D"]:
        assert f"TRIGGER:{trigger}" in feed.text

    preferences = client.patch(
        "/auth/me",
        headers=headers,
        json={
            "notification_preferences": {
                "deadline_reminder_days": [14, 3],
                "web_enabled": False,
                "email_enabled": False,
                "push_enabled": False,
                "content_updates_enabled": True,
            }
        },
    )
    assert preferences.status_code == 200
    assert preferences.json()["notification_preferences"][
        "deadline_reminder_days"
    ] == [14, 3]
    updated_feed = client.get(synced.json()["subscription_url"])
    assert updated_feed.text.count("BEGIN:VALARM") == 3

    completed = client.put(
        "/calendar-sync/events",
        headers=headers,
        json={
            "events": [
                {
                    "id": "official-2027-03-30",
                    "title": "林肯大學合作校申請截止",
                    "date": "2027-03-30",
                    "category": "partner",
                    "preparation_days": 21,
                    "status": "ready",
                    "origin": "official",
                }
            ]
        },
    )
    assert completed.status_code == 200
    assert completed.json()["event_count"] == 1
    completed_feed = client.get(synced.json()["subscription_url"])
    assert "林肯大學合作校申請截止" in completed_feed.text
    assert "BEGIN:VALARM" not in completed_feed.text

    revoked = client.delete("/calendar-sync", headers=headers)
    assert revoked.status_code == 200
    assert revoked.headers["cache-control"] == "no-store"
    assert revoked.json()["enabled"] is False
    assert client.get(synced.json()["subscription_url"]).status_code == 404


def test_calendar_sync_requires_login(tmp_path) -> None:
    ensure_data_dirs(tmp_path)
    client = TestClient(create_app(tmp_path))

    assert client.get("/calendar-sync").status_code == 401
    assert client.post("/calendar-sync/enable").status_code == 401
    assert client.put("/calendar-sync/events", json={"events": []}).status_code == 401


def test_public_free_account_cannot_use_external_calendar_but_can_revoke(
    tmp_path,
    monkeypatch,
) -> None:
    client, headers = _authenticated_client(tmp_path)
    enabled = client.post("/calendar-sync/enable", headers=headers)
    assert enabled.status_code == 200
    feed_url = enabled.json()["subscription_url"]
    assert client.get(feed_url).status_code == 200

    monkeypatch.setenv("EXCHANGE_PRODUCT_RELEASE_MODE", "public")

    status = client.get("/calendar-sync", headers=headers)
    assert status.status_code == 403
    assert status.json()["detail"] == "外部日曆同步屬於進階功能，目前帳號尚未開放。"
    assert client.post("/calendar-sync/enable", headers=headers).status_code == 403
    assert client.put(
        "/calendar-sync/events",
        headers=headers,
        json={"events": []},
    ).status_code == 403
    assert client.get(feed_url).status_code == 404

    revoked = client.delete("/calendar-sync", headers=headers)
    assert revoked.status_code == 200
    assert revoked.json()["enabled"] is False
    assert revoked.headers["cache-control"] == "no-store"
    assert client.get(feed_url).status_code == 404


def test_public_subscription_account_can_use_external_calendar(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("EXCHANGE_PRODUCT_RELEASE_MODE", "public")
    client, headers = _authenticated_client(
        tmp_path,
        product_tier=ProductAccessTier.SUBSCRIPTION,
    )

    assert client.get("/calendar-sync", headers=headers).status_code == 200
    enabled = client.post("/calendar-sync/enable", headers=headers)
    assert enabled.status_code == 200
    assert client.get(enabled.json()["subscription_url"]).status_code == 200
    assert client.put(
        "/calendar-sync/events",
        headers=headers,
        json={"events": []},
    ).status_code == 200


def test_stale_calendar_sync_cannot_restore_revoked_feed_token(tmp_path) -> None:
    class RevokeBeforeConditionalSyncRepository(JsonlAccountRepository):
        revoke_before_sync = False

        def patch_account_fields(self, account_id, updates, *, expected=None):
            if self.revoke_before_sync and "calendar_events" in updates and expected:
                self.revoke_before_sync = False
                super().patch_account_fields(
                    account_id,
                    {
                        "calendar_feed_token": None,
                        "calendar_events": [],
                        "calendar_last_synced_at": None,
                    },
                )
            return super().patch_account_fields(
                account_id,
                updates,
                expected=expected,
            )

    ensure_data_dirs(tmp_path)
    repository = RevokeBeforeConditionalSyncRepository(tmp_path)
    account = repository.create_account(
        UserAccount(
            email="race@example.com",
            display_name="Race",
            product_tier=ProductAccessTier.SUBSCRIPTION,
        )
    )
    access_token = "calendar-race-access-token"
    repository.save_session(
        AccountSessionRecord(
            account_id=account.id,
            token_hash=hashlib.sha256(access_token.encode("utf-8")).hexdigest(),
            expires_at=utc_now() + timedelta(days=1),
        )
    )
    client = TestClient(create_app(tmp_path, account_repository=repository))
    headers = {"Authorization": f"Bearer {access_token}"}
    assert client.post("/calendar-sync/enable", headers=headers).status_code == 200
    repository.revoke_before_sync = True

    stale_sync = client.put(
        "/calendar-sync/events",
        headers=headers,
        json={"events": []},
    )

    assert stale_sync.status_code == 409
    persisted = repository.find_account_by_id(account.id)
    assert persisted is not None
    assert persisted.calendar_feed_token is None
    assert persisted.calendar_events == []
