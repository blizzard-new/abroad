from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import os
import secrets
import smtplib
import ssl
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Protocol

from .models import (
    EmailVerificationChallenge,
    EmailVerificationConfirmation,
    EmailVerificationDispatch,
    utc_now,
)
from .repositories import AccountRepository
from .settings import DEFAULT_DATA_DIR
from .storage import ensure_data_dirs

EMAIL_VERIFICATION_TTL = timedelta(minutes=15)
EMAIL_VERIFICATION_RESEND_COOLDOWN = timedelta(seconds=60)
EMAIL_VERIFICATION_HOURLY_LIMIT = 5
EMAIL_VERIFICATION_MAX_ATTEMPTS = 5


class EmailVerificationError(RuntimeError):
    pass


class EmailVerificationConfigurationError(EmailVerificationError):
    pass


class EmailVerificationDeliveryError(EmailVerificationError):
    pass


class EmailVerificationRateLimitError(EmailVerificationError):
    def __init__(self, message: str, retry_after_seconds: int) -> None:
        super().__init__(message)
        self.retry_after_seconds = max(1, retry_after_seconds)


class EmailVerificationInvalidError(EmailVerificationError):
    pass


class EmailVerificationExpiredError(EmailVerificationError):
    pass


class VerificationEmailSender(Protocol):
    development_mode: bool

    def send(self, email: str, code: str, expires_in_minutes: int) -> None: ...


class DevelopmentVerificationEmailSender:
    development_mode = True

    def send(self, email: str, code: str, expires_in_minutes: int) -> None:
        # The code is returned only by the explicitly selected development backend.
        # It is never printed or written to application logs.
        return None


class DisabledVerificationEmailSender:
    development_mode = False

    def send(self, email: str, code: str, expires_in_minutes: int) -> None:
        raise EmailVerificationDeliveryError(
            "Email 驗證寄送服務尚未設定，請聯絡平台管理者。"
        )


class SmtpVerificationEmailSender:
    development_mode = False

    def __init__(
        self,
        *,
        host: str,
        port: int,
        sender: str,
        username: str | None = None,
        password: str | None = None,
        tls_mode: str = "starttls",
        timeout_seconds: float = 15.0,
    ) -> None:
        if not host.strip() or not sender.strip():
            raise EmailVerificationConfigurationError(
                "SMTP host 與寄件者 Email 必須設定。"
            )
        if tls_mode not in {"starttls", "ssl", "none"}:
            raise EmailVerificationConfigurationError(
                "EXCHANGE_SMTP_TLS 必須是 starttls、ssl 或 none。"
            )
        if bool(username) != bool(password):
            raise EmailVerificationConfigurationError(
                "SMTP 使用者名稱與密碼必須同時設定。"
            )
        self.host = host.strip()
        self.port = port
        self.sender = sender.strip()
        self.username = username
        self.password = password
        self.tls_mode = tls_mode
        self.timeout_seconds = timeout_seconds

    def send(self, email: str, code: str, expires_in_minutes: int) -> None:
        message = EmailMessage()
        message["Subject"] = "留學申請指南 Email 驗證碼"
        message["From"] = self.sender
        message["To"] = email
        message.set_content(
            f"你的驗證碼是 {code}。\n\n"
            f"驗證碼將在 {expires_in_minutes} 分鐘後失效；若不是你本人操作，"
            "請忽略這封信。"
        )
        context = ssl.create_default_context()
        try:
            if self.tls_mode == "ssl":
                client: smtplib.SMTP = smtplib.SMTP_SSL(
                    self.host,
                    self.port,
                    timeout=self.timeout_seconds,
                    context=context,
                )
            else:
                client = smtplib.SMTP(
                    self.host,
                    self.port,
                    timeout=self.timeout_seconds,
                )
            with client:
                if self.tls_mode == "starttls":
                    client.starttls(context=context)
                if self.username and self.password:
                    client.login(self.username, self.password)
                client.send_message(message)
        except (OSError, smtplib.SMTPException) as error:
            raise EmailVerificationDeliveryError(
                "驗證信目前無法寄出，請稍後再試。"
            ) from error


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _decode_secret(value: str) -> bytes:
    candidate = value.strip()
    if candidate.startswith("base64:"):
        candidate = candidate[7:]
    try:
        secret = _unb64(candidate)
    except (ValueError, binascii.Error) as error:
        raise EmailVerificationConfigurationError(
            "EXCHANGE_EMAIL_VERIFICATION_SECRET 必須是 base64url。"
        ) from error
    if len(secret) != 32:
        raise EmailVerificationConfigurationError(
            "EXCHANGE_EMAIL_VERIFICATION_SECRET 解碼後必須是 32 bytes。"
        )
    return secret


def _local_development_secret(data_dir: Path) -> bytes:
    paths = ensure_data_dirs(data_dir)
    secret_path = paths["email_verification_secret"]
    if secret_path.exists():
        return _decode_secret(secret_path.read_text(encoding="ascii"))
    secret = secrets.token_bytes(32)
    secret_path.write_text(_b64(secret), encoding="ascii")
    try:
        secret_path.chmod(0o600)
    except OSError:
        pass
    return secret


def mask_email(email: str) -> str:
    local, _, domain = email.partition("@")
    if not domain:
        return "***"
    visible = local[:1]
    return f"{visible}{'*' * max(2, len(local) - 1)}@{domain}"


class EmailVerificationService:
    def __init__(
        self,
        repository: AccountRepository,
        secret: bytes,
        sender: VerificationEmailSender,
    ) -> None:
        if len(secret) != 32:
            raise EmailVerificationConfigurationError(
                "Email 驗證服務 secret 必須是 32 bytes。"
            )
        import threading

        self._lock = threading.RLock()
        self.repository = repository
        self._secret = secret
        self.sender = sender

    @staticmethod
    def normalize_email(email: str) -> str:
        return email.strip().casefold()

    def email_fingerprint(self, email: str) -> str:
        normalized = self.normalize_email(email)
        return hmac.new(
            self._secret,
            f"email:{normalized}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _challenge_hash(self, challenge_id: str, kind: str, value: str) -> str:
        return hmac.new(
            self._secret,
            f"{kind}:{challenge_id}:{value}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def request_code(
        self,
        email: str,
        *,
        now: datetime | None = None,
    ) -> EmailVerificationDispatch:
        with self._lock:
            current = _aware_utc(now or utc_now())
            normalized = self.normalize_email(email)
            fingerprint = self.email_fingerprint(normalized)
            rows = self.repository.list_email_verifications(fingerprint)
            active = [
                row
                for row in rows
                if row.consumed_at is None and row.expires_at > current
            ]
            if active and active[0].resend_available_at > current:
                retry_after = int(
                    (active[0].resend_available_at - current).total_seconds()
                )
                raise EmailVerificationRateLimitError(
                    "驗證碼剛剛已寄出，請稍後再試。",
                    retry_after,
                )
            recent = [
                row
                for row in rows
                if row.requested_at >= current - timedelta(hours=1)
            ]
            if len(recent) >= EMAIL_VERIFICATION_HOURLY_LIMIT:
                retry_at = min(row.requested_at for row in recent) + timedelta(hours=1)
                raise EmailVerificationRateLimitError(
                    "驗證碼要求次數過多，請稍後再試。",
                    int((retry_at - current).total_seconds()),
                )
            code = f"{secrets.randbelow(1_000_000):06d}"
            challenge = EmailVerificationChallenge(
                email_fingerprint=fingerprint,
                code_hash="0" * 64,
                requested_at=current,
                resend_available_at=current + EMAIL_VERIFICATION_RESEND_COOLDOWN,
                expires_at=current + EMAIL_VERIFICATION_TTL,
            )
            challenge = challenge.model_copy(
                update={
                    "code_hash": self._challenge_hash(challenge.id, "code", code)
                }
            )
            self.repository.save_email_verification(challenge)
            try:
                self.sender.send(
                    normalized,
                    code,
                    int(EMAIL_VERIFICATION_TTL.total_seconds() // 60),
                )
            except EmailVerificationDeliveryError:
                self.repository.save_email_verification(
                    challenge.model_copy(update={"consumed_at": current})
                )
                raise
            return EmailVerificationDispatch(
                email_hint=mask_email(normalized),
                expires_at=challenge.expires_at,
                resend_available_at=challenge.resend_available_at,
                development_code=code if self.sender.development_mode else None,
            )

    def confirm_code(
        self,
        email: str,
        code: str,
        *,
        now: datetime | None = None,
    ) -> EmailVerificationConfirmation:
        with self._lock:
            current = _aware_utc(now or utc_now())
            fingerprint = self.email_fingerprint(email)
            rows = self.repository.list_email_verifications(fingerprint)
            challenge = next(
                (
                    row
                    for row in rows
                    if row.consumed_at is None and row.confirmed_at is None
                ),
                None,
            )
            if challenge is None:
                raise EmailVerificationInvalidError(
                    "找不到可使用的驗證碼，請重新寄送。"
                )
            if challenge.expires_at <= current:
                raise EmailVerificationExpiredError(
                    "驗證碼已過期，請重新寄送。"
                )
            if challenge.attempt_count >= EMAIL_VERIFICATION_MAX_ATTEMPTS:
                raise EmailVerificationInvalidError(
                    "驗證嘗試次數已達上限，請重新寄送。"
                )
            expected = self._challenge_hash(challenge.id, "code", code)
            if not hmac.compare_digest(challenge.code_hash, expected):
                attempts = challenge.attempt_count + 1
                self.repository.save_email_verification(
                    challenge.model_copy(
                        update={
                            "attempt_count": attempts,
                            "consumed_at": (
                                current
                                if attempts >= EMAIL_VERIFICATION_MAX_ATTEMPTS
                                else None
                            ),
                        }
                    )
                )
                raise EmailVerificationInvalidError("驗證碼不正確。")
            token = secrets.token_urlsafe(40)
            confirmed = challenge.model_copy(
                update={
                    "confirmation_token_hash": self._challenge_hash(
                        challenge.id,
                        "confirmation",
                        token,
                    ),
                    "confirmed_at": current,
                }
            )
            self.repository.save_email_verification(confirmed)
            return EmailVerificationConfirmation(
                verification_token=token,
                expires_at=confirmed.expires_at,
            )

    def consume_registration_token(
        self,
        email: str,
        token: str,
        *,
        now: datetime | None = None,
    ) -> None:
        with self._lock:
            current = _aware_utc(now or utc_now())
            fingerprint = self.email_fingerprint(email)
            for challenge in self.repository.list_email_verifications(fingerprint):
                if (
                    challenge.confirmed_at is None
                    or challenge.consumed_at is not None
                    or challenge.expires_at <= current
                    or challenge.confirmation_token_hash is None
                ):
                    continue
                expected = self._challenge_hash(challenge.id, "confirmation", token)
                if hmac.compare_digest(challenge.confirmation_token_hash, expected):
                    self.repository.save_email_verification(
                        challenge.model_copy(update={"consumed_at": current})
                    )
                    return
            raise EmailVerificationInvalidError(
                "Email 驗證已失效，請重新取得驗證碼。"
            )

    def purge_email(self, email: str | None) -> int:
        if not email:
            return 0
        return self.repository.delete_email_verifications(
            self.email_fingerprint(email)
        )


def create_email_verification_service(
    repository: AccountRepository,
    data_dir: Path = DEFAULT_DATA_DIR,
    environ: Mapping[str, str] | None = None,
    *,
    sender: VerificationEmailSender | None = None,
) -> EmailVerificationService:
    environment = os.environ if environ is None else environ
    runtime = environment.get("EXCHANGE_ENVIRONMENT", "development").strip().casefold()
    secret_value = environment.get("EXCHANGE_EMAIL_VERIFICATION_SECRET", "").strip()
    if secret_value:
        secret = _decode_secret(secret_value)
    elif runtime in {"production", "prod"}:
        raise EmailVerificationConfigurationError(
            "正式環境必須設定 EXCHANGE_EMAIL_VERIFICATION_SECRET。"
        )
    else:
        secret = _local_development_secret(Path(data_dir))

    if sender is None:
        backend = environment.get(
            "EXCHANGE_EMAIL_VERIFICATION_BACKEND",
            "disabled" if runtime in {"production", "prod"} else "development",
        ).strip().casefold()
        if backend == "development":
            if runtime in {"production", "prod"}:
                raise EmailVerificationConfigurationError(
                    "正式環境不可使用 development Email 驗證 backend。"
                )
            sender = DevelopmentVerificationEmailSender()
        elif backend == "smtp":
            try:
                port = int(environment.get("EXCHANGE_SMTP_PORT", "587"))
            except ValueError as error:
                raise EmailVerificationConfigurationError(
                    "EXCHANGE_SMTP_PORT 必須是整數。"
                ) from error
            sender = SmtpVerificationEmailSender(
                host=environment.get("EXCHANGE_SMTP_HOST", ""),
                port=port,
                sender=(
                    environment.get("EXCHANGE_EMAIL_FROM")
                    or environment.get("EXCHANGE_SMTP_FROM", "")
                ),
                username=environment.get("EXCHANGE_SMTP_USERNAME") or None,
                password=environment.get("EXCHANGE_SMTP_PASSWORD") or None,
                tls_mode=(
                    environment.get("EXCHANGE_SMTP_TLS")
                    or (
                        "starttls"
                        if environment.get("EXCHANGE_SMTP_STARTTLS", "1")
                        .strip()
                        .casefold()
                        not in {"0", "false", "no", "off"}
                        else "none"
                    )
                ).strip().casefold(),
            )
        elif backend == "disabled":
            sender = DisabledVerificationEmailSender()
        else:
            raise EmailVerificationConfigurationError(
                "EXCHANGE_EMAIL_VERIFICATION_BACKEND 必須是 development、smtp 或 disabled。"
            )
    return EmailVerificationService(repository, secret, sender)
