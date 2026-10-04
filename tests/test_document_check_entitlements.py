import hashlib
from datetime import timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.models import (
    AccountSessionRecord,
    ProductAccessTier,
    UserAccount,
    utc_now,
)
from exchange_info.storage import (
    ensure_data_dirs,
    save_account_sessions,
    save_user_accounts,
)


def _authenticated_client(
    data_dir: Path,
    *,
    tier: ProductAccessTier,
) -> TestClient:
    ensure_data_dirs(data_dir)
    account = UserAccount(display_name="文件檢查學生", product_tier=tier)
    token = f"document-check-{tier.value}-token"
    save_user_accounts([account], data_dir)
    save_account_sessions(
        [
            AccountSessionRecord(
                account_id=account.id,
                token_hash=hashlib.sha256(token.encode("utf-8")).hexdigest(),
                expires_at=utc_now() + timedelta(days=1),
            )
        ],
        data_dir,
    )
    client = TestClient(create_app(data_dir))
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


def _request(
    client: TestClient,
    path: str = "/document-check",
    *,
    use_ai: bool = False,
    consent: bool | None = True,
):
    data = {
        "document_type": "study_plan",
        "require_signature": "false",
        "use_ai": str(use_ai).lower(),
    }
    if consent is not None:
        data["consent"] = str(consent).lower()
    return client.post(
        path,
        files={
            "file": (
                "讀書計畫.txt",
                "申請動機、預計修課內容、返國後學習規劃。" * 30,
                "text/plain",
            )
        },
        data=data,
    )


def test_document_check_requires_login_and_subscription_in_public_mode(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("EXCHANGE_PRODUCT_RELEASE_MODE", "public")
    guest = TestClient(create_app(tmp_path / "guest"))
    free = _authenticated_client(tmp_path / "free", tier=ProductAccessTier.FREE)
    subscription = _authenticated_client(
        tmp_path / "subscription",
        tier=ProductAccessTier.SUBSCRIPTION,
    )

    assert _request(guest).status_code == 401
    assert _request(guest, "/ai/review-document").status_code == 401

    denied = _request(free)
    assert denied.status_code == 403
    assert "進階功能" in denied.json()["detail"]
    assert _request(free, "/ai/review-document").status_code == 403

    allowed = _request(subscription)
    assert allowed.status_code == 200
    assert allowed.json()["ai_enhanced"] is False
    assert "不會保存原檔" in allowed.json()["privacy_note"]
    assert allowed.headers["cache-control"] == "no-store"
    assert allowed.headers["x-content-type-options"] == "nosniff"


def test_document_check_requires_fresh_explicit_transfer_consent(tmp_path) -> None:
    client = _authenticated_client(
        tmp_path,
        tier=ProductAccessTier.SUBSCRIPTION,
    )

    omitted = _request(client, consent=None)
    denied = _request(client, consent=False)
    allowed = _request(client, consent=True)

    assert omitted.status_code == 422
    assert denied.status_code == 422
    assert "同意" in denied.json()["detail"]
    assert allowed.status_code == 200


def test_ai_document_review_stays_paused_even_for_subscription(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("EXCHANGE_PRODUCT_RELEASE_MODE", "public")
    client = _authenticated_client(
        tmp_path,
        tier=ProductAccessTier.SUBSCRIPTION,
    )

    response = _request(client, use_ai=True)
    compatibility_response = _request(client, "/ai/review-document")

    assert response.status_code == 503
    assert "AI 深度檢查目前暫緩" in response.json()["detail"]
    assert compatibility_response.status_code == 503
    assert "AI 深度檢查目前暫緩" in compatibility_response.json()["detail"]
