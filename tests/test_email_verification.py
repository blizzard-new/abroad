from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from exchange_info.email_verification import (
    EmailVerificationConfigurationError,
    EmailVerificationExpiredError,
    EmailVerificationInvalidError,
    EmailVerificationRateLimitError,
    EmailVerificationService,
    SmtpVerificationEmailSender,
    create_email_verification_service,
)
from exchange_info.repositories import JsonlAccountRepository
from exchange_info.storage import data_paths, ensure_data_dirs, load_email_verifications

BASE_TIME = datetime(2026, 7, 29, 1, 0, tzinfo=timezone.utc)


class _CapturingSender:
    development_mode = False

    def __init__(self) -> None:
        self.messages: list[tuple[str, str, int]] = []

    def send(self, email: str, code: str, expires_in_minutes: int) -> None:
        self.messages.append((email, code, expires_in_minutes))


def _service(tmp_path: Path) -> tuple[EmailVerificationService, _CapturingSender]:
    ensure_data_dirs(tmp_path)
    sender = _CapturingSender()
    service = EmailVerificationService(
        JsonlAccountRepository(tmp_path),
        b"e" * 32,
        sender,
    )
    return service, sender


def test_email_and_code_are_not_stored_in_plaintext(tmp_path) -> None:
    service, sender = _service(tmp_path)
    dispatch = service.request_code("Student@Example.com", now=BASE_TIME)
    email, code, expires_in_minutes = sender.messages[0]

    assert email == "student@example.com"
    assert expires_in_minutes == 15
    assert dispatch.development_code is None
    raw = data_paths(tmp_path)["email_verifications"].read_text(encoding="utf-8")
    assert "student@example.com" not in raw
    assert code not in raw
    row = load_email_verifications(tmp_path)[0]
    assert len(row.email_fingerprint) == 64
    assert len(row.code_hash) == 64


def test_code_confirmation_is_expiring_attempt_limited_and_single_use(tmp_path) -> None:
    service, sender = _service(tmp_path)
    service.request_code("student@example.com", now=BASE_TIME)
    code = sender.messages[-1][1]

    with pytest.raises(EmailVerificationRateLimitError):
        service.request_code(
            "student@example.com",
            now=BASE_TIME + timedelta(seconds=20),
        )
    with pytest.raises(EmailVerificationInvalidError):
        service.confirm_code(
            "student@example.com",
            "000000" if code != "000000" else "999999",
            now=BASE_TIME + timedelta(minutes=1),
        )

    confirmation = service.confirm_code(
        "student@example.com",
        code,
        now=BASE_TIME + timedelta(minutes=2),
    )
    service.consume_registration_token(
        "student@example.com",
        confirmation.verification_token,
        now=BASE_TIME + timedelta(minutes=3),
    )
    with pytest.raises(EmailVerificationInvalidError):
        service.consume_registration_token(
            "student@example.com",
            confirmation.verification_token,
            now=BASE_TIME + timedelta(minutes=4),
        )

    service.request_code(
        "expired@example.com",
        now=BASE_TIME,
    )
    expired_code = sender.messages[-1][1]
    with pytest.raises(EmailVerificationExpiredError):
        service.confirm_code(
            "expired@example.com",
            expired_code,
            now=BASE_TIME + timedelta(minutes=16),
        )


def test_development_backend_is_explicit_and_production_fails_closed(tmp_path) -> None:
    service = create_email_verification_service(
        JsonlAccountRepository(tmp_path),
        tmp_path,
        {"EXCHANGE_ENVIRONMENT": "development"},
    )
    dispatch = service.request_code("student@example.com", now=BASE_TIME)
    assert dispatch.development_code and len(dispatch.development_code) == 6

    with pytest.raises(EmailVerificationConfigurationError, match="SECRET"):
        create_email_verification_service(
            JsonlAccountRepository(tmp_path),
            tmp_path,
            {"EXCHANGE_ENVIRONMENT": "production"},
        )


def test_production_smtp_reuses_notification_mail_settings(tmp_path) -> None:
    secret = base64.urlsafe_b64encode(b"s" * 32).decode("ascii").rstrip("=")
    service = create_email_verification_service(
        JsonlAccountRepository(tmp_path),
        tmp_path,
        {
            "EXCHANGE_ENVIRONMENT": "production",
            "EXCHANGE_EMAIL_VERIFICATION_SECRET": secret,
            "EXCHANGE_EMAIL_VERIFICATION_BACKEND": "smtp",
            "EXCHANGE_SMTP_HOST": "smtp.example.com",
            "EXCHANGE_SMTP_PORT": "587",
            "EXCHANGE_SMTP_FROM": "no-reply@example.com",
            "EXCHANGE_SMTP_STARTTLS": "1",
        },
    )

    assert isinstance(service.sender, SmtpVerificationEmailSender)
    assert service.sender.sender == "no-reply@example.com"
    assert service.sender.tls_mode == "starttls"


def test_email_verification_migration_is_server_only() -> None:
    migration = (
        Path(__file__).resolve().parents[1]
        / "supabase"
        / "migrations"
        / "20260728213255_email_verification_challenges.sql"
    ).read_text(encoding="utf-8").casefold()

    assert "enable row level security" in migration
    assert "revoke all" in migration
    assert "from anon, authenticated" in migration
    assert "to service_role" in migration
    assert "grant select, insert, update, delete" in migration
    assert "email text" not in migration
    assert "code text" not in migration
    assert "email_fingerprint" in migration
    assert "code_hash" in migration
