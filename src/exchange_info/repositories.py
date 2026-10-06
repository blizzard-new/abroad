from __future__ import annotations

import hashlib
import json
import os
import secrets
from collections.abc import Mapping
from contextlib import ExitStack, contextmanager
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Generator, Protocol

import requests
from pydantic import BaseModel, Field, TypeAdapter, field_validator, model_validator

from .supabase_keys import supabase_key_headers
from .models import (
    AccountApplicationWorkspace,
    AccountProviderLink,
    AccountNotification,
    AccountSessionRecord,
    AccountSubmissionProgress,
    ApplicationCenterContext,
    AuthProvider,
    CommunityModerationAudit,
    EmailVerificationChallenge,
    NotificationDelivery,
    StudentVerificationMethod,
    UserAccount,
    utc_now,
)
from .storage import (
    data_paths,
    load_account_notifications,
    load_account_sessions,
    load_community_moderation_audits,
    load_email_verifications,
    load_notification_deliveries,
    load_user_accounts,
    save_account_notifications,
    save_account_sessions,
    save_community_moderation_audits,
    save_email_verifications,
    save_notification_deliveries,
    save_user_accounts,
    storage_path_lock,
)


class AccountRepositoryError(RuntimeError):
    """Raised when the configured account repository cannot complete an operation."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class AccountNotFoundError(AccountRepositoryError):
    """Raised when an update-only account mutation no longer has a target row."""


class AccountConflictError(AccountRepositoryError):
    """Raised when an insert or conditional account mutation conflicts."""


ACCOUNT_PROFILE_PATCH_FIELDS = frozenset(
    {
        "display_name",
        "avatar_url",
        "home_university",
        "home_university_changed_at",
        "target_countries",
        "application_stage",
        "followed_boards",
        "notification_preferences",
        "content_updates_seen_at",
        "email_verified",
        "calendar_feed_token",
        "calendar_events",
        "calendar_last_synced_at",
        "product_tier",
    }
)
_JSON_OBJECT_ADAPTER = TypeAdapter(dict[str, Any])


def _json_object(payload: Mapping[str, object]) -> dict[str, Any]:
    return _JSON_OBJECT_ADAPTER.dump_python(dict(payload), mode="json")


def workspace_identity_key(home_school: str) -> str:
    return " ".join(home_school.strip().casefold().split())


def _validate_account_patch_fields(
    updates: Mapping[str, object],
    expected: Mapping[str, object] | None,
) -> None:
    invalid_updates = set(updates) - ACCOUNT_PROFILE_PATCH_FIELDS
    invalid_expected = set(expected or {}) - ACCOUNT_PROFILE_PATCH_FIELDS
    if invalid_updates or invalid_expected:
        invalid = sorted(invalid_updates | invalid_expected)
        raise ValueError(f"不允許修改或比對帳號欄位：{', '.join(invalid)}")
    if not updates:
        raise ValueError("帳號欄位更新不可為空。")


class OAuthLoginMutationStatus(str, Enum):
    COMMITTED = "committed"
    UNVERIFIED_EMAIL_CONFLICT = "unverified_email_conflict"
    VERIFIED_EMAIL_CONFLICT = "verified_email_conflict"
    SAME_PROVIDER_CONFLICT = "same_provider_conflict"
    INTEGRITY_CONFLICT = "integrity_conflict"


class StudentVerificationMutationStatus(str, Enum):
    COMMITTED = "committed"
    ACCOUNT_MISSING = "account_missing"
    SESSION_INVALID = "session_invalid"
    ALREADY_VERIFIED = "already_verified"
    INTEGRITY_CONFLICT = "integrity_conflict"


class OAuthLoginMutationRequest(BaseModel):
    provider: AuthProvider
    subject: str = Field(min_length=1, max_length=512)
    trusted_email: str | None = Field(default=None, max_length=254)
    display_name: str = Field(min_length=1, max_length=200)
    avatar_url: str | None = None
    home_university: str
    new_account_id: str = Field(min_length=1, max_length=128)
    session_id: str = Field(min_length=1, max_length=128)
    session_token_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    session_expires_at: datetime
    occurred_at: datetime

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("OAuth subject 不可為空白。")
        return value

    @field_validator("session_expires_at", "occurred_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("OAuth mutation 時間必須包含時區。")
        return value

    @model_validator(mode="after")
    def validate_provider_contract(self) -> OAuthLoginMutationRequest:
        if self.provider not in {AuthProvider.GOOGLE, AuthProvider.FACEBOOK}:
            raise ValueError("目前只有 Google 與 Facebook 可使用 OAuth login mutation。")
        if self.provider == AuthProvider.FACEBOOK and self.trusted_email is not None:
            raise ValueError("Facebook Email 不可視為已驗證 Email。")
        if self.session_expires_at <= self.occurred_at:
            raise ValueError("OAuth session 必須晚於 mutation 發生時間到期。")
        return self


class OAuthLoginMutationResult(BaseModel):
    status: OAuthLoginMutationStatus
    account: UserAccount | None = None
    session: AccountSessionRecord | None = None


class StudentVerificationMutationRequest(BaseModel):
    account_id: str = Field(min_length=1, max_length=128)
    session_id: str = Field(min_length=1, max_length=128)
    session_token_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    school_name: str = Field(min_length=1, max_length=200)
    department_name: str | None = Field(default=None, max_length=200)
    verification_method: StudentVerificationMethod
    school_email_verified: bool = False
    verified_at: datetime

    @field_validator("verified_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("學生身分 mutation 時間必須包含時區。")
        return value


class StudentVerificationMutationResult(BaseModel):
    status: StudentVerificationMutationStatus
    account: UserAccount | None = None


class AccountDeletionMutationStatus(str, Enum):
    COMMITTED = "committed"
    INVALID_REQUEST = "invalid_request"
    SESSION_INVALID = "session_invalid"
    ACCOUNT_MISSING = "account_missing"
    RECEIPT_MISSING = "receipt_missing"
    IDEMPOTENCY_CONFLICT = "idempotency_conflict"
    INTEGRITY_CONFLICT = "integrity_conflict"


class AccountDeletionMutationRequest(BaseModel):
    mutation_id: str = Field(min_length=16, max_length=128)
    session_token_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    account_id: str | None = Field(default=None, min_length=1, max_length=128)
    session_id: str | None = Field(default=None, min_length=1, max_length=128)
    email_fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    pending_report_retention_days: int = Field(default=90, ge=1, le=365)
    replacement_name: str = Field(default="已刪除帳號", min_length=2, max_length=30)

    @field_validator("replacement_name")
    @classmethod
    def normalize_replacement_name(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def validate_initial_or_replay_shape(self) -> AccountDeletionMutationRequest:
        initial_fields = (self.account_id, self.session_id)
        if any(value is not None for value in initial_fields) and not all(
            value is not None for value in initial_fields
        ):
            raise ValueError("帳號刪除的 account 與 session 必須同時提供。")
        if self.email_fingerprint is not None and self.account_id is None:
            raise ValueError("只有首次帳號刪除可提供 Email fingerprint。")
        return self


class AccountDeletionMutationResult(BaseModel):
    status: AccountDeletionMutationStatus
    storage_object_keys: list[str] = Field(default_factory=list)
    counts: dict[str, int] = Field(default_factory=dict)
    idempotent: bool = False


class AccountDeletionStorageJob(BaseModel):
    mutation_id: str = Field(min_length=16, max_length=128)
    storage_object_keys: list[str] = Field(default_factory=list)


def account_deletion_mutation_fingerprint(
    request: AccountDeletionMutationRequest,
) -> str:
    canonical = json.dumps(
        {
            "operation": "account_deletion",
            "payload": {
                "mutation_id": request.mutation_id,
                "pending_report_retention_days": (
                    request.pending_report_retention_days
                ),
                "replacement_name": request.replacement_name,
                "session_token_hash": request.session_token_hash,
            },
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


class WorkspaceMutationKind(str, Enum):
    WORKSPACE_REPLACE = "workspace_replace"
    SUBMISSION_PROGRESS_TRANSITION = "submission_progress_transition"


class WorkspaceMutationStatus(str, Enum):
    COMMITTED = "committed"
    ACCOUNT_MISSING = "account_missing"
    CONFLICT = "conflict"
    INVALID_REQUEST = "invalid_request"
    INTEGRITY_CONFLICT = "integrity_conflict"


class WorkspaceMutationRequest(BaseModel):
    account_id: str = Field(min_length=1, max_length=128)
    expected_revision: int = Field(ge=0)
    workspace: AccountApplicationWorkspace
    mutation_kind: WorkspaceMutationKind
    progress_key: str | None = Field(default=None, min_length=1, max_length=240)
    progress: AccountSubmissionProgress | None = None

    @model_validator(mode="after")
    def validate_mutation(self) -> WorkspaceMutationRequest:
        if self.expected_revision != self.workspace.revision:
            raise ValueError("Workspace expected revision 必須等於候選版本。")
        if not workspace_identity_key(self.workspace.home_school):
            raise ValueError("Workspace 母校不可為空白。")
        if self.mutation_kind == WorkspaceMutationKind.WORKSPACE_REPLACE:
            if self.progress_key is not None or self.progress is not None:
                raise ValueError("一般 workspace 替換不可夾帶送件進度 mutation。")
            return self
        if self.progress_key is None or self.progress is None:
            raise ValueError("送件進度 mutation 必須包含 progress key 與內容。")
        if not self.progress_key.strip():
            raise ValueError("送件進度 key 不可為空白。")
        self.progress_key = self.progress_key.strip()
        return self


class WorkspaceMutationResult(BaseModel):
    status: WorkspaceMutationStatus
    workspace: AccountApplicationWorkspace | None = None


class CommunitySuspensionMutationStatus(str, Enum):
    COMMITTED = "committed"
    ACCOUNT_MISSING = "account_missing"
    MODERATOR_MISSING = "moderator_missing"
    CONFLICT = "conflict"
    INVALID_DEADLINE = "invalid_deadline"
    NO_CHANGE = "no_change"
    IDEMPOTENCY_CONFLICT = "idempotency_conflict"
    INTEGRITY_CONFLICT = "integrity_conflict"


class CommunitySuspensionMutationRequest(BaseModel):
    event_id: str = Field(min_length=16, max_length=128)
    identity_id: str = Field(min_length=1, max_length=128)
    account_id: str = Field(min_length=1, max_length=128)
    moderator_id: str = Field(min_length=1, max_length=128)
    expected_suspended_until: datetime | None = None
    suspended_until: datetime
    reason: str = Field(min_length=2, max_length=500)

    @field_validator("expected_suspended_until", "suspended_until")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("停權 mutation 時間必須包含時區。")
        return value

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: str) -> str:
        reason = value.strip()
        if len(reason) < 2:
            raise ValueError("停權原因至少需要 2 個字。")
        return reason


class CommunitySuspensionMutationResult(BaseModel):
    status: CommunitySuspensionMutationStatus
    account: UserAccount | None = None
    audit: CommunityModerationAudit | None = None


class AccountRepository(Protocol):
    backend_name: str

    def list_accounts(self) -> list[UserAccount]: ...

    def find_account_by_id(self, account_id: str) -> UserAccount | None: ...

    def find_account_by_email(self, email: str) -> UserAccount | None: ...

    def create_account(self, account: UserAccount) -> UserAccount: ...

    def update_account(self, account: UserAccount) -> UserAccount: ...

    def patch_account_fields(
        self,
        account_id: str,
        updates: Mapping[str, object],
        *,
        expected: Mapping[str, object] | None = None,
    ) -> UserAccount: ...

    def save_account(self, account: UserAccount) -> UserAccount: ...

    def commit_oauth_login(
        self, request: OAuthLoginMutationRequest
    ) -> OAuthLoginMutationResult: ...

    def commit_student_verification(
        self, request: StudentVerificationMutationRequest
    ) -> StudentVerificationMutationResult: ...

    def commit_workspace(
        self, request: WorkspaceMutationRequest
    ) -> WorkspaceMutationResult: ...

    def commit_community_suspension(
        self, request: CommunitySuspensionMutationRequest
    ) -> CommunitySuspensionMutationResult: ...

    def list_community_suspension_audits(
        self,
    ) -> list[CommunityModerationAudit]: ...

    def commit_account_deletion(
        self, request: AccountDeletionMutationRequest
    ) -> AccountDeletionMutationResult: ...

    def complete_account_deletion_storage(
        self, mutation_id: str, session_token_hash: str
    ) -> AccountDeletionMutationStatus: ...

    def list_pending_account_deletion_storage(
        self, limit: int = 100
    ) -> list[AccountDeletionStorageJob]: ...

    def complete_pending_account_deletion_storage(
        self, mutation_id: str
    ) -> AccountDeletionMutationStatus: ...

    def purge_account_deletion_receipts(self) -> int: ...

    def delete_account(self, account_id: str) -> None: ...

    def find_session_by_token_hash(self, token_hash: str) -> AccountSessionRecord | None: ...

    def save_session(self, session: AccountSessionRecord) -> AccountSessionRecord: ...

    def delete_session_by_token_hash(self, token_hash: str) -> None: ...

    def purge_expired_sessions(self, now: datetime | None = None) -> int: ...

    def list_email_verifications(
        self, email_fingerprint: str | None = None
    ) -> list[EmailVerificationChallenge]: ...

    def save_email_verification(
        self, challenge: EmailVerificationChallenge
    ) -> EmailVerificationChallenge: ...

    def delete_email_verifications(self, email_fingerprint: str) -> int: ...

    def purge_expired_email_verifications(
        self, now: datetime | None = None
    ) -> int: ...

    def list_notifications(self, account_id: str, limit: int = 100) -> list[AccountNotification]: ...

    def find_notification_by_dedupe(
        self, account_id: str, dedupe_key: str
    ) -> AccountNotification | None: ...

    def find_notification_by_id(
        self, account_id: str, notification_id: str
    ) -> AccountNotification | None: ...

    def save_notification(self, notification: AccountNotification) -> AccountNotification: ...

    def mark_notification_read(
        self, account_id: str, notification_id: str, read_at: datetime
    ) -> AccountNotification | None: ...

    def mark_all_notifications_read(self, account_id: str, read_at: datetime) -> int: ...

    def find_delivery(
        self, notification_id: str, channel: str
    ) -> NotificationDelivery | None: ...

    def list_due_deliveries(self, now: datetime, limit: int = 100) -> list[NotificationDelivery]: ...

    def save_delivery(self, delivery: NotificationDelivery) -> NotificationDelivery: ...


class JsonlAccountRepository:
    """Local/test fallback that preserves the prototype's JSONL data format."""

    backend_name = "jsonl"

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = Path(data_dir)

    @contextmanager
    def _locked(self, *path_keys: str) -> Generator[None, None, None]:
        paths = data_paths(self.data_dir)
        selected = sorted(
            {paths[path_key] for path_key in path_keys},
            key=lambda path: str(path.resolve(strict=False)).casefold(),
        )
        with ExitStack() as stack:
            for path in selected:
                stack.enter_context(storage_path_lock(path))
            yield

    def list_accounts(self) -> list[UserAccount]:
        return load_user_accounts(self.data_dir)

    def find_account_by_id(self, account_id: str) -> UserAccount | None:
        return next((row for row in self.list_accounts() if row.id == account_id), None)

    def find_account_by_email(self, email: str) -> UserAccount | None:
        normalized = email.strip().casefold()
        return next(
            (
                row
                for row in self.list_accounts()
                if row.email and row.email.casefold() == normalized
            ),
            None,
        )

    @staticmethod
    def _preserve_committed_auth_fields(
        existing: UserAccount,
        incoming: UserAccount,
    ) -> UserAccount:
        existing_links = {link.provider: link for link in existing.provider_links}
        merged_links = list(existing.provider_links)
        for link in incoming.provider_links:
            if link.provider not in existing_links:
                existing_links[link.provider] = link
                merged_links.append(link)
        updates: dict[str, Any] = {"provider_links": merged_links}
        if existing.email_verified:
            updates["email_verified"] = True
            if existing.email:
                updates["email"] = existing.email
        if existing.school_email_verified:
            updates["school_email_verified"] = True
        if existing.student_status_verified:
            updates.update(
                {
                    "home_university": existing.home_university,
                    "student_status_verified": True,
                    "verified_university": existing.verified_university,
                    "verified_department": existing.verified_department,
                    "student_verification_method": (
                        existing.student_verification_method
                    ),
                    "student_verified_at": existing.student_verified_at,
                }
            )
        return incoming.model_copy(update=updates)

    def create_account(self, account: UserAccount) -> UserAccount:
        with self._locked("user_accounts"):
            current_rows = self.list_accounts()
            normalized_email = account.email.casefold() if account.email else None
            if any(
                row.id == account.id
                or (
                    normalized_email is not None
                    and row.email is not None
                    and row.email.casefold() == normalized_email
                )
                for row in current_rows
            ):
                raise AccountConflictError("帳號 ID 或 Email 已經存在。")
            save_user_accounts([*current_rows, account], self.data_dir)
        return account

    def update_account(self, account: UserAccount) -> UserAccount:
        with self._locked("user_accounts"):
            current_rows = self.list_accounts()
            existing = next(
                (row for row in current_rows if row.id == account.id),
                None,
            )
            if existing is None:
                raise AccountNotFoundError("帳號已不存在，不能以更新操作重新建立。")
            persisted = self._preserve_committed_auth_fields(existing, account)
            save_user_accounts(
                [
                    persisted if row.id == account.id else row
                    for row in current_rows
                ],
                self.data_dir,
            )
        return persisted

    def patch_account_fields(
        self,
        account_id: str,
        updates: Mapping[str, object],
        *,
        expected: Mapping[str, object] | None = None,
    ) -> UserAccount:
        _validate_account_patch_fields(updates, expected)
        serialized_updates = _json_object(updates)
        serialized_expected = _json_object(expected or {})
        with self._locked("user_accounts"):
            current_rows = self.list_accounts()
            existing = next((row for row in current_rows if row.id == account_id), None)
            if existing is None:
                raise AccountNotFoundError("帳號已不存在，不能以更新操作重新建立。")
            current_payload = existing.model_dump(mode="json")
            if any(
                current_payload.get(field_name) != expected_value
                for field_name, expected_value in serialized_expected.items()
            ):
                raise AccountConflictError(
                    "帳號欄位已由另一個請求更新，請取得最新狀態後重試。",
                    status_code=409,
                )
            persisted = self._preserve_committed_auth_fields(
                existing,
                UserAccount.model_validate(
                    {
                        **existing.model_dump(mode="json"),
                        **serialized_updates,
                        "updated_at": utc_now(),
                    }
                ),
            )
            save_user_accounts(
                [
                    persisted if row.id == account_id else row
                    for row in current_rows
                ],
                self.data_dir,
            )
        return persisted

    @staticmethod
    def _empty_workspace(home_school: str) -> AccountApplicationWorkspace:
        return AccountApplicationWorkspace(
            home_school=home_school,
            application_context=ApplicationCenterContext(school_name=home_school),
        )

    def commit_workspace(
        self,
        request: WorkspaceMutationRequest,
    ) -> WorkspaceMutationResult:
        workspace_key = workspace_identity_key(request.workspace.home_school)
        with self._locked("user_accounts"):
            account_rows = load_user_accounts(self.data_dir)
            account = next(
                (row for row in account_rows if row.id == request.account_id),
                None,
            )
            if account is None:
                return WorkspaceMutationResult(
                    status=WorkspaceMutationStatus.ACCOUNT_MISSING
                )
            existing = next(
                (
                    row
                    for row in account.application_workspaces
                    if workspace_identity_key(row.home_school) == workspace_key
                ),
                None,
            )
            current_revision = existing.revision if existing is not None else 0
            if request.expected_revision != current_revision:
                return WorkspaceMutationResult(
                    status=WorkspaceMutationStatus.CONFLICT,
                    workspace=existing
                    or self._empty_workspace(request.workspace.home_school),
                )

            committed_at = utc_now()
            if request.mutation_kind == WorkspaceMutationKind.WORKSPACE_REPLACE:
                committed_workspace = request.workspace.model_copy(
                    update={
                        "revision": current_revision + 1,
                        "submission_progress": (
                            existing.submission_progress if existing is not None else {}
                        ),
                        "updated_at": committed_at,
                    }
                )
            else:
                if request.progress_key is None or request.progress is None:
                    return WorkspaceMutationResult(
                        status=WorkspaceMutationStatus.INVALID_REQUEST
                    )
                base_workspace = existing or self._empty_workspace(
                    request.workspace.home_school
                )
                committed_workspace = base_workspace.model_copy(
                    update={
                        "revision": current_revision + 1,
                        "submission_progress": {
                            **base_workspace.submission_progress,
                            request.progress_key: request.progress,
                        },
                        "updated_at": committed_at,
                    }
                )

            other_workspaces = [
                row
                for row in account.application_workspaces
                if workspace_identity_key(row.home_school) != workspace_key
            ]
            all_workspaces = [*other_workspaces, committed_workspace]
            account_updates: dict[str, Any] = {
                "application_workspaces": all_workspaces,
                "updated_at": committed_at,
            }
            if request.mutation_kind == WorkspaceMutationKind.WORKSPACE_REPLACE:
                calendar_events = {
                    event.id: event
                    for row in all_workspaces
                    for event in row.deadline_events
                }
                account_updates.update(
                    {
                        "calendar_events": list(calendar_events.values()),
                        "calendar_last_synced_at": committed_at,
                    }
                )
            persisted = account.model_copy(update=account_updates)
            save_user_accounts(
                [
                    persisted if row.id == request.account_id else row
                    for row in account_rows
                ],
                self.data_dir,
            )
        return WorkspaceMutationResult(
            status=WorkspaceMutationStatus.COMMITTED,
            workspace=committed_workspace,
        )

    def commit_community_suspension(
        self,
        request: CommunitySuspensionMutationRequest,
    ) -> CommunitySuspensionMutationResult:
        with self._locked("community_moderation_audits", "user_accounts"):
            account_rows = load_user_accounts(self.data_dir)
            audit_rows = load_community_moderation_audits(self.data_dir)
            target = next(
                (row for row in account_rows if row.id == request.account_id),
                None,
            )
            existing_event = next(
                (row for row in audit_rows if row.id == request.event_id),
                None,
            )
            if existing_event is not None:
                same_event = (
                    existing_event.resource_type == "identity"
                    and existing_event.resource_id == request.identity_id
                    and existing_event.moderator_id == request.moderator_id
                    and existing_event.note == request.reason.strip()
                    and existing_event.previous_suspended_until
                    == request.expected_suspended_until
                    and existing_event.new_suspended_until == request.suspended_until
                )
                return CommunitySuspensionMutationResult(
                    status=(
                        CommunitySuspensionMutationStatus.COMMITTED
                        if same_event
                        else CommunitySuspensionMutationStatus.IDEMPOTENCY_CONFLICT
                    ),
                    account=target if same_event else None,
                    audit=existing_event if same_event else None,
                )
            if target is None:
                return CommunitySuspensionMutationResult(
                    status=CommunitySuspensionMutationStatus.ACCOUNT_MISSING
                )
            if not any(row.id == request.moderator_id for row in account_rows):
                return CommunitySuspensionMutationResult(
                    status=CommunitySuspensionMutationStatus.MODERATOR_MISSING
                )

            committed_at = utc_now()
            if request.suspended_until <= committed_at:
                return CommunitySuspensionMutationResult(
                    status=CommunitySuspensionMutationStatus.INVALID_DEADLINE
                )
            if target.community_suspended_until != request.expected_suspended_until:
                return CommunitySuspensionMutationResult(
                    status=CommunitySuspensionMutationStatus.CONFLICT,
                    account=target,
                )
            if target.community_suspended_until == request.suspended_until:
                return CommunitySuspensionMutationResult(
                    status=CommunitySuspensionMutationStatus.NO_CHANGE,
                    account=target,
                )

            previous_status = (
                "suspended"
                if target.community_suspended_until is not None
                and target.community_suspended_until > committed_at
                else "active"
            )
            audit = CommunityModerationAudit(
                id=request.event_id,
                resource_type="identity",
                resource_id=request.identity_id,
                previous_status=previous_status,
                new_status="suspended",
                moderator_id=request.moderator_id,
                note=request.reason.strip(),
                previous_suspended_until=target.community_suspended_until,
                new_suspended_until=request.suspended_until,
                retained_until=committed_at + timedelta(days=90),
                created_at=committed_at,
            )
            persisted = target.model_copy(
                update={
                    "community_suspended_until": request.suspended_until,
                    "updated_at": committed_at,
                }
            )
            try:
                save_community_moderation_audits([*audit_rows, audit], self.data_dir)
                save_user_accounts(
                    [
                        persisted if row.id == request.account_id else row
                        for row in account_rows
                    ],
                    self.data_dir,
                )
            except Exception as error:
                try:
                    save_community_moderation_audits(audit_rows, self.data_dir)
                except Exception as rollback_error:
                    raise AccountRepositoryError(
                        "本機停權稽核回滾失敗；已停止後續操作。"
                    ) from rollback_error
                raise AccountRepositoryError(
                    "本機停權與稽核事件未能一起保存。"
                ) from error
        return CommunitySuspensionMutationResult(
            status=CommunitySuspensionMutationStatus.COMMITTED,
            account=persisted,
            audit=audit,
        )

    def list_community_suspension_audits(
        self,
    ) -> list[CommunityModerationAudit]:
        with self._locked("community_moderation_audits"):
            rows = load_community_moderation_audits(self.data_dir)
            current = utc_now()
            retained = [
                row
                for row in rows
                if not (
                    row.resource_type == "identity"
                    and row.retained_until is not None
                    and row.retained_until <= current
                )
            ]
            if len(retained) != len(rows):
                try:
                    save_community_moderation_audits(retained, self.data_dir)
                except Exception as error:
                    raise AccountRepositoryError(
                        "本機過期停權稽核清理失敗。"
                    ) from error
        return [row for row in retained if row.resource_type == "identity"]

    def save_account(self, account: UserAccount) -> UserAccount:
        """Compatibility upsert for fixtures and offline bootstrap code.

        Runtime API mutations use create_account/update_account so a stale update
        cannot recreate a deleted account.
        """
        with self._locked("user_accounts"):
            current_rows = self.list_accounts()
            existing = next(
                (row for row in current_rows if row.id == account.id),
                None,
            )
            persisted = (
                self._preserve_committed_auth_fields(existing, account)
                if existing is not None
                else account
            )
            rows = [row for row in current_rows if row.id != account.id]
            save_user_accounts([*rows, persisted], self.data_dir)
        return persisted

    def commit_oauth_login(
        self, request: OAuthLoginMutationRequest
    ) -> OAuthLoginMutationResult:
        trusted_email = (
            request.trusted_email.strip().casefold()
            if request.trusted_email and request.trusted_email.strip()
            else None
        )
        with self._locked("user_accounts", "account_sessions"):
            account_rows = load_user_accounts(self.data_dir)
            session_rows = load_account_sessions(self.data_dir)
            provider_matches = [
                account
                for account in account_rows
                if any(
                    link.provider == request.provider
                    and link.subject == request.subject
                    for link in account.provider_links
                )
            ]
            email_matches = [
                account
                for account in account_rows
                if trusted_email
                and account.email
                and account.email.casefold() == trusted_email
            ]
            if len(provider_matches) > 1 or len(email_matches) > 1:
                return OAuthLoginMutationResult(
                    status=OAuthLoginMutationStatus.INTEGRITY_CONFLICT
                )
            provider_account = provider_matches[0] if provider_matches else None
            email_account = email_matches[0] if email_matches else None
            if (
                email_account is not None
                and not email_account.email_verified
                and (
                    provider_account is None
                    or provider_account.id != email_account.id
                )
            ):
                return OAuthLoginMutationResult(
                    status=OAuthLoginMutationStatus.UNVERIFIED_EMAIL_CONFLICT
                )
            if (
                provider_account is not None
                and email_account is not None
                and provider_account.id != email_account.id
            ):
                return OAuthLoginMutationResult(
                    status=OAuthLoginMutationStatus.VERIFIED_EMAIL_CONFLICT
                )
            if (
                provider_account is not None
                and trusted_email is not None
                and provider_account.email is not None
                and provider_account.email.casefold() != trusted_email
            ):
                return OAuthLoginMutationResult(
                    status=OAuthLoginMutationStatus.VERIFIED_EMAIL_CONFLICT
                )
            if provider_account is None and email_account is not None and any(
                link.provider == request.provider
                for link in email_account.provider_links
            ):
                return OAuthLoginMutationResult(
                    status=OAuthLoginMutationStatus.SAME_PROVIDER_CONFLICT
                )

            committed_at = utc_now()
            if request.session_expires_at <= committed_at:
                return OAuthLoginMutationResult(
                    status=OAuthLoginMutationStatus.INTEGRITY_CONFLICT
                )
            account = provider_account or email_account
            if account is None:
                if any(row.id == request.new_account_id for row in account_rows):
                    return OAuthLoginMutationResult(
                        status=OAuthLoginMutationStatus.INTEGRITY_CONFLICT
                    )
                account = UserAccount(
                    id=request.new_account_id,
                    email=trusted_email,
                    display_name=(request.display_name or "留學同學")[:30],
                    avatar_url=request.avatar_url,
                    email_verified=bool(trusted_email),
                    home_university=request.home_university,
                    provider_links=[
                        AccountProviderLink(
                            provider=request.provider,
                            subject=request.subject,
                        )
                    ],
                    created_at=committed_at,
                    updated_at=committed_at,
                )
            else:
                links = list(account.provider_links)
                if not any(
                    link.provider == request.provider
                    and link.subject == request.subject
                    for link in links
                ):
                    links.append(
                        AccountProviderLink(
                            provider=request.provider,
                            subject=request.subject,
                        )
                    )
                account = account.model_copy(
                    update={
                        "email": account.email or trusted_email,
                        "email_verified": account.email_verified
                        or bool(trusted_email),
                        "avatar_url": account.avatar_url or request.avatar_url,
                        "provider_links": links,
                        "updated_at": committed_at,
                    }
                )

            if any(
                row.id == request.session_id
                or secrets.compare_digest(
                    row.token_hash,
                    request.session_token_hash,
                )
                for row in session_rows
            ):
                return OAuthLoginMutationResult(
                    status=OAuthLoginMutationStatus.INTEGRITY_CONFLICT
                )
            session = AccountSessionRecord(
                id=request.session_id,
                account_id=account.id,
                token_hash=request.session_token_hash,
                expires_at=request.session_expires_at,
                created_at=committed_at,
            )
            next_accounts = [
                row for row in account_rows if row.id != account.id
            ] + [account]
            next_sessions = [*session_rows, session]
            if request.session_expires_at <= utc_now():
                return OAuthLoginMutationResult(
                    status=OAuthLoginMutationStatus.INTEGRITY_CONFLICT
                )
            try:
                save_user_accounts(next_accounts, self.data_dir)
                save_account_sessions(next_sessions, self.data_dir)
            except Exception:
                # The local fallback spans two JSONL files. Restore both snapshots
                # before surfacing an error so callers observe the same all-or-none
                # contract as the production transaction.
                save_user_accounts(account_rows, self.data_dir)
                save_account_sessions(session_rows, self.data_dir)
                raise
            return OAuthLoginMutationResult(
                status=OAuthLoginMutationStatus.COMMITTED,
                account=account,
                session=session,
            )

    def commit_student_verification(
        self, request: StudentVerificationMutationRequest
    ) -> StudentVerificationMutationResult:
        with self._locked("user_accounts", "account_sessions"):
            account_rows = load_user_accounts(self.data_dir)
            session_rows = load_account_sessions(self.data_dir)
            account = next(
                (row for row in account_rows if row.id == request.account_id),
                None,
            )
            if account is None:
                return StudentVerificationMutationResult(
                    status=StudentVerificationMutationStatus.ACCOUNT_MISSING
                )
            session = next(
                (
                    row
                    for row in session_rows
                    if row.id == request.session_id
                    and row.account_id == request.account_id
                    and secrets.compare_digest(
                        row.token_hash,
                        request.session_token_hash,
                    )
                ),
                None,
            )
            committed_at = utc_now()
            if session is None or session.expires_at <= committed_at:
                return StudentVerificationMutationResult(
                    status=StudentVerificationMutationStatus.SESSION_INVALID
                )
            if account.student_status_verified:
                return StudentVerificationMutationResult(
                    status=StudentVerificationMutationStatus.ALREADY_VERIFIED,
                    account=account,
                )
            updated = account.model_copy(
                update={
                    "home_university": request.school_name,
                    "school_email_verified": account.school_email_verified
                    or request.school_email_verified,
                    "student_status_verified": True,
                    "verified_university": request.school_name,
                    "verified_department": request.department_name,
                    "student_verification_method": request.verification_method,
                    "student_verified_at": committed_at,
                    "updated_at": committed_at,
                }
            )
            save_user_accounts(
                [
                    updated if row.id == request.account_id else row
                    for row in account_rows
                ],
                self.data_dir,
            )
            return StudentVerificationMutationResult(
                status=StudentVerificationMutationStatus.COMMITTED,
                account=updated,
            )

    def delete_account(self, account_id: str) -> None:
        with self._locked(
            "user_accounts",
            "account_sessions",
            "account_notifications",
            "notification_deliveries",
        ):
            save_user_accounts(
                [row for row in self.list_accounts() if row.id != account_id],
                self.data_dir,
            )
            save_account_sessions(
                [
                    row
                    for row in load_account_sessions(self.data_dir)
                    if row.account_id != account_id
                ],
                self.data_dir,
            )
            notification_ids = {
                row.id
                for row in load_account_notifications(self.data_dir)
                if row.account_id == account_id
            }
            save_account_notifications(
                [
                    row
                    for row in load_account_notifications(self.data_dir)
                    if row.account_id != account_id
                ],
                self.data_dir,
            )
            save_notification_deliveries(
                [
                    row
                    for row in load_notification_deliveries(self.data_dir)
                    if row.account_id != account_id
                    and row.notification_id not in notification_ids
                ],
                self.data_dir,
            )

    def commit_account_deletion(
        self, request: AccountDeletionMutationRequest
    ) -> AccountDeletionMutationResult:
        if request.account_id is None or request.session_id is None:
            return AccountDeletionMutationResult(
                status=AccountDeletionMutationStatus.SESSION_INVALID
            )
        session = self.find_session_by_token_hash(request.session_token_hash)
        if (
            session is None
            or session.id != request.session_id
            or session.account_id != request.account_id
            or session.expires_at <= utc_now()
            or not secrets.compare_digest(
                session.token_hash,
                request.session_token_hash,
            )
        ):
            return AccountDeletionMutationResult(
                status=AccountDeletionMutationStatus.SESSION_INVALID
            )
        if self.find_account_by_id(request.account_id) is None:
            return AccountDeletionMutationResult(
                status=AccountDeletionMutationStatus.ACCOUNT_MISSING
            )
        self.delete_account(request.account_id)
        return AccountDeletionMutationResult(
            status=AccountDeletionMutationStatus.COMMITTED
        )

    def complete_account_deletion_storage(
        self, mutation_id: str, session_token_hash: str
    ) -> AccountDeletionMutationStatus:
        del mutation_id, session_token_hash
        return AccountDeletionMutationStatus.COMMITTED

    def list_pending_account_deletion_storage(
        self, limit: int = 100
    ) -> list[AccountDeletionStorageJob]:
        del limit
        return []

    def complete_pending_account_deletion_storage(
        self, mutation_id: str
    ) -> AccountDeletionMutationStatus:
        del mutation_id
        return AccountDeletionMutationStatus.COMMITTED

    def purge_account_deletion_receipts(self) -> int:
        return 0

    def find_session_by_token_hash(self, token_hash: str) -> AccountSessionRecord | None:
        return next(
            (
                row
                for row in load_account_sessions(self.data_dir)
                if row.token_hash == token_hash
            ),
            None,
        )

    def save_session(self, session: AccountSessionRecord) -> AccountSessionRecord:
        with self._locked("account_sessions"):
            rows = [
                row
                for row in load_account_sessions(self.data_dir)
                if row.id != session.id and row.token_hash != session.token_hash
            ]
            save_account_sessions([*rows, session], self.data_dir)
        return session

    def delete_session_by_token_hash(self, token_hash: str) -> None:
        with self._locked("account_sessions"):
            save_account_sessions(
                [
                    row
                    for row in load_account_sessions(self.data_dir)
                    if row.token_hash != token_hash
                ],
                self.data_dir,
            )

    def purge_expired_sessions(self, now: datetime | None = None) -> int:
        with self._locked("account_sessions"):
            cutoff = now or utc_now()
            rows = load_account_sessions(self.data_dir)
            active = [row for row in rows if row.expires_at > cutoff]
            if len(active) != len(rows):
                save_account_sessions(active, self.data_dir)
            return len(rows) - len(active)

    def list_email_verifications(
        self, email_fingerprint: str | None = None
    ) -> list[EmailVerificationChallenge]:
        rows = load_email_verifications(self.data_dir)
        if email_fingerprint is not None:
            rows = [
                row for row in rows if row.email_fingerprint == email_fingerprint
            ]
        return sorted(rows, key=lambda row: row.requested_at, reverse=True)

    def save_email_verification(
        self, challenge: EmailVerificationChallenge
    ) -> EmailVerificationChallenge:
        with self._locked("email_verifications"):
            rows = [
                row
                for row in load_email_verifications(self.data_dir)
                if row.id != challenge.id
            ]
            save_email_verifications([*rows, challenge], self.data_dir)
        return challenge

    def delete_email_verifications(self, email_fingerprint: str) -> int:
        with self._locked("email_verifications"):
            rows = load_email_verifications(self.data_dir)
            remaining = [
                row for row in rows if row.email_fingerprint != email_fingerprint
            ]
            if len(remaining) != len(rows):
                save_email_verifications(remaining, self.data_dir)
            return len(rows) - len(remaining)

    def purge_expired_email_verifications(
        self, now: datetime | None = None
    ) -> int:
        with self._locked("email_verifications"):
            cutoff = now or utc_now()
            rows = load_email_verifications(self.data_dir)
            active = [
                row
                for row in rows
                if row.expires_at > cutoff and row.consumed_at is None
            ]
            if len(active) != len(rows):
                save_email_verifications(active, self.data_dir)
            return len(rows) - len(active)

    def list_notifications(
        self, account_id: str, limit: int = 100
    ) -> list[AccountNotification]:
        rows = [
            row
            for row in load_account_notifications(self.data_dir)
            if row.account_id == account_id
        ]
        return sorted(rows, key=lambda row: row.created_at, reverse=True)[:limit]

    def find_notification_by_dedupe(
        self, account_id: str, dedupe_key: str
    ) -> AccountNotification | None:
        return next(
            (
                row
                for row in load_account_notifications(self.data_dir)
                if row.account_id == account_id and row.dedupe_key == dedupe_key
            ),
            None,
        )

    def find_notification_by_id(
        self, account_id: str, notification_id: str
    ) -> AccountNotification | None:
        return next(
            (
                row
                for row in load_account_notifications(self.data_dir)
                if row.account_id == account_id and row.id == notification_id
            ),
            None,
        )

    def save_notification(self, notification: AccountNotification) -> AccountNotification:
        with self._locked("account_notifications"):
            existing = self.find_notification_by_dedupe(
                notification.account_id, notification.dedupe_key
            )
            if existing is not None:
                return existing
            rows = load_account_notifications(self.data_dir)
            save_account_notifications([*rows, notification], self.data_dir)
            return notification

    def mark_notification_read(
        self, account_id: str, notification_id: str, read_at: datetime
    ) -> AccountNotification | None:
        with self._locked("account_notifications"):
            rows = load_account_notifications(self.data_dir)
            matched: AccountNotification | None = None
            updated_rows: list[AccountNotification] = []
            for row in rows:
                if row.id == notification_id and row.account_id == account_id:
                    row = row.model_copy(update={"read_at": read_at})
                    matched = row
                updated_rows.append(row)
            if matched is not None:
                save_account_notifications(updated_rows, self.data_dir)
            return matched

    def mark_all_notifications_read(self, account_id: str, read_at: datetime) -> int:
        with self._locked("account_notifications"):
            rows = load_account_notifications(self.data_dir)
            count = 0
            updated_rows: list[AccountNotification] = []
            for row in rows:
                if row.account_id == account_id and row.read_at is None:
                    row = row.model_copy(update={"read_at": read_at})
                    count += 1
                updated_rows.append(row)
            if count:
                save_account_notifications(updated_rows, self.data_dir)
            return count

    def find_delivery(
        self, notification_id: str, channel: str
    ) -> NotificationDelivery | None:
        return next(
            (
                row
                for row in load_notification_deliveries(self.data_dir)
                if row.notification_id == notification_id and row.channel == channel
            ),
            None,
        )

    def list_due_deliveries(
        self, now: datetime, limit: int = 100
    ) -> list[NotificationDelivery]:
        rows = [
            row
            for row in load_notification_deliveries(self.data_dir)
            if row.status in {"pending", "retrying"} and row.next_attempt_at <= now
        ]
        return sorted(rows, key=lambda row: row.next_attempt_at)[:limit]

    def save_delivery(self, delivery: NotificationDelivery) -> NotificationDelivery:
        with self._locked("notification_deliveries"):
            rows = [
                row
                for row in load_notification_deliveries(self.data_dir)
                if row.id != delivery.id
                and not (
                    row.notification_id == delivery.notification_id
                    and row.channel == delivery.channel
                )
            ]
            save_notification_deliveries([*rows, delivery], self.data_dir)
        return delivery


class _RequestSession(Protocol):
    def request(self, method: str, url: str, **kwargs: Any) -> Any: ...


class SupabaseAccountRepository:
    """Server-only PostgREST repository backed by Supabase.

    The secret key is held only by the FastAPI process. The corresponding tables deny
    `anon` and `authenticated` direct access, so Web and Flutter clients must continue
    to use the product API.
    """

    backend_name = "supabase"
    _accounts_table = "exchange_accounts"
    _workspaces_table = "exchange_account_workspaces"
    _sessions_table = "exchange_account_sessions"
    _email_verifications_table = "exchange_email_verifications"
    _notifications_table = "exchange_notifications"
    _deliveries_table = "exchange_notification_deliveries"

    def __init__(
        self,
        url: str,
        secret_key: str,
        *,
        request_session: _RequestSession | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        normalized_url = url.strip().rstrip("/")
        normalized_key = secret_key.strip()
        if not normalized_url.startswith("https://"):
            raise ValueError("Supabase URL 必須使用 https://。")
        if not normalized_key:
            raise ValueError("Supabase secret key 不可為空。")
        self._rest_url = f"{normalized_url}/rest/v1"
        self._secret_key = normalized_key
        self._session = request_session or requests.Session()
        self._timeout_seconds = timeout_seconds

    @property
    def _headers(self) -> dict[str, str]:
        return {
            **supabase_key_headers(self._secret_key),
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _request(
        self,
        method: str,
        table: str,
        *,
        params: Mapping[str, str] | None = None,
        json_body: object | None = None,
        prefer: str | None = None,
    ) -> list[dict[str, Any]]:
        headers = self._headers
        if prefer:
            headers["Prefer"] = prefer
        try:
            response = self._session.request(
                method,
                f"{self._rest_url}/{table}",
                headers=headers,
                params=dict(params or {}),
                json=json_body,
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
        except requests.RequestException as error:
            status = getattr(getattr(error, "response", None), "status_code", None)
            suffix = f"（HTTP {status}）" if status else ""
            raise AccountRepositoryError(
                f"Supabase 帳號資料存取失敗{suffix}。",
                status_code=status,
            ) from error
        if not getattr(response, "content", b""):
            return []
        payload = response.json()
        if not isinstance(payload, list):
            raise AccountRepositoryError("Supabase 回傳了非預期的帳號資料格式。")
        return payload

    def _rpc(self, function_name: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        try:
            response = self._session.request(
                "POST",
                f"{self._rest_url}/rpc/{function_name}",
                headers=self._headers,
                json=dict(payload),
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
        except requests.RequestException as error:
            status = getattr(getattr(error, "response", None), "status_code", None)
            suffix = f"（HTTP {status}）" if status else ""
            raise AccountRepositoryError(
                f"Supabase 原子帳號操作失敗{suffix}。",
                status_code=status,
            ) from error
        try:
            result = response.json()
        except (TypeError, ValueError) as error:
            raise AccountRepositoryError("Supabase 原子帳號操作回傳無效 JSON。") from error
        if isinstance(result, list) and len(result) == 1:
            result = result[0]
        if not isinstance(result, dict):
            raise AccountRepositoryError("Supabase 回傳了非預期的原子帳號操作格式。")
        return result

    @staticmethod
    def _workspace_key(home_school: str) -> str:
        return workspace_identity_key(home_school)

    def _workspace_rows(self, account_id: str) -> list[dict[str, Any]]:
        return self._request(
            "GET",
            self._workspaces_table,
            params={
                "select": "home_school_key,workspace,revision",
                "account_id": f"eq.{account_id}",
                "order": "updated_at.asc",
            },
        )

    def _hydrate_account(self, row: Mapping[str, Any]) -> UserAccount:
        profile = dict(row.get("profile") or {})
        profile["id"] = row.get("id")
        profile["email"] = row.get("email")
        if row.get("created_at") is not None:
            profile["created_at"] = row["created_at"]
        if row.get("updated_at") is not None:
            profile["updated_at"] = row["updated_at"]
        profile["application_workspaces"] = []
        for workspace_row in self._workspace_rows(str(row["id"])):
            workspace = workspace_row.get("workspace")
            if not isinstance(workspace, dict):
                continue
            revision = workspace_row.get("revision")
            if revision is not None:
                workspace = {**workspace, "revision": revision}
            profile["application_workspaces"].append(workspace)
        if "community_suspended_until" in row:
            profile["community_suspended_until"] = row.get(
                "community_suspended_until"
            )
        return UserAccount.model_validate(profile)

    def list_accounts(self) -> list[UserAccount]:
        rows = self._request(
            "GET",
            self._accounts_table,
            params={
                "select": "id,email,profile,community_suspended_until,created_at,updated_at",
                "order": "created_at.asc",
            },
        )
        return [self._hydrate_account(row) for row in rows]

    def find_account_by_id(self, account_id: str) -> UserAccount | None:
        rows = self._request(
            "GET",
            self._accounts_table,
            params={
                "select": "id,email,profile,community_suspended_until,created_at,updated_at",
                "id": f"eq.{account_id}",
                "limit": "1",
            },
        )
        return self._hydrate_account(rows[0]) if rows else None

    def find_account_by_email(self, email: str) -> UserAccount | None:
        rows = self._request(
            "GET",
            self._accounts_table,
            params={
                "select": "id,email,profile,community_suspended_until,created_at,updated_at",
                "email": f"eq.{email.strip().casefold()}",
                "limit": "1",
            },
        )
        return self._hydrate_account(rows[0]) if rows else None

    @staticmethod
    def _account_write_payload(account: UserAccount) -> dict[str, Any]:
        return {
            "id": account.id,
            "email": account.email.casefold() if account.email else None,
            "profile": account.model_dump(
                mode="json",
                exclude={"application_workspaces", "community_suspended_until"},
            ),
            "created_at": account.created_at.isoformat(),
            "updated_at": account.updated_at.isoformat(),
            "community_suspended_until": (
                account.community_suspended_until.isoformat()
                if account.community_suspended_until is not None
                else None
            ),
        }

    def create_account(self, account: UserAccount) -> UserAccount:
        if account.application_workspaces:
            raise AccountRepositoryError(
                "Supabase 建立帳號時不可夾帶 workspace；請在帳號建立後使用 atomic workspace RPC。"
            )
        if account.community_suspended_until is not None:
            raise AccountRepositoryError(
                "Supabase 建立帳號時不可夾帶停權狀態；請使用專用停權 RPC。"
            )
        try:
            rows = self._request(
                "POST",
                self._accounts_table,
                params={
                    "select": "id,email,profile,community_suspended_until,created_at,updated_at"
                },
                json_body=self._account_write_payload(account),
                prefer="return=representation",
            )
        except AccountRepositoryError as error:
            if error.status_code == 409:
                raise AccountConflictError(
                    "帳號 ID 或 Email 已經存在。",
                    status_code=409,
                ) from error
            raise
        if len(rows) != 1:
            raise AccountRepositoryError("Supabase 未建立預期的帳號資料。")
        persisted = self._account_from_rpc(rows[0])
        if persisted is None:
            raise AccountRepositoryError("Supabase 未回傳已建立的帳號資料。")
        return persisted

    def update_account(self, account: UserAccount) -> UserAccount:
        raise AccountRepositoryError(
            "Supabase 不允許整份帳號 update；請使用欄位級或專用 atomic RPC。"
        )

    def patch_account_fields(
        self,
        account_id: str,
        updates: Mapping[str, object],
        *,
        expected: Mapping[str, object] | None = None,
    ) -> UserAccount:
        _validate_account_patch_fields(updates, expected)
        serialized_updates = _json_object(updates)
        result = self._rpc(
            "exchange_patch_account_profile",
            {
                "p_account_id": account_id,
                "p_updates": serialized_updates,
                "p_expected": _json_object(expected or {}),
            },
        )
        status = str(result.get("status") or "")
        if status == "account_missing":
            raise AccountNotFoundError("帳號已不存在，不能以更新操作重新建立。")
        if status == "conflict":
            raise AccountConflictError(
                "帳號欄位已由另一個請求更新，請取得最新狀態後重試。",
                status_code=409,
            )
        if status != "committed":
            raise AccountRepositoryError("Supabase 回傳未知的帳號欄位更新狀態。")
        payload = result.get("account")
        if not isinstance(payload, Mapping):
            payload = result
        if not isinstance(payload.get("profile"), Mapping):
            raise AccountRepositoryError("Supabase 未回傳已更新的帳號資料。")
        persisted = self._account_from_rpc(payload)
        if persisted is None:
            raise AccountRepositoryError("Supabase 未回傳已更新的帳號資料。")
        workspace_payloads: list[dict[str, Any]] = []
        for row in self._workspace_rows(account_id):
            workspace = row.get("workspace")
            if not isinstance(workspace, dict):
                continue
            revision = row.get("revision")
            workspace_payloads.append(
                {**workspace, **({"revision": revision} if revision is not None else {})}
            )
        persisted = UserAccount.model_validate(
            {
                **persisted.model_dump(mode="json"),
                "application_workspaces": workspace_payloads,
            }
        )
        return persisted

    def commit_workspace(
        self,
        request: WorkspaceMutationRequest,
    ) -> WorkspaceMutationResult:
        result = self._rpc(
            "exchange_commit_account_workspace",
            {
                "p_account_id": request.account_id,
                "p_home_school_key": self._workspace_key(
                    request.workspace.home_school
                ),
                "p_expected_revision": request.expected_revision,
                "p_candidate_workspace": request.workspace.model_dump(mode="json"),
                "p_mutation_kind": request.mutation_kind.value,
                "p_progress_key": request.progress_key,
                "p_progress": (
                    request.progress.model_dump(mode="json")
                    if request.progress is not None
                    else None
                ),
            },
        )
        try:
            status = WorkspaceMutationStatus(str(result.get("status") or ""))
        except ValueError as error:
            raise AccountRepositoryError(
                "Supabase 回傳未知的 workspace mutation 狀態。"
            ) from error
        workspace_payload = result.get("workspace")
        if not isinstance(workspace_payload, Mapping):
            workspace_payload = result.get("current_workspace")
        workspace = None
        if isinstance(workspace_payload, Mapping):
            try:
                workspace = AccountApplicationWorkspace.model_validate(
                    workspace_payload
                )
            except (TypeError, ValueError) as error:
                raise AccountRepositoryError(
                    "Supabase workspace mutation 回傳無效資料。"
                ) from error
        if status in {
            WorkspaceMutationStatus.COMMITTED,
            WorkspaceMutationStatus.CONFLICT,
        } and workspace is None:
            if status == WorkspaceMutationStatus.CONFLICT:
                workspace = JsonlAccountRepository._empty_workspace(
                    request.workspace.home_school
                )
            else:
                raise AccountRepositoryError(
                    "Supabase workspace mutation 未回傳已提交資料。"
                )
        return WorkspaceMutationResult(status=status, workspace=workspace)

    def commit_community_suspension(
        self,
        request: CommunitySuspensionMutationRequest,
    ) -> CommunitySuspensionMutationResult:
        result = self._rpc(
            "exchange_commit_community_suspension",
            {
                "p_event_id": request.event_id,
                "p_identity_id": request.identity_id,
                "p_account_id": request.account_id,
                "p_moderator_id": request.moderator_id,
                "p_expected_suspended_until": (
                    request.expected_suspended_until.isoformat()
                    if request.expected_suspended_until is not None
                    else None
                ),
                "p_suspended_until": request.suspended_until.isoformat(),
                "p_reason": request.reason,
            },
        )
        try:
            status = CommunitySuspensionMutationStatus(
                str(result.get("status") or "")
            )
        except ValueError as error:
            raise AccountRepositoryError(
                "Supabase 回傳未知的社群停權 mutation 狀態。"
            ) from error
        account = self._account_from_rpc(result.get("account"))
        audit_payload = result.get("audit")
        audit = None
        if isinstance(audit_payload, Mapping):
            try:
                audit = CommunityModerationAudit.model_validate(audit_payload)
            except (TypeError, ValueError) as error:
                raise AccountRepositoryError(
                    "Supabase 社群停權 mutation 回傳無效 audit。"
                ) from error
        if status == CommunitySuspensionMutationStatus.COMMITTED and audit is None:
            raise AccountRepositoryError(
                "Supabase 社群停權 mutation 未回傳 audit。"
            )
        return CommunitySuspensionMutationResult(
            status=status,
            account=account,
            audit=audit,
        )

    def list_community_suspension_audits(
        self,
    ) -> list[CommunityModerationAudit]:
        self._rpc("exchange_purge_expired_community_suspension_audits", {})
        rows = self._request(
            "GET",
            "exchange_community_suspension_audits",
            params={
                "select": (
                    "id,identity_id,moderator_id,reason,previous_suspended_until,"
                    "new_suspended_until,created_at,retained_until"
                ),
                "order": "created_at.asc",
            },
        )
        audits: list[CommunityModerationAudit] = []
        for row in rows:
            try:
                audit = CommunityModerationAudit(
                    id=str(row["id"]),
                    resource_type="identity",
                    resource_id=str(row["identity_id"]),
                    previous_status="active",
                    new_status="suspended",
                    moderator_id=str(row.get("moderator_id") or "deleted-moderator"),
                    note=str(row.get("reason") or ""),
                    previous_suspended_until=row.get("previous_suspended_until"),
                    new_suspended_until=row.get("new_suspended_until"),
                    retained_until=row.get("retained_until"),
                    created_at=row.get("created_at"),
                )
                if (
                    audit.previous_suspended_until is not None
                    and audit.previous_suspended_until > audit.created_at
                ):
                    audit = audit.model_copy(update={"previous_status": "suspended"})
                audits.append(audit)
            except (KeyError, TypeError, ValueError) as error:
                raise AccountRepositoryError(
                    "Supabase 回傳無效的社群停權 audit。"
                ) from error
        return audits

    def save_account(self, account: UserAccount) -> UserAccount:
        """Reject compatibility upserts in the production repository.

        Supabase runtime callers must choose insert-only ``create_account`` or a
        field/auth-specific RPC so a deleted account cannot be recreated by an
        old full-model write.
        """
        raise AccountRepositoryError(
            "Supabase 不允許相容帳號 upsert；請使用 create_account 或欄位級 RPC。"
        )

    @staticmethod
    def _account_from_rpc(payload: object) -> UserAccount | None:
        if payload is None:
            return None
        if not isinstance(payload, Mapping):
            raise AccountRepositoryError("Supabase 原子操作缺少有效的帳號資料。")
        profile = dict(payload.get("profile") or {})
        profile["id"] = payload.get("id")
        profile["email"] = payload.get("email")
        if payload.get("created_at") is not None:
            profile["created_at"] = payload["created_at"]
        if payload.get("updated_at") is not None:
            profile["updated_at"] = payload["updated_at"]
        if "community_suspended_until" in payload:
            profile["community_suspended_until"] = payload.get(
                "community_suspended_until"
            )
        profile.setdefault("application_workspaces", [])
        try:
            return UserAccount.model_validate(profile)
        except (TypeError, ValueError) as error:
            raise AccountRepositoryError("Supabase 原子操作回傳無效帳號資料。") from error

    def commit_oauth_login(
        self, request: OAuthLoginMutationRequest
    ) -> OAuthLoginMutationResult:
        payload = self._rpc(
            "exchange_commit_oauth_login",
            {
                "p_provider": request.provider.value,
                "p_subject": request.subject,
                "p_trusted_email": (
                    request.trusted_email.strip().casefold()
                    if request.trusted_email
                    else None
                ),
                "p_display_name": request.display_name,
                "p_avatar_url": request.avatar_url,
                "p_home_university": request.home_university,
                "p_new_account_id": request.new_account_id,
                "p_session_id": request.session_id,
                "p_session_token_hash": request.session_token_hash,
                "p_session_expires_at": request.session_expires_at.isoformat(),
                "p_occurred_at": request.occurred_at.isoformat(),
            },
        )
        try:
            status = OAuthLoginMutationStatus(str(payload.get("status") or ""))
        except ValueError as error:
            raise AccountRepositoryError(
                "Supabase 回傳未知的 OAuth 帳號操作狀態。"
            ) from error
        account = self._account_from_rpc(payload.get("account"))
        session_payload = payload.get("session")
        try:
            session = (
                AccountSessionRecord.model_validate(session_payload)
                if session_payload is not None
                else None
            )
        except (TypeError, ValueError) as error:
            raise AccountRepositoryError("Supabase 原子操作回傳無效 session。") from error
        if status == OAuthLoginMutationStatus.COMMITTED and (
            account is None or session is None
        ):
            raise AccountRepositoryError("Supabase OAuth 原子操作缺少完成結果。")
        return OAuthLoginMutationResult(
            status=status,
            account=account,
            session=session,
        )

    def commit_student_verification(
        self, request: StudentVerificationMutationRequest
    ) -> StudentVerificationMutationResult:
        payload = self._rpc(
            "exchange_commit_student_verification",
            {
                "p_account_id": request.account_id,
                "p_expected_session_id": request.session_id,
                "p_expected_session_token_hash": request.session_token_hash,
                "p_school_name": request.school_name,
                "p_department_name": request.department_name,
                "p_verification_method": request.verification_method.value,
                "p_school_email_verified": request.school_email_verified,
                "p_verified_at": request.verified_at.isoformat(),
            },
        )
        try:
            status = StudentVerificationMutationStatus(
                str(payload.get("status") or "")
            )
        except ValueError as error:
            raise AccountRepositoryError(
                "Supabase 回傳未知的學生身分操作狀態。"
            ) from error
        account = self._account_from_rpc(payload.get("account"))
        if status in {
            StudentVerificationMutationStatus.COMMITTED,
            StudentVerificationMutationStatus.ALREADY_VERIFIED,
        } and account is None:
            raise AccountRepositoryError("Supabase 學生身分原子操作缺少帳號結果。")
        return StudentVerificationMutationResult(status=status, account=account)

    def commit_account_deletion(
        self, request: AccountDeletionMutationRequest
    ) -> AccountDeletionMutationResult:
        payload = self._rpc(
            "exchange_commit_account_deletion",
            {
                "p_mutation_id": request.mutation_id,
                "p_request_fingerprint": account_deletion_mutation_fingerprint(
                    request
                ),
                "p_account_id": request.account_id,
                "p_session_id": request.session_id,
                "p_session_token_hash": request.session_token_hash,
                "p_email_fingerprint": request.email_fingerprint,
                "p_pending_report_retention_days": (
                    request.pending_report_retention_days
                ),
                "p_replacement_name": request.replacement_name,
            },
        )
        try:
            status = AccountDeletionMutationStatus(
                str(payload.get("status") or "")
            )
        except ValueError as error:
            raise AccountRepositoryError(
                "Supabase 回傳未知的帳號刪除狀態。"
            ) from error
        object_keys = payload.get("storage_object_keys") or []
        counts = payload.get("counts") or {}
        if not isinstance(object_keys, list) or not all(
            isinstance(value, str) for value in object_keys
        ):
            raise AccountRepositoryError(
                "Supabase 帳號刪除回傳無效的 Storage 清單。"
            )
        if not isinstance(counts, Mapping):
            raise AccountRepositoryError("Supabase 帳號刪除回傳無效計數。")
        try:
            normalized_counts = {
                str(key): int(value) for key, value in counts.items()
            }
        except (TypeError, ValueError) as error:
            raise AccountRepositoryError(
                "Supabase 帳號刪除回傳無效計數。"
            ) from error
        return AccountDeletionMutationResult(
            status=status,
            storage_object_keys=object_keys,
            counts=normalized_counts,
            idempotent=bool(payload.get("idempotent", False)),
        )

    def complete_account_deletion_storage(
        self, mutation_id: str, session_token_hash: str
    ) -> AccountDeletionMutationStatus:
        payload = self._rpc(
            "exchange_complete_account_deletion_storage",
            {
                "p_mutation_id": mutation_id,
                "p_session_token_hash": session_token_hash,
            },
        )
        try:
            return AccountDeletionMutationStatus(
                str(payload.get("status") or "")
            )
        except ValueError as error:
            raise AccountRepositoryError(
                "Supabase 回傳未知的帳號 Storage 清理狀態。"
            ) from error

    def list_pending_account_deletion_storage(
        self, limit: int = 100
    ) -> list[AccountDeletionStorageJob]:
        if limit < 1 or limit > 500:
            raise ValueError("帳號 Storage 清理批次必須介於 1 到 500。")
        payload = self._rpc(
            "exchange_list_pending_account_deletion_storage",
            {"p_limit": limit},
        )
        jobs = payload.get("jobs") or []
        if not isinstance(jobs, list):
            raise AccountRepositoryError(
                "Supabase 回傳無效的待清理帳號 Storage 工作。"
            )
        try:
            return [AccountDeletionStorageJob.model_validate(job) for job in jobs]
        except (TypeError, ValueError) as error:
            raise AccountRepositoryError(
                "Supabase 回傳無效的待清理帳號 Storage 工作。"
            ) from error

    def complete_pending_account_deletion_storage(
        self, mutation_id: str
    ) -> AccountDeletionMutationStatus:
        payload = self._rpc(
            "exchange_complete_pending_account_deletion_storage",
            {"p_mutation_id": mutation_id},
        )
        try:
            return AccountDeletionMutationStatus(
                str(payload.get("status") or "")
            )
        except ValueError as error:
            raise AccountRepositoryError(
                "Supabase 回傳未知的待清理帳號 Storage 狀態。"
            ) from error

    def purge_account_deletion_receipts(self) -> int:
        payload = self._rpc("exchange_purge_account_deletion_receipts", {})
        if payload.get("status") != AccountDeletionMutationStatus.COMMITTED.value:
            raise AccountRepositoryError("Supabase 無法清理帳號刪除收據。")
        try:
            count = int(payload.get("receipts", 0))
        except (TypeError, ValueError) as error:
            raise AccountRepositoryError(
                "Supabase 回傳無效的帳號刪除收據清理計數。"
            ) from error
        if count < 0:
            raise AccountRepositoryError(
                "Supabase 回傳無效的帳號刪除收據清理計數。"
            )
        return count

    def delete_account(self, account_id: str) -> None:
        del account_id
        raise AccountRepositoryError(
            "Supabase 帳號刪除必須使用 exchange_commit_account_deletion 原子操作。"
        )

    def find_session_by_token_hash(self, token_hash: str) -> AccountSessionRecord | None:
        rows = self._request(
            "GET",
            self._sessions_table,
            params={
                "select": "id,account_id,token_hash,expires_at,created_at",
                "token_hash": f"eq.{token_hash}",
                "limit": "1",
            },
        )
        return AccountSessionRecord.model_validate(rows[0]) if rows else None

    def save_session(self, session: AccountSessionRecord) -> AccountSessionRecord:
        self._request(
            "POST",
            self._sessions_table,
            params={"on_conflict": "id"},
            json_body=session.model_dump(mode="json"),
            prefer="resolution=merge-duplicates,return=minimal",
        )
        return session

    def delete_session_by_token_hash(self, token_hash: str) -> None:
        self._request(
            "DELETE",
            self._sessions_table,
            params={"token_hash": f"eq.{token_hash}"},
        )

    def purge_expired_sessions(self, now: datetime | None = None) -> int:
        rows = self._request(
            "DELETE",
            self._sessions_table,
            params={"expires_at": f"lte.{(now or utc_now()).isoformat()}", "select": "id"},
            prefer="return=representation",
        )
        return len(rows)

    def list_email_verifications(
        self, email_fingerprint: str | None = None
    ) -> list[EmailVerificationChallenge]:
        params = {
            "select": "*",
            "order": "requested_at.desc",
            "limit": "100",
        }
        if email_fingerprint is not None:
            params["email_fingerprint"] = f"eq.{email_fingerprint}"
        rows = self._request(
            "GET",
            self._email_verifications_table,
            params=params,
        )
        return [EmailVerificationChallenge.model_validate(row) for row in rows]

    def save_email_verification(
        self, challenge: EmailVerificationChallenge
    ) -> EmailVerificationChallenge:
        rows = self._request(
            "POST",
            self._email_verifications_table,
            params={"on_conflict": "id"},
            json_body=challenge.model_dump(mode="json"),
            prefer="resolution=merge-duplicates,return=representation",
        )
        return EmailVerificationChallenge.model_validate(rows[0]) if rows else challenge

    def delete_email_verifications(self, email_fingerprint: str) -> int:
        rows = self._request(
            "DELETE",
            self._email_verifications_table,
            params={
                "email_fingerprint": f"eq.{email_fingerprint}",
                "select": "id",
            },
            prefer="return=representation",
        )
        return len(rows)

    def purge_expired_email_verifications(
        self, now: datetime | None = None
    ) -> int:
        rows = self._request(
            "DELETE",
            self._email_verifications_table,
            params={
                "or": (
                    f"(expires_at.lte.{(now or utc_now()).isoformat()},"
                    "consumed_at.not.is.null)"
                ),
                "select": "id",
            },
            prefer="return=representation",
        )
        return len(rows)

    def list_notifications(
        self, account_id: str, limit: int = 100
    ) -> list[AccountNotification]:
        rows = self._request(
            "GET",
            self._notifications_table,
            params={
                "select": "*",
                "account_id": f"eq.{account_id}",
                "order": "created_at.desc",
                "limit": str(limit),
            },
        )
        return [AccountNotification.model_validate(row) for row in rows]

    def find_notification_by_dedupe(
        self, account_id: str, dedupe_key: str
    ) -> AccountNotification | None:
        rows = self._request(
            "GET",
            self._notifications_table,
            params={
                "select": "*",
                "account_id": f"eq.{account_id}",
                "dedupe_key": f"eq.{dedupe_key}",
                "limit": "1",
            },
        )
        return AccountNotification.model_validate(rows[0]) if rows else None

    def find_notification_by_id(
        self, account_id: str, notification_id: str
    ) -> AccountNotification | None:
        rows = self._request(
            "GET",
            self._notifications_table,
            params={
                "select": "*",
                "account_id": f"eq.{account_id}",
                "id": f"eq.{notification_id}",
                "limit": "1",
            },
        )
        return AccountNotification.model_validate(rows[0]) if rows else None

    def save_notification(self, notification: AccountNotification) -> AccountNotification:
        existing = self.find_notification_by_dedupe(
            notification.account_id, notification.dedupe_key
        )
        if existing is not None:
            return existing
        rows = self._request(
            "POST",
            self._notifications_table,
            params={"on_conflict": "account_id,dedupe_key"},
            json_body=notification.model_dump(mode="json"),
            prefer="resolution=ignore-duplicates,return=representation",
        )
        if rows:
            return AccountNotification.model_validate(rows[0])
        concurrent = self.find_notification_by_dedupe(
            notification.account_id, notification.dedupe_key
        )
        return concurrent or notification

    def mark_notification_read(
        self, account_id: str, notification_id: str, read_at: datetime
    ) -> AccountNotification | None:
        rows = self._request(
            "PATCH",
            self._notifications_table,
            params={
                "id": f"eq.{notification_id}",
                "account_id": f"eq.{account_id}",
            },
            json_body={"read_at": read_at.isoformat()},
            prefer="return=representation",
        )
        return AccountNotification.model_validate(rows[0]) if rows else None

    def mark_all_notifications_read(self, account_id: str, read_at: datetime) -> int:
        rows = self._request(
            "PATCH",
            self._notifications_table,
            params={"account_id": f"eq.{account_id}", "read_at": "is.null"},
            json_body={"read_at": read_at.isoformat()},
            prefer="return=representation",
        )
        return len(rows)

    def find_delivery(
        self, notification_id: str, channel: str
    ) -> NotificationDelivery | None:
        rows = self._request(
            "GET",
            self._deliveries_table,
            params={
                "select": "*",
                "notification_id": f"eq.{notification_id}",
                "channel": f"eq.{channel}",
                "limit": "1",
            },
        )
        return NotificationDelivery.model_validate(rows[0]) if rows else None

    def list_due_deliveries(
        self, now: datetime, limit: int = 100
    ) -> list[NotificationDelivery]:
        rows = self._request(
            "GET",
            self._deliveries_table,
            params={
                "select": "*",
                "status": "in.(pending,retrying)",
                "next_attempt_at": f"lte.{now.isoformat()}",
                "order": "next_attempt_at.asc",
                "limit": str(limit),
            },
        )
        return [NotificationDelivery.model_validate(row) for row in rows]

    def save_delivery(self, delivery: NotificationDelivery) -> NotificationDelivery:
        rows = self._request(
            "POST",
            self._deliveries_table,
            params={"on_conflict": "id"},
            json_body=delivery.model_dump(mode="json"),
            prefer="resolution=merge-duplicates,return=representation",
        )
        return NotificationDelivery.model_validate(rows[0]) if rows else delivery


def create_account_repository(
    data_dir: Path,
    environ: Mapping[str, str] | None = None,
) -> AccountRepository:
    environment = os.environ if environ is None else environ
    mode = environment.get("EXCHANGE_ACCOUNT_REPOSITORY", "auto").strip().casefold()
    runtime = environment.get("EXCHANGE_ENVIRONMENT", "development").strip().casefold()
    url = (
        environment.get("EXCHANGE_SUPABASE_URL")
        or environment.get("SUPABASE_URL")
        or ""
    ).strip()
    secret_key = (
        environment.get("EXCHANGE_SUPABASE_SECRET_KEY")
        or environment.get("SUPABASE_SECRET_KEY")
        or environment.get("SUPABASE_SERVICE_ROLE_KEY")
        or ""
    ).strip()
    if mode not in {"auto", "jsonl", "supabase"}:
        raise AccountRepositoryError(
            "EXCHANGE_ACCOUNT_REPOSITORY 必須是 auto、jsonl 或 supabase。"
        )
    if runtime in {"production", "prod"} and mode == "jsonl":
        raise AccountRepositoryError(
            "正式環境禁止使用 JSONL 帳號資料；請設定 Supabase repository。"
        )
    if mode == "jsonl":
        return JsonlAccountRepository(data_dir)
    if bool(url) != bool(secret_key):
        raise AccountRepositoryError("Supabase URL 與 secret key 必須同時設定。")
    if mode == "supabase" or (url and secret_key):
        if not url or not secret_key:
            raise AccountRepositoryError("Supabase repository 尚未完成伺服器端設定。")
        return SupabaseAccountRepository(url, secret_key)
    if runtime in {"production", "prod"}:
        raise AccountRepositoryError(
            "正式環境禁止使用 JSONL 帳號資料；請設定 Supabase repository。"
        )
    return JsonlAccountRepository(data_dir)
