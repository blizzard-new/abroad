"""Defensive regression tests for codebase security audit remediations."""

from __future__ import annotations

from datetime import timedelta
import hashlib
import io
from pathlib import Path
import zipfile

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from starlette.requests import Request

from exchange_info.analytics import RateLimiter
from exchange_info.api import AUTH_COOKIE_NAME, create_app
from exchange_info.content_summary import _is_safe_public_https_url
from exchange_info.document_checker import MAX_DOCX_UNCOMPRESSED_BYTES, check_document
from exchange_info.models import (
    AccountProfileUpdate,
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


def _build_request(
    *,
    host_header: str = "app.uniway-tw.com",
    peer_ip: str = "127.0.0.1",
    extra_headers: dict[str, str] | None = None,
) -> Request:
    headers = [(b"host", host_header.encode("latin-1"))]
    for key, value in (extra_headers or {}).items():
        headers.append((key.lower().encode("latin-1"), value.encode("latin-1")))
    scope = {
        "type": "http",
        "method": "GET",
        "scheme": "https",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": headers,
        "client": (peer_ip, 54321),
        "server": ("127.0.0.1", 8000),
    }
    return Request(scope)


def _seed_account_with_session(
    data_dir: Path,
    *,
    email: str = "student@example.edu.tw",
    tier: ProductAccessTier = ProductAccessTier.FREE,
    raw_token: str = "valid-session-token-0123456789abcdef",
) -> tuple[UserAccount, str]:
    ensure_data_dirs(data_dir)
    account = UserAccount(email=email, display_name="Test Student", product_tier=tier)
    save_user_accounts([account], data_dir)
    save_account_sessions(
        [
            AccountSessionRecord(
                account_id=account.id,
                token_hash=hashlib.sha256(raw_token.encode("utf-8")).hexdigest(),
                expires_at=utc_now() + timedelta(days=1),
            )
        ],
        data_dir,
    )
    return account, raw_token


def test_maintenance_router_blocks_spoofed_headers_and_allows_loopback_token(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    token = "maint_secret_token_0123456789abcdef0123456789"
    monkeypatch.setenv("EXCHANGE_MAINTENANCE_AUTOMATION_TOKEN", token)
    app = create_app(data_dir=tmp_path)

    spoofed_headers = {"X-Admin-Id": "admin_kevin", "X-Admin-Role": "super_admin"}
    with TestClient(app, client=("203.0.113.10", 51000)) as public_client:
        assert public_client.get("/admin/sources", headers=spoofed_headers).status_code == 401
        assert public_client.get("/maintenance-preview", headers=spoofed_headers).status_code == 401
        assert public_client.get("/maintenance-preview.js", headers=spoofed_headers).status_code == 401
        assert (
            public_client.get("/admin/sources", headers={"X-Maintenance-Token": token}).status_code
            == 401
        )

    with TestClient(app, client=("127.0.0.1", 51001)) as loopback_client:
        res = loopback_client.get("/admin/sources", headers={"X-Maintenance-Token": token})
        assert res.status_code == 200
        assert "items" in res.json()


def test_document_check_blocks_forged_bearer_tokens_without_valid_session(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("EXCHANGE_PRODUCT_RELEASE_MODE", "public")
    _, valid_sub_token = _seed_account_with_session(
        tmp_path,
        email="sub@example.edu.tw",
        tier=ProductAccessTier.SUBSCRIPTION,
        raw_token="real-subscription-session-token",
    )
    app = create_app(data_dir=tmp_path)
    payload_data = {"document_type": "study_plan", "require_signature": "false", "use_ai": "false", "consent": "true"}
    payload_files = {"file": ("plan.txt", ("申請動機與修課規劃。" * 25).encode("utf-8"), "text/plain")}

    with TestClient(app) as client:
        # Previously any non-"free" Bearer string bypassed auth; ensure forged strings return 401.
        assert (
            client.post(
                "/document-check",
                data=payload_data,
                files=payload_files,
                headers={"Authorization": "Bearer paid-tier-bypass"},
            ).status_code
            == 401
        )
        assert (
            client.post(
                "/ai/review-document",
                data=payload_data,
                files=payload_files,
                headers={"Authorization": "Bearer paid-tier-bypass"},
            ).status_code
            == 401
        )
        assert (
            client.post(
                "/document-check",
                data=payload_data,
                files=payload_files,
                headers={"Authorization": f"Bearer {valid_sub_token}"},
            ).status_code
            == 200
        )


def test_csrf_middleware_blocks_cross_site_cookie_mutations(tmp_path: Path) -> None:
    _, raw_token = _seed_account_with_session(tmp_path, email="csrf@example.edu.tw")
    app = create_app(data_dir=tmp_path)

    with TestClient(app) as client:
        client.cookies.set(AUTH_COOKIE_NAME, raw_token)
        assert (
            client.patch(
                "/auth/me",
                json={"display_name": "Blocked"},
                headers={"Origin": "https://attacker.example"},
            ).status_code
            == 403
        )
        assert (
            client.patch(
                "/auth/me",
                json={"display_name": "Blocked"},
                headers={"Sec-Fetch-Site": "cross-site"},
            ).status_code
            == 403
        )
        ok = client.patch(
            "/auth/me",
            json={"display_name": "Allowed Same Origin"},
            headers={"Origin": "http://testserver", "Sec-Fetch-Site": "same-origin"},
        )
        assert ok.status_code == 200
        assert ok.json()["display_name"] == "Allowed Same Origin"


def test_admin_refresh_routes_reject_unauthenticated_and_regular_users(tmp_path: Path) -> None:
    _, user_token = _seed_account_with_session(tmp_path, email="regular@example.edu.tw")
    app = create_app(data_dir=tmp_path)

    with TestClient(app) as client:
        assert client.post("/destination-profile/refresh", params={"school": "ETH Zurich"}).status_code == 401
        assert client.post("/application-workflow/refresh", params={"school": "ETH Zurich"}).status_code == 401
        assert (
            client.post(
                "/destination-profile/refresh",
                params={"school": "ETH Zurich"},
                headers={"Authorization": f"Bearer {user_token}"},
            ).status_code
            == 403
        )
        assert (
            client.post(
                "/application-workflow/refresh",
                params={"school": "ETH Zurich"},
                headers={"Authorization": f"Bearer {user_token}"},
            ).status_code
            == 403
        )


def test_request_origin_hardening_against_host_and_ip_spoofing() -> None:
    from exchange_info.request_origin import client_address, is_production_environment, public_base_url

    assert is_production_environment({"EXCHANGE_ENVIRONMENT": "PROD"}) is True
    assert is_production_environment({"EXCHANGE_ENVIRONMENT": " production "}) is True
    assert is_production_environment({"EXCHANGE_ENVIRONMENT": "development"}) is False

    spoofed_host_req = _build_request(host_header="evil.example")
    assert public_base_url(spoofed_host_req, {"EXCHANGE_ENVIRONMENT": "production"}) == "https://app.uniway-tw.com"

    direct_public_peer = _build_request(
        peer_ip="198.51.100.25",
        extra_headers={"X-Client-IP": "203.0.113.99"},
    )
    assert client_address(direct_public_peer, {"EXCHANGE_CLIENT_IP_HEADER": "X-Client-IP"}) == "198.51.100.25"

    trusted_loopback_peer = _build_request(
        peer_ip="127.0.0.1",
        extra_headers={"X-Client-IP": "203.0.113.99"},
    )
    assert client_address(trusted_loopback_peer, {"EXCHANGE_CLIENT_IP_HEADER": "X-Client-IP"}) == "203.0.113.99"


def test_rate_limiter_lru_cap_and_url_safety_validators() -> None:
    limiter = RateLimiter(max_batches=2, max_events=2, window_seconds=60, max_keys=5)
    for idx in range(25):
        assert limiter.allow(f"ip-{idx}", 1, now=100.0 + idx * 0.01) is True
    assert len(limiter._hits) <= 5

    assert _is_safe_public_https_url("http://example.com/") is False
    assert _is_safe_public_https_url("file:///etc/passwd") is False
    assert _is_safe_public_https_url("https://127.0.0.1/admin") is False

    with pytest.raises(ValidationError):
        AccountProfileUpdate(avatar_url="http://example.com/a.png")
    with pytest.raises(ValidationError):
        AccountProfileUpdate(avatar_url="javascript:alert(1)")
    with pytest.raises(ValidationError):
        AccountProfileUpdate(avatar_url="https://user:pass@example.com/a.png")
    valid = AccountProfileUpdate(avatar_url="https://example.com/avatar.png")
    assert valid.avatar_url == "https://example.com/avatar.png"


def test_docx_extractor_enforces_actual_stream_byte_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    import exchange_info.document_checker as checker

    monkeypatch.setattr(checker, "MAX_DOCX_UNCOMPRESSED_BYTES", 64)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "word/document.xml",
            "<w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'>"
            + ("<w:t>HelloWorld</w:t>" * 20)
            + "</w:document>",
        )
    assert MAX_DOCX_UNCOMPRESSED_BYTES > 64
    with pytest.raises(ValueError, match="DOCX 壓縮內容過大"):
        check_document(file_name="oversized.docx", content=buf.getvalue())
