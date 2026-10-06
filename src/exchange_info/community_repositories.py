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
from typing import Any, Generator, Protocol, TypeAlias

import requests
from pydantic import BaseModel, Field, field_validator, model_validator
from .supabase_keys import supabase_key_headers
from .access_control import catalog_home_university, is_platform_admin

from .models import (
    AnonymousIdentity,
    CommunityAnswer,
    CommunityBlock,
    CommunityBoardKind,
    CommunityIdentityMode,
    CommunityModerationAudit,
    CommunityPost,
    CommunityPostComment,
    CommunityReaction,
    CommunityBookmark,
    CommunityPublishEvent,
    CommunityQuestion,
    CommunityReport,
    CommunityReportStatus,
    ConversationStatus,
    ExperienceSubmission,
    ModerationStatus,
    PrivateConversation,
    PrivateMessage,
    PublicChatMessage,
    UserAccount,
    utc_now,
)
from .storage import (
    data_paths,
    load_anonymous_identities,
    load_community_answers,
    load_community_blocks,
    load_community_moderation_audits,
    load_community_post_comments,
    load_community_posts,
    load_community_publish_events,
    load_community_questions,
    load_community_reports,
    load_experience_submissions,
    load_private_conversations,
    load_private_messages,
    load_public_chat_messages,
    load_user_accounts,
    read_jsonl,
    save_anonymous_identities,
    save_community_answers,
    save_community_blocks,
    save_community_moderation_audits,
    save_community_post_comments,
    save_community_posts,
    save_community_publish_events,
    save_community_questions,
    save_community_reports,
    save_experience_submissions,
    save_private_conversations,
    save_private_messages,
    save_public_chat_messages,
    storage_path_lock,
    write_jsonl,
)


PUBLIC_RATE_WINDOW = timedelta(minutes=10)
NEW_ACCOUNT_WINDOW = timedelta(hours=24)
NEW_ACCOUNT_PUBLICATION_LIMIT = 5
ESTABLISHED_ACCOUNT_PUBLICATION_LIMIT = 20
PUBLIC_BOARD_NAMES = frozenset({"公共留學板", "一般留學討論", "語言學校板"})
PUBLIC_MUTATION_PATH_NAME = "community_public_mutations.jsonl"
PUBLICATION_SERVER_OWNED_FIELDS = frozenset(
    {
        "id",
        "author_id",
        "author_identity_id",
        "display_name",
        "created_at",
        "updated_at",
        "revision",
        "answer_count",
        "comment_count",
        "viewer_can_delete",
        "deleted",
        "verified_experience",
        "status",
    }
)


class CommunityRepositoryError(RuntimeError):
    """Raised when a community persistence command cannot be completed safely."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class PublicCommunityResourceType(str, Enum):
    QUESTION = "question"
    ANSWER = "answer"
    POST = "post"
    COMMENT = "comment"
    CHAT = "chat"
    EXPERIENCE = "experience"


PublicCommunityContent: TypeAlias = (
    CommunityQuestion
    | CommunityAnswer
    | CommunityPost
    | CommunityPostComment
    | PublicChatMessage
    | ExperienceSubmission
)


class CommunityIdentityMutationStatus(str, Enum):
    COMMITTED = "committed"
    INVALID_REQUEST = "invalid_request"
    ACCOUNT_MISSING = "account_missing"
    IDENTITY_CONFLICT = "identity_conflict"
    IDEMPOTENCY_CONFLICT = "idempotency_conflict"
    INTEGRITY_CONFLICT = "integrity_conflict"


class PublicCommunityPublicationStatus(str, Enum):
    COMMITTED = "committed"
    INVALID_REQUEST = "invalid_request"
    ACCOUNT_MISSING = "account_missing"
    IDENTITY_MISSING = "identity_missing"
    IDENTITY_CONFLICT = "identity_conflict"
    ACCOUNT_SUSPENDED = "account_suspended"
    EMAIL_UNVERIFIED = "email_unverified"
    STUDENT_VERIFICATION_REQUIRED = "student_verification_required"
    BOARD_FORBIDDEN = "board_forbidden"
    PARENT_MISSING = "parent_missing"
    RATE_LIMITED = "rate_limited"
    IDEMPOTENCY_CONFLICT = "idempotency_conflict"
    INTEGRITY_CONFLICT = "integrity_conflict"


class PublicCommunityDeleteStatus(str, Enum):
    COMMITTED = "committed"
    INVALID_REQUEST = "invalid_request"
    ACCOUNT_MISSING = "account_missing"
    IDENTITY_MISSING = "identity_missing"
    IDENTITY_CONFLICT = "identity_conflict"
    ACCOUNT_SUSPENDED = "account_suspended"
    RESOURCE_MISSING = "resource_missing"
    NOT_OWNER = "not_owner"
    STATUS_CONFLICT = "status_conflict"
    IDEMPOTENCY_CONFLICT = "idempotency_conflict"
    INTEGRITY_CONFLICT = "integrity_conflict"


class PublicCommunityModerationStatus(str, Enum):
    COMMITTED = "committed"
    INVALID_REQUEST = "invalid_request"
    MODERATOR_MISSING = "moderator_missing"
    RESOURCE_MISSING = "resource_missing"
    NO_CHANGE = "no_change"
    STATUS_CONFLICT = "status_conflict"
    IDEMPOTENCY_CONFLICT = "idempotency_conflict"
    INTEGRITY_CONFLICT = "integrity_conflict"


class PublicAuthorAnonymizationStatus(str, Enum):
    COMMITTED = "committed"
    INVALID_REQUEST = "invalid_request"
    IDENTITY_MISSING = "identity_missing"
    IDENTITY_CONFLICT = "identity_conflict"
    IDEMPOTENCY_CONFLICT = "idempotency_conflict"
    INTEGRITY_CONFLICT = "integrity_conflict"


class PrivateCommunityMutationStatus(str, Enum):
    COMMITTED = "committed"
    INVALID_REQUEST = "invalid_request"
    ACCOUNT_MISSING = "account_missing"
    IDENTITY_MISSING = "identity_missing"
    IDENTITY_CONFLICT = "identity_conflict"
    ACCOUNT_SUSPENDED = "account_suspended"
    RECIPIENT_MISSING = "recipient_missing"
    SELF_TARGET = "self_target"
    CONVERSATION_MISSING = "conversation_missing"
    NOT_PARTICIPANT = "not_participant"
    RECIPIENT_ONLY = "recipient_only"
    BLOCKED = "blocked"
    STATUS_CONFLICT = "status_conflict"
    RESOURCE_MISSING = "resource_missing"
    SELF_REPORT = "self_report"
    CONVERSATION_REQUIRED = "conversation_required"
    REPORT_MISSING = "report_missing"
    NO_CHANGE = "no_change"
    IDEMPOTENCY_CONFLICT = "idempotency_conflict"
    INTEGRITY_CONFLICT = "integrity_conflict"


class CommunityIdentityMutationRequest(BaseModel):
    mutation_id: str = Field(min_length=16, max_length=128)
    identity: AnonymousIdentity

    @model_validator(mode="after")
    def validate_identity(self) -> CommunityIdentityMutationRequest:
        if not self.identity.display_name.strip():
            raise ValueError("社群身分顯示名稱不可為空白。")
        if len(self.identity.access_token_hash) != 64 or any(
            character not in "0123456789abcdef"
            for character in self.identity.access_token_hash.casefold()
        ):
            raise ValueError("社群身分 token hash 必須是 SHA-256 hex。")
        return self


class CommunityIdentityMutationResult(BaseModel):
    status: CommunityIdentityMutationStatus
    identity: AnonymousIdentity | None = None


class PublicCommunityPublicationRequest(BaseModel):
    mutation_id: str = Field(min_length=16, max_length=128)
    account_id: str = Field(min_length=1, max_length=128)
    identity_id: str = Field(min_length=1, max_length=128)
    access_token_hash: str = Field(pattern=r"^[0-9a-fA-F]{64}$")
    resource_type: PublicCommunityResourceType
    content: dict[str, Any]

    @model_validator(mode="after")
    def validate_content_shape(self) -> PublicCommunityPublicationRequest:
        normalized = _content_from_payload(self.resource_type, self.content)
        self.content = normalized.model_dump(mode="json")
        return self


class PublicCommunityPublicationResult(BaseModel):
    status: PublicCommunityPublicationStatus
    content: dict[str, Any] | None = None
    retry_after_seconds: int | None = Field(default=None, ge=1)

    def parsed_content(self) -> PublicCommunityContent | None:
        if self.content is None:
            return None
        resource_type = PublicCommunityResourceType(str(self.content["resource_type"]))
        return _content_from_payload(resource_type, self.content["payload"])


class PublicCommunityDeleteRequest(BaseModel):
    mutation_id: str = Field(min_length=16, max_length=128)
    account_id: str = Field(min_length=1, max_length=128)
    identity_id: str = Field(min_length=1, max_length=128)
    access_token_hash: str = Field(pattern=r"^[0-9a-fA-F]{64}$")
    resource_type: PublicCommunityResourceType
    resource_id: str = Field(min_length=1, max_length=128)

    @field_validator("access_token_hash")
    @classmethod
    def normalize_access_token_hash(cls, value: str) -> str:
        return value.casefold()

    @model_validator(mode="after")
    def restrict_deletable_types(self) -> PublicCommunityDeleteRequest:
        if self.resource_type not in {
            PublicCommunityResourceType.POST,
            PublicCommunityResourceType.COMMENT,
        }:
            raise ValueError("目前只有貼文與留言支援作者刪除。")
        return self


class PublicCommunityDeleteResult(BaseModel):
    status: PublicCommunityDeleteStatus
    resource_id: str | None = None
    deleted_comment_count: int = Field(default=0, ge=0)


class PublicCommunityModerationRequest(BaseModel):
    mutation_id: str = Field(min_length=16, max_length=128)
    moderator_id: str = Field(min_length=1, max_length=128)
    resource_type: PublicCommunityResourceType
    resource_id: str = Field(min_length=1, max_length=128)
    expected_status: ModerationStatus
    status: ModerationStatus
    note: str = Field(min_length=2, max_length=500)

    @field_validator("status")
    @classmethod
    def restrict_status(cls, value: ModerationStatus) -> ModerationStatus:
        if value not in {ModerationStatus.APPROVED, ModerationStatus.HIDDEN}:
            raise ValueError("管理操作只能核准或隱藏內容。")
        return value

    @field_validator("expected_status")
    @classmethod
    def restrict_expected_status(cls, value: ModerationStatus) -> ModerationStatus:
        if value not in {
            ModerationStatus.PENDING,
            ModerationStatus.APPROVED,
            ModerationStatus.HIDDEN,
        }:
            raise ValueError("預期 moderation 狀態無效。")
        return value

    @field_validator("note")
    @classmethod
    def normalize_note(cls, value: str) -> str:
        return value.strip()


class PublicCommunityModerationResult(BaseModel):
    status: PublicCommunityModerationStatus
    content: dict[str, Any] | None = None
    audit: CommunityModerationAudit | None = None


class PublicAuthorAnonymizationRequest(BaseModel):
    mutation_id: str = Field(min_length=16, max_length=128)
    identity_id: str = Field(min_length=1, max_length=128)
    expected_account_id: str | None = Field(default=None, min_length=1, max_length=128)
    replacement_name: str = Field(default="已刪除帳號", min_length=2, max_length=30)

    @field_validator("replacement_name")
    @classmethod
    def normalize_replacement_name(cls, value: str) -> str:
        return value.strip()


class PublicAuthorAnonymizationResult(BaseModel):
    status: PublicAuthorAnonymizationStatus
    counts: dict[str, int] = Field(default_factory=dict)


class PrivateCommunityActorRequest(BaseModel):
    mutation_id: str = Field(min_length=16, max_length=128)
    account_id: str = Field(min_length=1, max_length=128)
    identity_id: str = Field(min_length=1, max_length=128)
    access_token_hash: str = Field(pattern=r"^[0-9a-fA-F]{64}$")

    @field_validator("access_token_hash")
    @classmethod
    def normalize_private_access_token_hash(cls, value: str) -> str:
        return value.casefold()


class PrivateConversationMutationRequest(PrivateCommunityActorRequest):
    recipient_identity_id: str = Field(min_length=1, max_length=128)
    conversation: PrivateConversation
    initial_message: PrivateMessage

    @model_validator(mode="after")
    def validate_private_conversation(self) -> PrivateConversationMutationRequest:
        if (
            self.conversation.sender_id != self.identity_id
            or self.conversation.recipient_id != self.recipient_identity_id
            or self.conversation.status != ConversationStatus.PENDING
            or self.initial_message.conversation_id != self.conversation.id
            or self.initial_message.author_id != self.identity_id
        ):
            raise ValueError("私訊邀請的身分或初始訊息不一致。")
        return self


class PrivateConversationStatusMutationRequest(PrivateCommunityActorRequest):
    conversation_id: str = Field(min_length=1, max_length=128)
    expected_status: ConversationStatus
    status: ConversationStatus

    @model_validator(mode="after")
    def validate_private_status_transition(
        self,
    ) -> PrivateConversationStatusMutationRequest:
        if (
            self.expected_status != ConversationStatus.PENDING
            or self.status != ConversationStatus.ACCEPTED
        ):
            raise ValueError("目前只允許收件者接受待處理邀請。")
        return self


class PrivateMessageMutationRequest(PrivateCommunityActorRequest):
    message: PrivateMessage

    @model_validator(mode="after")
    def validate_private_message(self) -> PrivateMessageMutationRequest:
        if self.message.author_id != self.identity_id:
            raise ValueError("私訊作者與操作身分不一致。")
        return self


class CommunityBlockMutationRequest(PrivateCommunityActorRequest):
    block: CommunityBlock

    @model_validator(mode="after")
    def validate_block(self) -> CommunityBlockMutationRequest:
        if self.block.owner_id != self.identity_id:
            raise ValueError("封鎖發起者與操作身分不一致。")
        return self


class CommunityReportMutationRequest(PrivateCommunityActorRequest):
    report: CommunityReport

    @model_validator(mode="after")
    def validate_report(self) -> CommunityReportMutationRequest:
        if self.report.reporter_id != self.identity_id:
            raise ValueError("檢舉者與操作身分不一致。")
        if self.report.status != CommunityReportStatus.PENDING:
            raise ValueError("新檢舉必須是 pending。")
        return self


class CommunityReportReviewMutationRequest(BaseModel):
    mutation_id: str = Field(min_length=16, max_length=128)
    moderator_id: str = Field(min_length=1, max_length=128)
    report_id: str = Field(min_length=1, max_length=128)
    expected_status: CommunityReportStatus = CommunityReportStatus.PENDING
    status: CommunityReportStatus
    note: str = Field(min_length=2, max_length=500)

    @field_validator("status")
    @classmethod
    def restrict_report_status(
        cls, value: CommunityReportStatus
    ) -> CommunityReportStatus:
        if value not in {
            CommunityReportStatus.RESOLVED,
            CommunityReportStatus.DISMISSED,
        }:
            raise ValueError("檢舉只能標記為 resolved 或 dismissed。")
        return value

    @field_validator("note")
    @classmethod
    def normalize_report_note(cls, value: str) -> str:
        return value.strip()


class PrivateCommunityIdentityPurgeRequest(BaseModel):
    mutation_id: str = Field(min_length=16, max_length=128)
    identity_id: str = Field(min_length=1, max_length=128)
    expected_account_id: str = Field(min_length=1, max_length=128)
    pending_report_retention_days: int = Field(default=90, ge=1, le=365)


class PrivateCommunityMutationResult(BaseModel):
    status: PrivateCommunityMutationStatus
    conversation: PrivateConversation | None = None
    message: PrivateMessage | None = None
    block: CommunityBlock | None = None
    report: CommunityReport | None = None
    audit: CommunityModerationAudit | None = None
    counts: dict[str, int] = Field(default_factory=dict)


class PublicCommunityModerationQueue(BaseModel):
    question: list[CommunityQuestion] = Field(default_factory=list)
    answer: list[CommunityAnswer] = Field(default_factory=list)
    post: list[CommunityPost] = Field(default_factory=list)
    comment: list[CommunityPostComment] = Field(default_factory=list)
    chat: list[PublicChatMessage] = Field(default_factory=list)
    experience: list[ExperienceSubmission] = Field(default_factory=list)


class _CommunityMutationRecord(BaseModel):
    mutation_id: str
    operation: str
    fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    result: dict[str, Any]
    created_at: datetime


def community_mutation_fingerprint(
    operation: str,
    payload: BaseModel | Mapping[str, object],
) -> str:
    serialized = (
        payload.model_dump(mode="json")
        if isinstance(payload, BaseModel)
        else dict(payload)
    )
    canonical = json.dumps(
        {"operation": operation, "payload": serialized},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def public_community_publication_fingerprint(
    request: PublicCommunityPublicationRequest,
) -> str:
    """Hash client semantics, not generated resource/projection fields."""

    semantic_content = {
        key: value
        for key, value in request.content.items()
        if key not in PUBLICATION_SERVER_OWNED_FIELDS
    }
    return community_mutation_fingerprint(
        "publication",
        {
            "account_id": request.account_id,
            "identity_id": request.identity_id,
            "access_token_hash": request.access_token_hash.casefold(),
            "resource_type": request.resource_type.value,
            "content": semantic_content,
        },
    )


def private_community_mutation_fingerprint(
    operation: str,
    request: BaseModel,
) -> str:
    """Hash private-community client semantics, excluding generated fields."""

    payload = request.model_dump(mode="json")
    if operation == "private_conversation":
        payload["conversation"] = {
            key: value
            for key, value in payload["conversation"].items()
            if key
            not in {
                "id",
                "sender_name",
                "recipient_name",
                "status",
                "created_at",
                "updated_at",
            }
        }
        payload["initial_message"] = {
            key: value
            for key, value in payload["initial_message"].items()
            if key
            not in {"id", "conversation_id", "display_name", "created_at"}
        }
    elif operation == "private_message":
        payload["message"] = {
            key: value
            for key, value in payload["message"].items()
            if key not in {"id", "display_name", "created_at"}
        }
    elif operation == "community_block":
        payload["block"] = {
            key: value
            for key, value in payload["block"].items()
            if key not in {"id", "created_at"}
        }
    elif operation == "community_report":
        payload["report"] = {
            key: value
            for key, value in payload["report"].items()
            if key
            not in {
                "id",
                "status",
                "reviewed_by",
                "reviewed_at",
                "resolution_note",
                "retained_until",
                "created_at",
            }
        }
    return community_mutation_fingerprint(operation, payload)


def _content_from_payload(
    resource_type: PublicCommunityResourceType,
    payload: Mapping[str, Any],
) -> PublicCommunityContent:
    model_by_type: dict[PublicCommunityResourceType, type[BaseModel]] = {
        PublicCommunityResourceType.QUESTION: CommunityQuestion,
        PublicCommunityResourceType.ANSWER: CommunityAnswer,
        PublicCommunityResourceType.POST: CommunityPost,
        PublicCommunityResourceType.COMMENT: CommunityPostComment,
        PublicCommunityResourceType.CHAT: PublicChatMessage,
        PublicCommunityResourceType.EXPERIENCE: ExperienceSubmission,
    }
    return model_by_type[resource_type].model_validate(payload)  # type: ignore[return-value]


def _content_result_payload(
    resource_type: PublicCommunityResourceType,
    content: PublicCommunityContent,
) -> dict[str, Any]:
    return {
        "resource_type": resource_type.value,
        "payload": content.model_dump(mode="json"),
    }


def _content_row_from_supabase(
    resource_type: PublicCommunityResourceType,
    row: Mapping[str, Any],
) -> dict[str, Any]:
    """Translate the durable SQL row into the existing API model contract."""

    payload = dict(row)
    if "author_identity_id" in payload:
        author_id = payload.pop("author_identity_id")
        if author_id is None and resource_type in {
            PublicCommunityResourceType.POST,
            PublicCommunityResourceType.COMMENT,
            PublicCommunityResourceType.CHAT,
        }:
            author_id = ""
        payload["author_id"] = author_id
    # SQL-owned CAS/timestamp columns intentionally remain extra fields; the
    # current Pydantic read models ignore them.  These UI-only values are not
    # persisted in SQL and therefore keep their model defaults.
    if resource_type == PublicCommunityResourceType.POST:
        payload.setdefault("comment_count", 0)
        payload.setdefault("viewer_can_delete", False)
    elif resource_type == PublicCommunityResourceType.COMMENT:
        payload.setdefault("viewer_can_delete", False)
    elif resource_type == PublicCommunityResourceType.QUESTION:
        payload.setdefault("answer_count", 0)
    return payload


def _identity_row_from_supabase(
    row: Mapping[str, Any],
    *,
    fallback_access_token_hash: str | None = None,
) -> dict[str, Any]:
    payload = dict(row)
    if not payload.get("access_token_hash") and fallback_access_token_hash:
        payload["access_token_hash"] = fallback_access_token_hash.casefold()
    return payload


def _moderation_audit_row_from_supabase(
    row: Mapping[str, Any],
) -> dict[str, Any]:
    payload = dict(row)
    if payload.get("moderator_id") is None:
        payload["moderator_id"] = ""
    return payload


def _school_key(value: str | None) -> str:
    return " ".join((value or "").strip().casefold().split())


def reaction_summary(rows, resource_type, resource_id, account_id=None):
    matching = [row for row in rows if row.resource_type == resource_type and row.resource_id == resource_id]
    return {"counts": {kind: sum(row.reaction == kind for row in matching) for kind in ("helpful", "thanks")},
            "viewer_reaction": next((row.reaction for row in matching if row.account_id == account_id), None)}


def _save_reactions(rows, data_dir):
    try:
        write_jsonl(Path(data_dir) / "processed" / "community_reactions.jsonl", rows)
    except OSError as error:
        raise CommunityRepositoryError("反應暫時無法儲存，請稍後重試。") from error


def _save_bookmarks(rows, data_dir):
    try:
        write_jsonl(Path(data_dir) / "processed" / "community_bookmarks.jsonl", rows)
    except OSError as error:
        raise CommunityRepositoryError("收藏暫時無法儲存，請稍後重試。") from error


class CommunityRepository(Protocol):
    backend_name: str

    def list_identities(self) -> list[AnonymousIdentity]: ...

    def find_identity_by_id(self, identity_id: str) -> AnonymousIdentity | None: ...

    def find_identity_by_account(self, account_id: str) -> AnonymousIdentity | None: ...

    def commit_identity(
        self,
        request: CommunityIdentityMutationRequest,
        *,
        now: datetime | None = None,
    ) -> CommunityIdentityMutationResult: ...

    def commit_publication(
        self,
        request: PublicCommunityPublicationRequest,
        *,
        now: datetime | None = None,
    ) -> PublicCommunityPublicationResult: ...

    def list_questions(self) -> list[CommunityQuestion]: ...

    def list_answers(self) -> list[CommunityAnswer]: ...

    def list_posts(self) -> list[CommunityPost]: ...

    def list_comments(self) -> list[CommunityPostComment]: ...
    def list_reactions(self) -> list[CommunityReaction]: ...
    def set_reaction(self, account_id: str, resource_type: str, resource_id: str,
                     reaction: str | None, *, platform_admin: bool = False) -> dict[str, Any]: ...
    def purge_account_interactions(self, account_id: str) -> None: ...
    def list_bookmarks(self, account_id: str) -> list[str]: ...
    def set_bookmark(self, account_id: str, post_id: str, saved: bool) -> dict[str, Any]: ...

    def list_public_chat_messages(self) -> list[PublicChatMessage]: ...

    def list_experience_submissions(self) -> list[ExperienceSubmission]: ...

    def delete_public_content(
        self,
        request: PublicCommunityDeleteRequest,
        *,
        now: datetime | None = None,
    ) -> PublicCommunityDeleteResult: ...

    def list_moderation_queue(self) -> PublicCommunityModerationQueue: ...

    def commit_moderation(
        self,
        request: PublicCommunityModerationRequest,
        *,
        now: datetime | None = None,
    ) -> PublicCommunityModerationResult: ...

    def list_moderation_audits(self) -> list[CommunityModerationAudit]: ...

    def find_public_author(
        self,
        resource_type: PublicCommunityResourceType,
        resource_id: str,
    ) -> str | None: ...

    def anonymize_public_author(
        self,
        request: PublicAuthorAnonymizationRequest,
        *,
        now: datetime | None = None,
    ) -> PublicAuthorAnonymizationResult: ...

    def list_private_conversations(self) -> list[PrivateConversation]: ...

    def list_private_messages(self) -> list[PrivateMessage]: ...

    def list_blocks(self) -> list[CommunityBlock]: ...

    def list_reports(self, *, now: datetime | None = None) -> list[CommunityReport]: ...

    def commit_private_conversation(
        self,
        request: PrivateConversationMutationRequest,
        *,
        now: datetime | None = None,
    ) -> PrivateCommunityMutationResult: ...

    def commit_private_conversation_status(
        self,
        request: PrivateConversationStatusMutationRequest,
        *,
        now: datetime | None = None,
    ) -> PrivateCommunityMutationResult: ...

    def commit_private_message(
        self,
        request: PrivateMessageMutationRequest,
        *,
        now: datetime | None = None,
    ) -> PrivateCommunityMutationResult: ...

    def commit_block(
        self,
        request: CommunityBlockMutationRequest,
        *,
        now: datetime | None = None,
    ) -> PrivateCommunityMutationResult: ...

    def commit_report(
        self,
        request: CommunityReportMutationRequest,
        *,
        now: datetime | None = None,
    ) -> PrivateCommunityMutationResult: ...

    def commit_report_review(
        self,
        request: CommunityReportReviewMutationRequest,
        *,
        now: datetime | None = None,
    ) -> PrivateCommunityMutationResult: ...

    def purge_private_identity(
        self,
        request: PrivateCommunityIdentityPurgeRequest,
        *,
        now: datetime | None = None,
    ) -> PrivateCommunityMutationResult: ...


class JsonlCommunityRepository:
    backend_name = "jsonl"

    _PUBLIC_PATH_KEYS = (
        "community_answers",
        "community_identities",
        "community_moderation_audits",
        "community_post_comments",
        "community_posts",
        "community_publish_events",
        "community_questions",
        "experience_submissions",
        "public_chat_messages",
        "private_conversations",
        "private_messages",
        "community_blocks",
        "community_reports",
        "user_accounts",
    )

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = Path(data_dir)
        self._mutation_path = (
            self.data_dir / "processed" / PUBLIC_MUTATION_PATH_NAME
        )

    def _all_transaction_paths(self) -> list[Path]:
        paths = data_paths(self.data_dir)
        selected = {paths[key] for key in self._PUBLIC_PATH_KEYS}
        selected.add(self._mutation_path)
        selected.add(self.data_dir / "processed" / "community_reactions.jsonl")
        selected.add(self.data_dir / "processed" / "community_bookmarks.jsonl")
        return sorted(
            selected,
            key=lambda path: os.path.normcase(
                os.path.abspath(os.fspath(path))
            ).casefold(),
        )

    @contextmanager
    def _locked_all(self) -> Generator[None, None, None]:
        with ExitStack() as stack:
            for path in self._all_transaction_paths():
                stack.enter_context(storage_path_lock(path))
            yield

    @staticmethod
    def _normalize_now(now: datetime | None) -> datetime:
        current = now or utc_now()
        if current.tzinfo is None or current.utcoffset() is None:
            raise ValueError("Community mutation 時間必須包含時區。")
        return current

    def _load_mutations(self) -> list[_CommunityMutationRecord]:
        return read_jsonl(self._mutation_path, _CommunityMutationRecord)

    def _save_mutations(self, rows: list[_CommunityMutationRecord]) -> int:
        return write_jsonl(self._mutation_path, rows)

    @staticmethod
    def _find_mutation(
        rows: list[_CommunityMutationRecord],
        mutation_id: str,
    ) -> _CommunityMutationRecord | None:
        return next((row for row in rows if row.mutation_id == mutation_id), None)

    @staticmethod
    def _matches_mutation(
        record: _CommunityMutationRecord,
        operation: str,
        fingerprint: str,
    ) -> bool:
        return record.operation == operation and secrets.compare_digest(
            record.fingerprint,
            fingerprint,
        )

    @staticmethod
    def _rollback_writes(
        writes: list[tuple[Any, list[BaseModel], list[BaseModel]]],
        data_dir: Path,
    ) -> None:
        attempted: list[tuple[Any, list[BaseModel]]] = []
        try:
            for saver, new_rows, original_rows in writes:
                attempted.append((saver, original_rows))
                saver(new_rows, data_dir)
        except Exception as error:
            rollback_errors: list[Exception] = []
            for saver, original_rows in reversed(attempted):
                try:
                    saver(original_rows, data_dir)
                except Exception as rollback_error:
                    rollback_errors.append(rollback_error)
            if rollback_errors:
                raise CommunityRepositoryError(
                    "本機公開社群交易失敗，且回滾未完整完成。"
                ) from rollback_errors[0]
            raise CommunityRepositoryError("本機公開社群交易未能一起保存。") from error

    def _mutation_write(
        self,
        new_rows: list[_CommunityMutationRecord],
        original_rows: list[_CommunityMutationRecord],
    ) -> tuple[Any, list[BaseModel], list[BaseModel]]:
        def save_rows(rows: list[BaseModel], _: Path) -> int:
            return self._save_mutations(
                [_CommunityMutationRecord.model_validate(row) for row in rows]
            )

        return save_rows, list(new_rows), list(original_rows)

    def list_identities(self) -> list[AnonymousIdentity]:
        return load_anonymous_identities(self.data_dir)

    def find_identity_by_id(self, identity_id: str) -> AnonymousIdentity | None:
        return next((row for row in self.list_identities() if row.id == identity_id), None)

    def find_identity_by_account(self, account_id: str) -> AnonymousIdentity | None:
        return next(
            (row for row in self.list_identities() if row.account_id == account_id),
            None,
        )

    def commit_identity(
        self,
        request: CommunityIdentityMutationRequest,
        *,
        now: datetime | None = None,
    ) -> CommunityIdentityMutationResult:
        current = self._normalize_now(now)
        operation = "identity"
        fingerprint = community_mutation_fingerprint(operation, request)
        with self._locked_all():
            mutations = self._load_mutations()
            existing_mutation = self._find_mutation(mutations, request.mutation_id)
            if existing_mutation is not None:
                if not self._matches_mutation(
                    existing_mutation, operation, fingerprint
                ):
                    return CommunityIdentityMutationResult(
                        status=CommunityIdentityMutationStatus.IDEMPOTENCY_CONFLICT
                    )
                try:
                    return CommunityIdentityMutationResult(
                        status=CommunityIdentityMutationStatus.COMMITTED,
                        identity=AnonymousIdentity.model_validate(
                            existing_mutation.result["identity"]
                        ),
                    )
                except (KeyError, TypeError, ValueError) as error:
                    raise CommunityRepositoryError(
                        "本機社群身分 mutation 紀錄已損毀。"
                    ) from error

            identities = load_anonymous_identities(self.data_dir)
            accounts = load_user_accounts(self.data_dir)
            candidate = request.identity
            token_conflict = next(
                (
                    row
                    for row in identities
                    if row.id != candidate.id
                    and secrets.compare_digest(
                        row.access_token_hash.casefold(),
                        candidate.access_token_hash.casefold(),
                    )
                ),
                None,
            )
            if token_conflict is not None:
                return CommunityIdentityMutationResult(
                    status=CommunityIdentityMutationStatus.IDENTITY_CONFLICT
                )
            if candidate.account_id is not None:
                account = next(
                    (row for row in accounts if row.id == candidate.account_id),
                    None,
                )
                if account is None:
                    return CommunityIdentityMutationResult(
                        status=CommunityIdentityMutationStatus.ACCOUNT_MISSING
                    )
                linked = next(
                    (
                        row
                        for row in identities
                        if row.account_id == candidate.account_id
                    ),
                    None,
                )
                id_conflict = next(
                    (
                        row
                        for row in identities
                        if row.id == candidate.id
                        and row.account_id != candidate.account_id
                    ),
                    None,
                )
                if id_conflict is not None:
                    return CommunityIdentityMutationResult(
                        status=CommunityIdentityMutationStatus.IDENTITY_CONFLICT
                    )
                persisted = (
                    linked.model_copy(
                        update={
                            "display_name": account.display_name,
                            "access_token_hash": candidate.access_token_hash.casefold(),
                        }
                    )
                    if linked is not None
                    else candidate.model_copy(
                        update={
                            "display_name": account.display_name,
                            "access_token_hash": candidate.access_token_hash.casefold(),
                            "created_at": current,
                        }
                    )
                )
                updated_identities = [
                    persisted if row.id == persisted.id else row for row in identities
                ]
                if linked is None:
                    updated_identities.append(persisted)
            else:
                legacy = next(
                    (row for row in identities if row.id == candidate.id),
                    None,
                )
                if legacy is not None and legacy.account_id is not None:
                    return CommunityIdentityMutationResult(
                        status=CommunityIdentityMutationStatus.IDENTITY_CONFLICT
                    )
                persisted = (
                    legacy.model_copy(
                        update={
                            "display_name": candidate.display_name.strip(),
                            "access_token_hash": candidate.access_token_hash.casefold(),
                        }
                    )
                    if legacy is not None
                    else candidate.model_copy(
                        update={
                            "display_name": candidate.display_name.strip(),
                            "access_token_hash": candidate.access_token_hash.casefold(),
                            "created_at": current,
                        }
                    )
                )
                updated_identities = [
                    persisted if row.id == persisted.id else row
                    for row in identities
                ]
                if legacy is None:
                    updated_identities.append(persisted)

            record = _CommunityMutationRecord(
                mutation_id=request.mutation_id,
                operation=operation,
                fingerprint=fingerprint,
                result={"identity": persisted.model_dump(mode="json")},
                created_at=current,
            )
            writes = [
                (
                    save_anonymous_identities,
                    list(updated_identities),
                    list(identities),
                ),
                self._mutation_write([*mutations, record], mutations),
            ]
            self._rollback_writes(writes, self.data_dir)
        return CommunityIdentityMutationResult(
            status=CommunityIdentityMutationStatus.COMMITTED,
            identity=persisted,
        )

    @staticmethod
    def _account_and_identity_status(
        accounts: list[UserAccount],
        identities: list[AnonymousIdentity],
        *,
        account_id: str,
        identity_id: str,
        access_token_hash: str,
        now: datetime,
    ) -> tuple[
        PublicCommunityPublicationStatus | None,
        UserAccount | None,
        AnonymousIdentity | None,
    ]:
        account = next((row for row in accounts if row.id == account_id), None)
        if account is None:
            return PublicCommunityPublicationStatus.ACCOUNT_MISSING, None, None
        identity = next((row for row in identities if row.id == identity_id), None)
        if identity is None:
            return PublicCommunityPublicationStatus.IDENTITY_MISSING, account, None
        if identity.account_id != account.id or not secrets.compare_digest(
            identity.access_token_hash.casefold(), access_token_hash.casefold()
        ):
            return (
                PublicCommunityPublicationStatus.IDENTITY_CONFLICT,
                account,
                identity,
            )
        if (
            account.community_suspended_until is not None
            and account.community_suspended_until > now
        ):
            return (
                PublicCommunityPublicationStatus.ACCOUNT_SUSPENDED,
                account,
                identity,
            )
        return None, account, identity

    @staticmethod
    def _display_name_status(
        account: UserAccount,
        mode: CommunityIdentityMode,
    ) -> tuple[PublicCommunityPublicationStatus | None, str | None]:
        if mode == CommunityIdentityMode.ANONYMOUS:
            return None, "匿名學生"
        if mode == CommunityIdentityMode.REAL_NAME:
            return None, account.display_name
        school = catalog_home_university(account)
        if not school:
            return PublicCommunityPublicationStatus.STUDENT_VERIFICATION_REQUIRED, None
        if mode == CommunityIdentityMode.VERIFIED_SCHOOL:
            return None, f"{school}學生"
        if not account.verified_department:
            return PublicCommunityPublicationStatus.STUDENT_VERIFICATION_REQUIRED, None
        return None, f"{school} {account.verified_department}"

    @staticmethod
    def _verified_for_school(account: UserAccount, school_name: str) -> bool:
        if is_platform_admin(account):
            return True
        own_school = catalog_home_university(account)
        return bool(own_school and _school_key(own_school) == _school_key(school_name))

    def _prepare_content(
        self,
        request: PublicCommunityPublicationRequest,
        account: UserAccount,
        identity: AnonymousIdentity,
        now: datetime,
    ) -> tuple[PublicCommunityPublicationStatus | None, PublicCommunityContent | None]:
        content = _content_from_payload(request.resource_type, request.content)
        mode = content.identity_mode
        display_status, display_name = self._display_name_status(account, mode)
        if display_status is not None or display_name is None:
            return display_status, None

        parent_question: CommunityQuestion | None = None
        parent_post: CommunityPost | None = None
        if request.resource_type == PublicCommunityResourceType.ANSWER:
            assert isinstance(content, CommunityAnswer)
            parent_question = next(
                (
                    row
                    for row in load_community_questions(self.data_dir)
                    if row.id == content.question_id
                ),
                None,
            )
            if parent_question is None:
                return PublicCommunityPublicationStatus.PARENT_MISSING, None
        elif request.resource_type == PublicCommunityResourceType.COMMENT:
            assert isinstance(content, CommunityPostComment)
            parent_post = next(
                (
                    row
                    for row in load_community_posts(self.data_dir)
                    if row.id == content.post_id
                ),
                None,
            )
            if parent_post is None:
                return PublicCommunityPublicationStatus.PARENT_MISSING, None
            if parent_post.status != ModerationStatus.APPROVED:
                return PublicCommunityPublicationStatus.PARENT_MISSING, None
            if content.parent_id:
                parent_comment = next((row for row in load_community_post_comments(self.data_dir)
                                       if row.id == content.parent_id and row.post_id == content.post_id
                                       and row.status == ModerationStatus.APPROVED and row.parent_id is None), None)
                if parent_comment is None:
                    return PublicCommunityPublicationStatus.PARENT_MISSING, None

        allowed = True
        if isinstance(content, CommunityPost):
            if not account.email_verified:
                return PublicCommunityPublicationStatus.EMAIL_UNVERIFIED, None
            if content.board_kind in {
                CommunityBoardKind.UNIVERSITY_EXCHANGE,
                CommunityBoardKind.PUBLIC_STUDY_ABROAD,
                CommunityBoardKind.PUBLIC_TOPIC,
            }:
                # School boards are open to any account with a verified e-mail; only a
                # school-named byline needs a verified student (see _display_name_status).
                allowed = True
            elif content.school_name not in PUBLIC_BOARD_NAMES:
                allowed = self._verified_for_school(account, content.school_name)
        elif isinstance(content, CommunityPostComment):
            assert parent_post is not None
            if not account.email_verified:
                return PublicCommunityPublicationStatus.EMAIL_UNVERIFIED, None
        elif isinstance(content, CommunityQuestion):
            allowed = self._verified_for_school(account, content.home_university)
        elif isinstance(content, CommunityAnswer):
            assert parent_question is not None
            allowed = self._verified_for_school(
                account, parent_question.home_university
            )
        elif isinstance(content, PublicChatMessage):
            allowed = bool(catalog_home_university(account))
        elif isinstance(content, ExperienceSubmission):
            allowed = self._verified_for_school(account, content.home_university)
        if not allowed:
            return PublicCommunityPublicationStatus.BOARD_FORBIDDEN, None

        updates: dict[str, Any] = {
            "author_id": identity.id,
            "display_name": display_name,
            "created_at": now,
        }
        if isinstance(content, CommunityPost):
            updates.update({"comment_count": 0, "viewer_can_delete": False})
        elif isinstance(content, CommunityPostComment):
            updates["viewer_can_delete"] = False
        elif isinstance(content, CommunityQuestion):
            updates["answer_count"] = 0
        return None, content.model_copy(update=updates)

    def _load_content(
        self, resource_type: PublicCommunityResourceType
    ) -> list[PublicCommunityContent]:
        if resource_type == PublicCommunityResourceType.QUESTION:
            return list(load_community_questions(self.data_dir))
        if resource_type == PublicCommunityResourceType.ANSWER:
            return list(load_community_answers(self.data_dir))
        if resource_type == PublicCommunityResourceType.POST:
            return list(load_community_posts(self.data_dir))
        if resource_type == PublicCommunityResourceType.COMMENT:
            return list(load_community_post_comments(self.data_dir))
        if resource_type == PublicCommunityResourceType.CHAT:
            return list(load_public_chat_messages(self.data_dir))
        return list(load_experience_submissions(self.data_dir))

    def _save_content(
        self,
        resource_type: PublicCommunityResourceType,
        rows: list[BaseModel],
        data_dir: Path,
    ) -> int:
        if resource_type == PublicCommunityResourceType.QUESTION:
            return save_community_questions(
                [CommunityQuestion.model_validate(row) for row in rows], data_dir
            )
        if resource_type == PublicCommunityResourceType.ANSWER:
            return save_community_answers(
                [CommunityAnswer.model_validate(row) for row in rows], data_dir
            )
        if resource_type == PublicCommunityResourceType.POST:
            return save_community_posts(
                [CommunityPost.model_validate(row) for row in rows], data_dir
            )
        if resource_type == PublicCommunityResourceType.COMMENT:
            return save_community_post_comments(
                [CommunityPostComment.model_validate(row) for row in rows], data_dir
            )
        if resource_type == PublicCommunityResourceType.CHAT:
            return save_public_chat_messages(
                [PublicChatMessage.model_validate(row) for row in rows], data_dir
            )
        return save_experience_submissions(
            [ExperienceSubmission.model_validate(row) for row in rows], data_dir
        )

    def _content_write(
        self,
        resource_type: PublicCommunityResourceType,
        new_rows: list[PublicCommunityContent],
        original_rows: list[PublicCommunityContent],
    ) -> tuple[Any, list[BaseModel], list[BaseModel]]:
        def save_rows(rows: list[BaseModel], data_dir: Path) -> int:
            return self._save_content(resource_type, rows, data_dir)

        return save_rows, list(new_rows), list(original_rows)

    def commit_publication(
        self,
        request: PublicCommunityPublicationRequest,
        *,
        now: datetime | None = None,
    ) -> PublicCommunityPublicationResult:
        current = self._normalize_now(now)
        operation = "publication"
        fingerprint = public_community_publication_fingerprint(request)
        with self._locked_all():
            mutations = self._load_mutations()
            existing_mutation = self._find_mutation(mutations, request.mutation_id)
            if existing_mutation is not None:
                if not self._matches_mutation(
                    existing_mutation, operation, fingerprint
                ):
                    return PublicCommunityPublicationResult(
                        status=PublicCommunityPublicationStatus.IDEMPOTENCY_CONFLICT
                    )
                return PublicCommunityPublicationResult.model_validate(
                    existing_mutation.result
                )

            accounts = load_user_accounts(self.data_dir)
            identities = load_anonymous_identities(self.data_dir)
            actor_status, account, identity = self._account_and_identity_status(
                accounts,
                identities,
                account_id=request.account_id,
                identity_id=request.identity_id,
                access_token_hash=request.access_token_hash,
                now=current,
            )
            if actor_status is not None or account is None or identity is None:
                return PublicCommunityPublicationResult(
                    status=actor_status
                    or PublicCommunityPublicationStatus.INTEGRITY_CONFLICT
                )

            content_status, persisted = self._prepare_content(
                request, account, identity, current
            )
            if content_status is not None or persisted is None:
                return PublicCommunityPublicationResult(
                    status=content_status
                    or PublicCommunityPublicationStatus.INTEGRITY_CONFLICT
                )

            content_rows = self._load_content(request.resource_type)
            if any(row.id == persisted.id for row in content_rows):
                return PublicCommunityPublicationResult(
                    status=PublicCommunityPublicationStatus.INTEGRITY_CONFLICT
                )

            window_start = current - PUBLIC_RATE_WINDOW
            all_events = load_community_publish_events(self.data_dir)
            recent_events = [
                event for event in all_events if event.created_at >= window_start
            ]
            account_events = [
                event for event in recent_events if event.account_id == account.id
            ]
            limit = (
                NEW_ACCOUNT_PUBLICATION_LIMIT
                if not is_platform_admin(account) and account.created_at >= current - NEW_ACCOUNT_WINDOW
                else ESTABLISHED_ACCOUNT_PUBLICATION_LIMIT
            )
            if len(account_events) >= limit:
                return PublicCommunityPublicationResult(
                    status=PublicCommunityPublicationStatus.RATE_LIMITED,
                    retry_after_seconds=int(PUBLIC_RATE_WINDOW.total_seconds()),
                )

            event = CommunityPublishEvent(
                id=request.mutation_id,
                account_id=account.id,
                created_at=current,
            )
            result = PublicCommunityPublicationResult(
                status=PublicCommunityPublicationStatus.COMMITTED,
                content=_content_result_payload(request.resource_type, persisted),
            )
            record = _CommunityMutationRecord(
                mutation_id=request.mutation_id,
                operation=operation,
                fingerprint=fingerprint,
                result=result.model_dump(mode="json"),
                created_at=current,
            )
            writes = [
                self._content_write(
                    request.resource_type,
                    [*content_rows, persisted],
                    content_rows,
                ),
                (
                    save_community_publish_events,
                    list([*recent_events, event]),
                    list(all_events),
                ),
                self._mutation_write([*mutations, record], mutations),
            ]
            self._rollback_writes(writes, self.data_dir)
        return result

    def list_private_conversations(self) -> list[PrivateConversation]:
        return load_private_conversations(self.data_dir)

    def list_private_messages(self) -> list[PrivateMessage]:
        return load_private_messages(self.data_dir)

    def list_blocks(self) -> list[CommunityBlock]:
        return load_community_blocks(self.data_dir)

    def list_reports(self, *, now: datetime | None = None) -> list[CommunityReport]:
        current = self._normalize_now(now)
        with self._locked_all():
            reports = load_community_reports(self.data_dir)
            retained = [
                row
                for row in reports
                if row.retained_until is None or row.retained_until > current
            ]
            if retained != reports:
                save_community_reports(retained, self.data_dir)
            return retained

    @staticmethod
    def _private_actor_status(
        accounts: list[UserAccount],
        identities: list[AnonymousIdentity],
        request: PrivateCommunityActorRequest,
        now: datetime,
    ) -> tuple[
        PrivateCommunityMutationStatus | None,
        UserAccount | None,
        AnonymousIdentity | None,
    ]:
        public_status, account, identity = JsonlCommunityRepository._account_and_identity_status(
            accounts,
            identities,
            account_id=request.account_id,
            identity_id=request.identity_id,
            access_token_hash=request.access_token_hash,
            now=now,
        )
        status_map = {
            PublicCommunityPublicationStatus.ACCOUNT_MISSING: PrivateCommunityMutationStatus.ACCOUNT_MISSING,
            PublicCommunityPublicationStatus.IDENTITY_MISSING: PrivateCommunityMutationStatus.IDENTITY_MISSING,
            PublicCommunityPublicationStatus.IDENTITY_CONFLICT: PrivateCommunityMutationStatus.IDENTITY_CONFLICT,
            PublicCommunityPublicationStatus.ACCOUNT_SUSPENDED: PrivateCommunityMutationStatus.ACCOUNT_SUSPENDED,
        }
        return status_map.get(public_status), account, identity

    @staticmethod
    def _blocked_between(
        blocks: list[CommunityBlock], left_id: str, right_id: str
    ) -> bool:
        return any(
            {row.owner_id, row.target_id} == {left_id, right_id}
            for row in blocks
        )

    def _private_replay(
        self,
        mutations: list[_CommunityMutationRecord],
        mutation_id: str,
        operation: str,
        fingerprint: str,
    ) -> PrivateCommunityMutationResult | None:
        record = self._find_mutation(mutations, mutation_id)
        if record is None:
            return None
        if not self._matches_mutation(record, operation, fingerprint):
            return PrivateCommunityMutationResult(
                status=PrivateCommunityMutationStatus.IDEMPOTENCY_CONFLICT
            )
        return PrivateCommunityMutationResult.model_validate(record.result)

    def _commit_private_result(
        self,
        *,
        request: BaseModel,
        operation: str,
        result: PrivateCommunityMutationResult,
        current: datetime,
        mutations: list[_CommunityMutationRecord],
        writes: list[tuple[Any, list[BaseModel], list[BaseModel]]],
    ) -> PrivateCommunityMutationResult:
        record = _CommunityMutationRecord(
            mutation_id=str(request.mutation_id),
            operation=operation,
            fingerprint=private_community_mutation_fingerprint(operation, request),
            result=result.model_dump(mode="json"),
            created_at=current,
        )
        writes.append(self._mutation_write([*mutations, record], mutations))
        self._rollback_writes(writes, self.data_dir)
        return result

    def commit_private_conversation(
        self,
        request: PrivateConversationMutationRequest,
        *,
        now: datetime | None = None,
    ) -> PrivateCommunityMutationResult:
        current = self._normalize_now(now)
        operation = "private_conversation"
        fingerprint = private_community_mutation_fingerprint(operation, request)
        with self._locked_all():
            mutations = self._load_mutations()
            replay = self._private_replay(
                mutations, request.mutation_id, operation, fingerprint
            )
            if replay is not None:
                return replay
            accounts = load_user_accounts(self.data_dir)
            identities = load_anonymous_identities(self.data_dir)
            actor_status, _, sender = self._private_actor_status(
                accounts, identities, request, current
            )
            if actor_status is not None or sender is None:
                return PrivateCommunityMutationResult(status=actor_status)
            recipient = next(
                (
                    row
                    for row in identities
                    if row.id == request.recipient_identity_id and row.account_id
                ),
                None,
            )
            if recipient is None:
                return PrivateCommunityMutationResult(
                    status=PrivateCommunityMutationStatus.RECIPIENT_MISSING
                )
            if recipient.id == sender.id:
                return PrivateCommunityMutationResult(
                    status=PrivateCommunityMutationStatus.SELF_TARGET
                )
            blocks = load_community_blocks(self.data_dir)
            if self._blocked_between(blocks, sender.id, recipient.id):
                return PrivateCommunityMutationResult(
                    status=PrivateCommunityMutationStatus.BLOCKED
                )
            conversations = load_private_conversations(self.data_dir)
            messages = load_private_messages(self.data_dir)
            conversation = request.conversation.model_copy(
                update={
                    "sender_name": sender.display_name,
                    "recipient_name": recipient.display_name,
                    "created_at": current,
                    "updated_at": current,
                }
            )
            message = request.initial_message.model_copy(
                update={"display_name": sender.display_name, "created_at": current}
            )
            result = PrivateCommunityMutationResult(
                status=PrivateCommunityMutationStatus.COMMITTED,
                conversation=conversation,
                message=message,
            )
            return self._commit_private_result(
                request=request,
                operation=operation,
                result=result,
                current=current,
                mutations=mutations,
                writes=[
                    (
                        save_private_conversations,
                        [*conversations, conversation],
                        conversations,
                    ),
                    (save_private_messages, [*messages, message], messages),
                ],
            )

    def purge_private_identity(
        self,
        request: PrivateCommunityIdentityPurgeRequest,
        *,
        now: datetime | None = None,
    ) -> PrivateCommunityMutationResult:
        current = self._normalize_now(now)
        operation = "purge_private_identity"
        fingerprint = private_community_mutation_fingerprint(operation, request)
        with self._locked_all():
            mutations = self._load_mutations()
            replay = self._private_replay(
                mutations, request.mutation_id, operation, fingerprint
            )
            if replay is not None:
                return replay
            identities = load_anonymous_identities(self.data_dir)
            identity = next(
                (row for row in identities if row.id == request.identity_id), None
            )
            if identity is None:
                return PrivateCommunityMutationResult(
                    status=PrivateCommunityMutationStatus.IDENTITY_MISSING
                )
            if identity.account_id != request.expected_account_id:
                return PrivateCommunityMutationResult(
                    status=PrivateCommunityMutationStatus.IDENTITY_CONFLICT
                )
            conversations = load_private_conversations(self.data_dir)
            removed_conversation_ids = {
                row.id
                for row in conversations
                if request.identity_id in {row.sender_id, row.recipient_id}
            }
            retained_conversations = [
                row for row in conversations if row.id not in removed_conversation_ids
            ]
            messages = load_private_messages(self.data_dir)
            retained_messages = [
                row
                for row in messages
                if row.conversation_id not in removed_conversation_ids
            ]
            blocks = load_community_blocks(self.data_dir)
            retained_blocks = [
                row
                for row in blocks
                if request.identity_id not in {row.owner_id, row.target_id}
            ]
            reports = load_community_reports(self.data_dir)
            report_retention_deadline = current + timedelta(
                days=request.pending_report_retention_days
            )
            retained_reports: list[CommunityReport] = []
            deidentified_reports = 0
            deleted_reports = 0
            cleared_reviews = 0
            for row in reports:
                if row.reporter_id == request.identity_id:
                    if row.status == CommunityReportStatus.PENDING:
                        row = row.model_copy(
                            update={
                                "reporter_id": "",
                                "retained_until": report_retention_deadline,
                            }
                        )
                        retained_reports.append(row)
                        deidentified_reports += 1
                    else:
                        deleted_reports += 1
                    continue
                if row.reviewed_by == request.expected_account_id:
                    row = row.model_copy(update={"reviewed_by": None})
                    cleared_reviews += 1
                retained_reports.append(row)
            result = PrivateCommunityMutationResult(
                status=PrivateCommunityMutationStatus.COMMITTED,
                counts={
                    "conversation": len(conversations) - len(retained_conversations),
                    "message": len(messages) - len(retained_messages),
                    "block": len(blocks) - len(retained_blocks),
                    "report_deidentified": deidentified_reports,
                    "report_deleted": deleted_reports,
                    "report_review_cleared": cleared_reviews,
                },
            )
            return self._commit_private_result(
                request=request,
                operation=operation,
                result=result,
                current=current,
                mutations=mutations,
                writes=[
                    (
                        save_private_conversations,
                        retained_conversations,
                        conversations,
                    ),
                    (save_private_messages, retained_messages, messages),
                    (save_community_blocks, retained_blocks, blocks),
                    (save_community_reports, retained_reports, reports),
                ],
            )

    def commit_private_conversation_status(
        self,
        request: PrivateConversationStatusMutationRequest,
        *,
        now: datetime | None = None,
    ) -> PrivateCommunityMutationResult:
        current = self._normalize_now(now)
        operation = "private_conversation_status"
        fingerprint = private_community_mutation_fingerprint(operation, request)
        with self._locked_all():
            mutations = self._load_mutations()
            replay = self._private_replay(
                mutations, request.mutation_id, operation, fingerprint
            )
            if replay is not None:
                return replay
            accounts = load_user_accounts(self.data_dir)
            identities = load_anonymous_identities(self.data_dir)
            actor_status, _, actor = self._private_actor_status(
                accounts, identities, request, current
            )
            if actor_status is not None or actor is None:
                return PrivateCommunityMutationResult(status=actor_status)
            conversations = load_private_conversations(self.data_dir)
            conversation = next(
                (row for row in conversations if row.id == request.conversation_id), None
            )
            if conversation is None:
                return PrivateCommunityMutationResult(
                    status=PrivateCommunityMutationStatus.CONVERSATION_MISSING
                )
            if actor.id != conversation.recipient_id:
                return PrivateCommunityMutationResult(
                    status=PrivateCommunityMutationStatus.RECIPIENT_ONLY
                )
            if self._blocked_between(
                load_community_blocks(self.data_dir),
                conversation.sender_id,
                conversation.recipient_id,
            ):
                return PrivateCommunityMutationResult(
                    status=PrivateCommunityMutationStatus.BLOCKED
                )
            if conversation.status != request.expected_status:
                return PrivateCommunityMutationResult(
                    status=PrivateCommunityMutationStatus.STATUS_CONFLICT,
                    conversation=conversation,
                )
            updated = conversation.model_copy(
                update={"status": request.status, "updated_at": current}
            )
            result = PrivateCommunityMutationResult(
                status=PrivateCommunityMutationStatus.COMMITTED,
                conversation=updated,
            )
            return self._commit_private_result(
                request=request,
                operation=operation,
                result=result,
                current=current,
                mutations=mutations,
                writes=[
                    (
                        save_private_conversations,
                        [updated if row.id == updated.id else row for row in conversations],
                        conversations,
                    )
                ],
            )

    def commit_private_message(
        self,
        request: PrivateMessageMutationRequest,
        *,
        now: datetime | None = None,
    ) -> PrivateCommunityMutationResult:
        current = self._normalize_now(now)
        operation = "private_message"
        fingerprint = private_community_mutation_fingerprint(operation, request)
        with self._locked_all():
            mutations = self._load_mutations()
            replay = self._private_replay(
                mutations, request.mutation_id, operation, fingerprint
            )
            if replay is not None:
                return replay
            accounts = load_user_accounts(self.data_dir)
            identities = load_anonymous_identities(self.data_dir)
            actor_status, _, actor = self._private_actor_status(
                accounts, identities, request, current
            )
            if actor_status is not None or actor is None:
                return PrivateCommunityMutationResult(status=actor_status)
            conversations = load_private_conversations(self.data_dir)
            conversation = next(
                (
                    row
                    for row in conversations
                    if row.id == request.message.conversation_id
                ),
                None,
            )
            if conversation is None:
                return PrivateCommunityMutationResult(
                    status=PrivateCommunityMutationStatus.CONVERSATION_MISSING
                )
            if actor.id not in {conversation.sender_id, conversation.recipient_id}:
                return PrivateCommunityMutationResult(
                    status=PrivateCommunityMutationStatus.NOT_PARTICIPANT
                )
            if conversation.status != ConversationStatus.ACCEPTED:
                return PrivateCommunityMutationResult(
                    status=PrivateCommunityMutationStatus.STATUS_CONFLICT,
                    conversation=conversation,
                )
            if self._blocked_between(
                load_community_blocks(self.data_dir),
                conversation.sender_id,
                conversation.recipient_id,
            ):
                return PrivateCommunityMutationResult(
                    status=PrivateCommunityMutationStatus.BLOCKED
                )
            message = request.message.model_copy(
                update={"display_name": actor.display_name, "created_at": current}
            )
            updated = conversation.model_copy(update={"updated_at": current})
            messages = load_private_messages(self.data_dir)
            result = PrivateCommunityMutationResult(
                status=PrivateCommunityMutationStatus.COMMITTED,
                conversation=updated,
                message=message,
            )
            return self._commit_private_result(
                request=request,
                operation=operation,
                result=result,
                current=current,
                mutations=mutations,
                writes=[
                    (
                        save_private_conversations,
                        [updated if row.id == updated.id else row for row in conversations],
                        conversations,
                    ),
                    (save_private_messages, [*messages, message], messages),
                ],
            )

    def commit_block(
        self,
        request: CommunityBlockMutationRequest,
        *,
        now: datetime | None = None,
    ) -> PrivateCommunityMutationResult:
        current = self._normalize_now(now)
        operation = "community_block"
        fingerprint = private_community_mutation_fingerprint(operation, request)
        with self._locked_all():
            mutations = self._load_mutations()
            replay = self._private_replay(
                mutations, request.mutation_id, operation, fingerprint
            )
            if replay is not None:
                return replay
            accounts = load_user_accounts(self.data_dir)
            identities = load_anonymous_identities(self.data_dir)
            actor_status, _, actor = self._private_actor_status(
                accounts, identities, request, current
            )
            if actor_status is not None or actor is None:
                return PrivateCommunityMutationResult(status=actor_status)
            target = next(
                (
                    row
                    for row in identities
                    if row.id == request.block.target_id and row.account_id
                ),
                None,
            )
            if target is None:
                return PrivateCommunityMutationResult(
                    status=PrivateCommunityMutationStatus.RECIPIENT_MISSING
                )
            if target.id == actor.id:
                return PrivateCommunityMutationResult(
                    status=PrivateCommunityMutationStatus.SELF_TARGET
                )
            conversations = load_private_conversations(self.data_dir)
            if not any(
                {row.sender_id, row.recipient_id} == {actor.id, target.id}
                for row in conversations
            ):
                return PrivateCommunityMutationResult(
                    status=PrivateCommunityMutationStatus.CONVERSATION_REQUIRED
                )
            blocks = load_community_blocks(self.data_dir)
            existing = next(
                (
                    row
                    for row in blocks
                    if row.owner_id == actor.id and row.target_id == target.id
                ),
                None,
            )
            block = existing or request.block.model_copy(update={"created_at": current})
            result = PrivateCommunityMutationResult(
                status=PrivateCommunityMutationStatus.COMMITTED, block=block
            )
            writes: list[tuple[Any, list[BaseModel], list[BaseModel]]] = []
            if existing is None:
                writes.append((save_community_blocks, [*blocks, block], blocks))
            return self._commit_private_result(
                request=request,
                operation=operation,
                result=result,
                current=current,
                mutations=mutations,
                writes=writes,
            )

    def _report_author_id(
        self, resource_type: str, resource_id: str, reporter_id: str
    ) -> str | None:
        public_types = {
            "post": (PublicCommunityResourceType.POST, load_community_posts),
            "comment": (
                PublicCommunityResourceType.COMMENT,
                load_community_post_comments,
            ),
            "chat": (PublicCommunityResourceType.CHAT, load_public_chat_messages),
        }
        if resource_type in public_types:
            _, loader = public_types[resource_type]
            resource = next(
                (row for row in loader(self.data_dir) if row.id == resource_id), None
            )
            return None if resource is None else resource.author_id
        message = next(
            (
                row
                for row in load_private_messages(self.data_dir)
                if row.id == resource_id
            ),
            None,
        )
        if message is None:
            return None
        conversation = next(
            (
                row
                for row in load_private_conversations(self.data_dir)
                if row.id == message.conversation_id
            ),
            None,
        )
        if conversation is None or reporter_id not in {
            conversation.sender_id,
            conversation.recipient_id,
        }:
            return None
        return message.author_id

    def commit_report(
        self,
        request: CommunityReportMutationRequest,
        *,
        now: datetime | None = None,
    ) -> PrivateCommunityMutationResult:
        current = self._normalize_now(now)
        operation = "community_report"
        fingerprint = private_community_mutation_fingerprint(operation, request)
        with self._locked_all():
            mutations = self._load_mutations()
            replay = self._private_replay(
                mutations, request.mutation_id, operation, fingerprint
            )
            if replay is not None:
                return replay
            accounts = load_user_accounts(self.data_dir)
            identities = load_anonymous_identities(self.data_dir)
            actor_status, _, actor = self._private_actor_status(
                accounts, identities, request, current
            )
            if actor_status is not None or actor is None:
                return PrivateCommunityMutationResult(status=actor_status)
            author_id = self._report_author_id(
                request.report.resource_type,
                request.report.resource_id,
                actor.id,
            )
            if author_id is None:
                return PrivateCommunityMutationResult(
                    status=PrivateCommunityMutationStatus.RESOURCE_MISSING
                )
            if author_id == actor.id:
                return PrivateCommunityMutationResult(
                    status=PrivateCommunityMutationStatus.SELF_REPORT
                )
            reports = [
                row
                for row in load_community_reports(self.data_dir)
                if row.retained_until is None or row.retained_until > current
            ]
            existing = next(
                (
                    row
                    for row in reports
                    if row.reporter_id == actor.id
                    and row.resource_type == request.report.resource_type
                    and row.resource_id == request.report.resource_id
                    and row.status == CommunityReportStatus.PENDING
                ),
                None,
            )
            report = existing or request.report.model_copy(update={"created_at": current})
            result = PrivateCommunityMutationResult(
                status=PrivateCommunityMutationStatus.COMMITTED, report=report
            )
            persisted = reports if existing is not None else [*reports, report]
            return self._commit_private_result(
                request=request,
                operation=operation,
                result=result,
                current=current,
                mutations=mutations,
                writes=[(save_community_reports, persisted, load_community_reports(self.data_dir))],
            )

    def commit_report_review(
        self,
        request: CommunityReportReviewMutationRequest,
        *,
        now: datetime | None = None,
    ) -> PrivateCommunityMutationResult:
        current = self._normalize_now(now)
        operation = "community_report_review"
        fingerprint = private_community_mutation_fingerprint(operation, request)
        with self._locked_all():
            mutations = self._load_mutations()
            replay = self._private_replay(
                mutations, request.mutation_id, operation, fingerprint
            )
            if replay is not None:
                return replay
            if not any(
                row.id == request.moderator_id
                for row in load_user_accounts(self.data_dir)
            ):
                return PrivateCommunityMutationResult(
                    status=PrivateCommunityMutationStatus.ACCOUNT_MISSING
                )
            reports = load_community_reports(self.data_dir)
            report = next((row for row in reports if row.id == request.report_id), None)
            if report is None:
                return PrivateCommunityMutationResult(
                    status=PrivateCommunityMutationStatus.REPORT_MISSING
                )
            if report.status != request.expected_status:
                return PrivateCommunityMutationResult(
                    status=PrivateCommunityMutationStatus.STATUS_CONFLICT,
                    report=report,
                )
            updated = report.model_copy(
                update={
                    "status": request.status,
                    "reviewed_by": request.moderator_id,
                    "reviewed_at": current,
                    "resolution_note": request.note,
                }
            )
            audit = CommunityModerationAudit(
                resource_type="report",
                resource_id=report.id,
                previous_status=report.status.value,
                new_status=request.status.value,
                moderator_id=request.moderator_id,
                note=request.note,
                created_at=current,
            )
            audits = load_community_moderation_audits(self.data_dir)
            updated_reports = [
                updated if row.id == updated.id else row for row in reports
            ]
            if not updated.reporter_id:
                updated_reports = [row for row in updated_reports if row.id != updated.id]
            result = PrivateCommunityMutationResult(
                status=PrivateCommunityMutationStatus.COMMITTED,
                report=updated,
                audit=audit,
            )
            return self._commit_private_result(
                request=request,
                operation=operation,
                result=result,
                current=current,
                mutations=mutations,
                writes=[
                    (save_community_reports, updated_reports, reports),
                    (save_community_moderation_audits, [*audits, audit], audits),
                ],
            )

    def list_questions(self) -> list[CommunityQuestion]:
        return load_community_questions(self.data_dir)

    def list_answers(self) -> list[CommunityAnswer]:
        return load_community_answers(self.data_dir)

    def list_posts(self) -> list[CommunityPost]:
        return load_community_posts(self.data_dir)

    def list_comments(self) -> list[CommunityPostComment]:
        return load_community_post_comments(self.data_dir)

    def list_reactions(self) -> list[CommunityReaction]:
        account_ids = {row.id for row in load_user_accounts(self.data_dir)}
        return [row for row in read_jsonl(self.data_dir / "processed" / "community_reactions.jsonl", CommunityReaction)
                if row.account_id in account_ids]

    def purge_account_interactions(self, account_id):
        with self._locked_all():
            if any(row.id == account_id for row in load_user_accounts(self.data_dir)):
                raise CommunityRepositoryError("帳號仍存在，無法清除刪除帳號的反應紀錄。")
            _save_reactions(self.list_reactions(), self.data_dir)
            rows = read_jsonl(self.data_dir / "processed" / "community_bookmarks.jsonl", CommunityBookmark)
            _save_bookmarks([row for row in rows if row.account_id != account_id], self.data_dir)

    def list_bookmarks(self, account_id):
        return [row.post_id for row in read_jsonl(self.data_dir / "processed" / "community_bookmarks.jsonl", CommunityBookmark)
                if row.account_id == account_id]

    def set_bookmark(self, account_id, post_id, saved):
        with self._locked_all():
            if not any(row.id == account_id for row in load_user_accounts(self.data_dir)):
                return {"status": "forbidden"}
            rows = read_jsonl(self.data_dir / "processed" / "community_bookmarks.jsonl", CommunityBookmark)
            own = {row.post_id for row in rows if row.account_id == account_id}
            if saved:
                if not any(row.id == post_id and row.status == ModerationStatus.APPROVED for row in self.list_posts()):
                    return {"status": "missing"}
                if post_id not in own and len(own) >= 100:
                    return {"status": "limit"}
            rows = [row for row in rows if not (row.account_id == account_id and row.post_id == post_id)]
            if saved:
                rows.append(CommunityBookmark(account_id=account_id, post_id=post_id))
            _save_bookmarks(rows, self.data_dir)
            return {"status": "committed", "saved": saved}

    def set_reaction(self, account_id, resource_type, resource_id, reaction, *, platform_admin=False):
        with self._locked_all():
            account = next((row for row in load_user_accounts(self.data_dir) if row.id == account_id), None)
            if account is None or not account.email_verified or (account.community_suspended_until and account.community_suspended_until > utc_now()):
                return {"status": "forbidden"}
            posts = self.list_posts()
            comments = self.list_comments()
            target = next((row for row in (posts if resource_type == "post" else comments) if row.id == resource_id and row.status == ModerationStatus.APPROVED), None)
            if target is None or getattr(target, "deleted", False):
                return {"status": "missing"}
            post = target if resource_type == "post" else next((row for row in posts if row.id == target.post_id and row.status == ModerationStatus.APPROVED), None)
            if post is None:
                return {"status": "missing"}
            if resource_type == "comment" and target.parent_id:
                parent = next((row for row in comments if row.id == target.parent_id and row.post_id == target.post_id and row.status == ModerationStatus.APPROVED), None)
                if parent is None:
                    return {"status": "missing"}
            if post.board_kind not in {
                CommunityBoardKind.UNIVERSITY_EXCHANGE,
                CommunityBoardKind.PUBLIC_STUDY_ABROAD,
                CommunityBoardKind.PUBLIC_TOPIC,
            } and post.school_name not in PUBLIC_BOARD_NAMES and not self._verified_for_school(account, post.school_name):
                return {"status": "forbidden"}
            rows = self.list_reactions()
            rows = [row for row in rows if not (row.account_id == account_id and row.resource_type == resource_type and row.resource_id == resource_id)]
            if reaction is not None:
                rows.append(CommunityReaction(account_id=account_id, resource_type=resource_type, resource_id=resource_id, reaction=reaction))
            _save_reactions(rows, self.data_dir)
            return {"status": "committed", **reaction_summary(rows, resource_type, resource_id, account_id)}

    def list_public_chat_messages(self) -> list[PublicChatMessage]:
        return load_public_chat_messages(self.data_dir)

    def list_experience_submissions(self) -> list[ExperienceSubmission]:
        return load_experience_submissions(self.data_dir)

    def _delete_actor_status(
        self,
        request: PublicCommunityDeleteRequest,
        now: datetime,
    ) -> tuple[
        PublicCommunityDeleteStatus | None,
        UserAccount | None,
        AnonymousIdentity | None,
    ]:
        publication_status, account, identity = self._account_and_identity_status(
            load_user_accounts(self.data_dir),
            load_anonymous_identities(self.data_dir),
            account_id=request.account_id,
            identity_id=request.identity_id,
            access_token_hash=request.access_token_hash,
            now=now,
        )
        status_map = {
            PublicCommunityPublicationStatus.ACCOUNT_MISSING: PublicCommunityDeleteStatus.ACCOUNT_MISSING,
            PublicCommunityPublicationStatus.IDENTITY_MISSING: PublicCommunityDeleteStatus.IDENTITY_MISSING,
            PublicCommunityPublicationStatus.IDENTITY_CONFLICT: PublicCommunityDeleteStatus.IDENTITY_CONFLICT,
            PublicCommunityPublicationStatus.ACCOUNT_SUSPENDED: PublicCommunityDeleteStatus.ACCOUNT_SUSPENDED,
        }
        if publication_status in status_map:
            return status_map[publication_status], account, identity
        return None, account, identity

    def delete_public_content(
        self,
        request: PublicCommunityDeleteRequest,
        *,
        now: datetime | None = None,
    ) -> PublicCommunityDeleteResult:
        current = self._normalize_now(now)
        operation = "delete_public_content"
        fingerprint = community_mutation_fingerprint(operation, request)
        with self._locked_all():
            mutations = self._load_mutations()
            existing_mutation = self._find_mutation(mutations, request.mutation_id)
            if existing_mutation is not None:
                if not self._matches_mutation(
                    existing_mutation, operation, fingerprint
                ):
                    return PublicCommunityDeleteResult(
                        status=PublicCommunityDeleteStatus.IDEMPOTENCY_CONFLICT
                    )
                return PublicCommunityDeleteResult.model_validate(
                    existing_mutation.result
                )
            actor_status, _, identity = self._delete_actor_status(request, current)
            if actor_status is not None or identity is None:
                return PublicCommunityDeleteResult(
                    status=actor_status
                    or PublicCommunityDeleteStatus.INTEGRITY_CONFLICT
                )

            posts = load_community_posts(self.data_dir)
            comments = load_community_post_comments(self.data_dir)
            if request.resource_type == PublicCommunityResourceType.POST:
                target = next(
                    (row for row in posts if row.id == request.resource_id), None
                )
            else:
                target = next(
                    (row for row in comments if row.id == request.resource_id), None
                )
            if target is None:
                return PublicCommunityDeleteResult(
                    status=PublicCommunityDeleteStatus.RESOURCE_MISSING
                )
            if target.author_id != identity.id:
                return PublicCommunityDeleteResult(
                    status=PublicCommunityDeleteStatus.NOT_OWNER
                )

            deleted_comment_count = 0
            updated_posts = posts
            updated_comments = comments
            if request.resource_type == PublicCommunityResourceType.POST:
                updated_posts = [row for row in posts if row.id != request.resource_id]
                deleted_comment_count = sum(
                    row.post_id == request.resource_id for row in comments
                )
                updated_comments = [
                    row for row in comments if row.post_id != request.resource_id
                ]
            else:
                updated_comments = [row.model_copy(update={"deleted": True,
                    "status": ModerationStatus.HIDDEN if row.parent_id else row.status, "body": "此留言已刪除",
                    "display_name": "已刪除留言", "author_id": ""})
                    if row.id == request.resource_id else row for row in comments]
            result = PublicCommunityDeleteResult(
                status=PublicCommunityDeleteStatus.COMMITTED,
                resource_id=request.resource_id,
                deleted_comment_count=deleted_comment_count,
            )
            record = _CommunityMutationRecord(
                mutation_id=request.mutation_id,
                operation=operation,
                fingerprint=fingerprint,
                result=result.model_dump(mode="json"),
                created_at=current,
            )
            writes: list[tuple[Any, list[BaseModel], list[BaseModel]]] = []
            if updated_posts != posts:
                writes.append(
                    (save_community_posts, list(updated_posts), list(posts))
                )
            if updated_comments != comments:
                writes.append(
                    (
                        save_community_post_comments,
                        list(updated_comments),
                        list(comments),
                    )
                )
            reactions = self.list_reactions()
            removed_comments = {row.id for row in comments if row.post_id == request.resource_id} if request.resource_type == PublicCommunityResourceType.POST else {request.resource_id}
            retained_reactions = [row for row in reactions if not (
                (request.resource_type == PublicCommunityResourceType.POST and row.resource_type == "post" and row.resource_id == request.resource_id)
                or (row.resource_type == "comment" and row.resource_id in removed_comments))]
            if retained_reactions != reactions:
                writes.append((_save_reactions, retained_reactions, reactions))
            if request.resource_type == PublicCommunityResourceType.POST:
                bookmarks = read_jsonl(self.data_dir / "processed" / "community_bookmarks.jsonl", CommunityBookmark)
                retained_bookmarks = [row for row in bookmarks if row.post_id != request.resource_id]
                if retained_bookmarks != bookmarks:
                    writes.append((_save_bookmarks, retained_bookmarks, bookmarks))
            writes.append(self._mutation_write([*mutations, record], mutations))
            self._rollback_writes(writes, self.data_dir)
        return result

    def list_moderation_queue(self) -> PublicCommunityModerationQueue:
        with self._locked_all():
            return PublicCommunityModerationQueue(
                question=[
                    row
                    for row in load_community_questions(self.data_dir)
                    if row.status == ModerationStatus.PENDING
                ],
                answer=[
                    row
                    for row in load_community_answers(self.data_dir)
                    if row.status == ModerationStatus.PENDING
                ],
                post=[
                    row
                    for row in load_community_posts(self.data_dir)
                    if row.status == ModerationStatus.PENDING
                ],
                comment=[
                    row
                    for row in load_community_post_comments(self.data_dir)
                    if row.status == ModerationStatus.PENDING
                ],
                chat=[
                    row
                    for row in load_public_chat_messages(self.data_dir)
                    if row.status == ModerationStatus.PENDING
                ],
                experience=[
                    row
                    for row in load_experience_submissions(self.data_dir)
                    if row.status == ModerationStatus.PENDING
                ],
            )

    def commit_moderation(
        self,
        request: PublicCommunityModerationRequest,
        *,
        now: datetime | None = None,
    ) -> PublicCommunityModerationResult:
        current = self._normalize_now(now)
        operation = "moderation"
        fingerprint = community_mutation_fingerprint(operation, request)
        with self._locked_all():
            mutations = self._load_mutations()
            existing_mutation = self._find_mutation(mutations, request.mutation_id)
            if existing_mutation is not None:
                if not self._matches_mutation(
                    existing_mutation, operation, fingerprint
                ):
                    return PublicCommunityModerationResult(
                        status=PublicCommunityModerationStatus.IDEMPOTENCY_CONFLICT
                    )
                return PublicCommunityModerationResult.model_validate(
                    existing_mutation.result
                )
            accounts = load_user_accounts(self.data_dir)
            if not any(row.id == request.moderator_id for row in accounts):
                return PublicCommunityModerationResult(
                    status=PublicCommunityModerationStatus.MODERATOR_MISSING
                )
            rows = self._load_content(request.resource_type)
            target = next((row for row in rows if row.id == request.resource_id), None)
            if target is None:
                return PublicCommunityModerationResult(
                    status=PublicCommunityModerationStatus.RESOURCE_MISSING
                )
            if target.status != request.expected_status:
                return PublicCommunityModerationResult(
                    status=PublicCommunityModerationStatus.STATUS_CONFLICT
                )
            if target.status == request.status:
                return PublicCommunityModerationResult(
                    status=PublicCommunityModerationStatus.NO_CHANGE
                )
            updated = target.model_copy(update={"status": request.status})
            updated_rows = [
                updated if row.id == target.id else row for row in rows
            ]
            audits = load_community_moderation_audits(self.data_dir)
            audit = CommunityModerationAudit(
                id=request.mutation_id,
                resource_type=request.resource_type.value,
                resource_id=request.resource_id,
                previous_status=target.status.value,
                new_status=request.status.value,
                moderator_id=request.moderator_id,
                note=request.note,
                created_at=current,
            )
            result = PublicCommunityModerationResult(
                status=PublicCommunityModerationStatus.COMMITTED,
                content=_content_result_payload(request.resource_type, updated),
                audit=audit,
            )
            record = _CommunityMutationRecord(
                mutation_id=request.mutation_id,
                operation=operation,
                fingerprint=fingerprint,
                result=result.model_dump(mode="json"),
                created_at=current,
            )
            writes = [
                self._content_write(request.resource_type, updated_rows, rows),
                (
                    save_community_moderation_audits,
                    list([*audits, audit]),
                    list(audits),
                ),
                self._mutation_write([*mutations, record], mutations),
            ]
            self._rollback_writes(writes, self.data_dir)
        return result

    def list_moderation_audits(self) -> list[CommunityModerationAudit]:
        return load_community_moderation_audits(self.data_dir)

    def find_public_author(
        self,
        resource_type: PublicCommunityResourceType,
        resource_id: str,
    ) -> str | None:
        target = next(
            (
                row
                for row in self._load_content(resource_type)
                if row.id == resource_id
            ),
            None,
        )
        if target is None:
            return None
        # ``None`` means that the resource does not exist.  A retained but
        # de-identified public record deliberately reports the empty string so
        # callers do not misclassify it as a 404.
        return target.author_id or ""

    def purge_identity(
        self,
        identity_id: str,
        *,
        expected_account_id: str | None = None,
    ) -> bool:
        """Remove a JSONL identity after every dependent lifecycle is complete.

        This hook is intentionally JSONL-specific for now.  Supabase identity
        removal belongs to the future account-deletion transaction and its FK
        cascade; pretending that a public-community RPC already owns that
        boundary would create two different production sources of truth.
        """

        with self._locked_all():
            identities = load_anonymous_identities(self.data_dir)
            identity = next((row for row in identities if row.id == identity_id), None)
            if identity is None:
                return False
            if (
                expected_account_id is not None
                and identity.account_id != expected_account_id
            ):
                raise CommunityRepositoryError(
                    "本機社群身分與預期帳號不一致，拒絕移除。"
                )
            save_anonymous_identities(
                [row for row in identities if row.id != identity_id],
                self.data_dir,
            )
            return True

    def anonymize_public_author(
        self,
        request: PublicAuthorAnonymizationRequest,
        *,
        now: datetime | None = None,
    ) -> PublicAuthorAnonymizationResult:
        current = self._normalize_now(now)
        operation = "anonymize_public_author"
        fingerprint = community_mutation_fingerprint(operation, request)
        with self._locked_all():
            mutations = self._load_mutations()
            existing_mutation = self._find_mutation(mutations, request.mutation_id)
            if existing_mutation is not None:
                if not self._matches_mutation(
                    existing_mutation, operation, fingerprint
                ):
                    return PublicAuthorAnonymizationResult(
                        status=PublicAuthorAnonymizationStatus.IDEMPOTENCY_CONFLICT
                    )
                return PublicAuthorAnonymizationResult.model_validate(
                    existing_mutation.result
                )
            identities = load_anonymous_identities(self.data_dir)
            identity = next(
                (row for row in identities if row.id == request.identity_id), None
            )
            if identity is None:
                return PublicAuthorAnonymizationResult(
                    status=PublicAuthorAnonymizationStatus.IDENTITY_MISSING
                )
            if (
                request.expected_account_id is not None
                and identity.account_id != request.expected_account_id
            ):
                return PublicAuthorAnonymizationResult(
                    status=PublicAuthorAnonymizationStatus.IDENTITY_CONFLICT
                )

            counts: dict[str, int] = {}
            writes: list[tuple[Any, list[BaseModel], list[BaseModel]]] = []
            publish_events = load_community_publish_events(self.data_dir)
            retained_events = (
                [
                    event
                    for event in publish_events
                    if event.account_id != identity.account_id
                ]
                if identity.account_id is not None
                else list(publish_events)
            )
            counts["publish_event"] = len(publish_events) - len(retained_events)
            if retained_events != publish_events:
                writes.append(
                    (
                        save_community_publish_events,
                        list(retained_events),
                        list(publish_events),
                    )
                )
            for resource_type in PublicCommunityResourceType:
                rows = self._load_content(resource_type)
                changed = 0
                updated_rows: list[PublicCommunityContent] = []
                for row in rows:
                    if row.author_id != identity.id:
                        updated_rows.append(row)
                        continue
                    changed += 1
                    author_id: str | None = (
                        ""
                        if resource_type
                        in {
                            PublicCommunityResourceType.POST,
                            PublicCommunityResourceType.COMMENT,
                            PublicCommunityResourceType.CHAT,
                        }
                        else None
                    )
                    updates: dict[str, Any] = {
                        "author_id": author_id,
                        "display_name": request.replacement_name,
                        "identity_mode": CommunityIdentityMode.ANONYMOUS,
                    }
                    if isinstance(row, ExperienceSubmission):
                        updates["source_url"] = None
                    updated_rows.append(row.model_copy(update=updates))
                counts[resource_type.value] = changed
                if changed:
                    writes.append(
                        self._content_write(resource_type, updated_rows, rows)
                    )
            result = PublicAuthorAnonymizationResult(
                status=PublicAuthorAnonymizationStatus.COMMITTED,
                counts=counts,
            )
            record = _CommunityMutationRecord(
                mutation_id=request.mutation_id,
                operation=operation,
                fingerprint=fingerprint,
                result=result.model_dump(mode="json"),
                created_at=current,
            )
            writes.append(self._mutation_write([*mutations, record], mutations))
            self._rollback_writes(writes, self.data_dir)
        return result


class SupabaseCommunityRepository:
    """Server-only PostgREST adapter for the public community boundary."""

    backend_name = "supabase"

    _TABLES = {
        PublicCommunityResourceType.QUESTION: "exchange_community_questions",
        PublicCommunityResourceType.ANSWER: "exchange_community_answers",
        PublicCommunityResourceType.POST: "exchange_community_posts",
        PublicCommunityResourceType.COMMENT: "exchange_community_post_comments",
        PublicCommunityResourceType.CHAT: "exchange_community_public_chat_messages",
        PublicCommunityResourceType.EXPERIENCE: "exchange_community_experience_submissions",
    }

    def __init__(
        self,
        url: str,
        secret_key: str,
        *,
        timeout_seconds: float = 15.0,
        session: requests.Session | None = None,
    ) -> None:
        self._rest_url = f"{url.rstrip('/')}/rest/v1"
        self._timeout_seconds = timeout_seconds
        self._session = session or requests.Session()
        self._headers = {
            **supabase_key_headers(secret_key),
            "Content-Type": "application/json",
        }

    def _request(
        self,
        method: str,
        table: str,
        *,
        params: Mapping[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        try:
            response = self._session.request(
                method,
                f"{self._rest_url}/{table}",
                headers=self._headers,
                params=dict(params or {}),
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as error:
            status = getattr(getattr(error, "response", None), "status_code", None)
            raise CommunityRepositoryError(
                "Supabase 社群讀取失敗。", status_code=status
            ) from error
        except (TypeError, ValueError) as error:
            raise CommunityRepositoryError("Supabase 社群讀取回傳無效 JSON。") from error
        if not isinstance(payload, list) or not all(
            isinstance(row, dict) for row in payload
        ):
            raise CommunityRepositoryError("Supabase 社群讀取回傳格式不正確。")
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
            result = response.json()
        except requests.RequestException as error:
            status = getattr(getattr(error, "response", None), "status_code", None)
            raise CommunityRepositoryError(
                "Supabase 公開社群原子操作失敗。", status_code=status
            ) from error
        except (TypeError, ValueError) as error:
            raise CommunityRepositoryError(
                "Supabase 公開社群原子操作回傳無效 JSON。"
            ) from error
        if isinstance(result, list) and len(result) == 1:
            result = result[0]
        if not isinstance(result, dict):
            raise CommunityRepositoryError(
                "Supabase 公開社群原子操作回傳格式不正確。"
            )
        return result

    @staticmethod
    def _parse_status(enum_type: type[Enum], payload: Mapping[str, Any]) -> Any:
        try:
            return enum_type(str(payload.get("status") or ""))
        except ValueError as error:
            raise CommunityRepositoryError(
                "Supabase 公開社群原子操作回傳未知狀態。"
            ) from error

    def list_identities(self) -> list[AnonymousIdentity]:
        rows = self._request(
            "GET",
            "exchange_community_identities",
            params={"select": "*", "order": "created_at.asc"},
        )
        return [
            AnonymousIdentity.model_validate(_identity_row_from_supabase(row))
            for row in rows
        ]

    def find_identity_by_id(self, identity_id: str) -> AnonymousIdentity | None:
        rows = self._request(
            "GET",
            "exchange_community_identities",
            params={"select": "*", "id": f"eq.{identity_id}", "limit": "1"},
        )
        return (
            AnonymousIdentity.model_validate(_identity_row_from_supabase(rows[0]))
            if rows
            else None
        )

    def find_identity_by_account(self, account_id: str) -> AnonymousIdentity | None:
        rows = self._request(
            "GET",
            "exchange_community_identities",
            params={
                "select": "*",
                "account_id": f"eq.{account_id}",
                "limit": "1",
            },
        )
        return (
            AnonymousIdentity.model_validate(_identity_row_from_supabase(rows[0]))
            if rows
            else None
        )

    def commit_identity(
        self,
        request: CommunityIdentityMutationRequest,
        *,
        now: datetime | None = None,
    ) -> CommunityIdentityMutationResult:
        result = self._rpc(
            "exchange_commit_community_identity",
            {
                "p_mutation_id": request.mutation_id,
                "p_request_fingerprint": community_mutation_fingerprint(
                    "identity", request
                ),
                "p_identity": request.identity.model_dump(mode="json"),
            },
        )
        status = self._parse_status(CommunityIdentityMutationStatus, result)
        identity_payload = result.get("identity")
        identity = (
            AnonymousIdentity.model_validate(
                _identity_row_from_supabase(
                    identity_payload,
                    fallback_access_token_hash=request.identity.access_token_hash,
                )
            )
            if isinstance(identity_payload, Mapping)
            else None
        )
        if status == CommunityIdentityMutationStatus.COMMITTED and identity is None:
            raise CommunityRepositoryError(
                "Supabase 社群身分操作未回傳已提交身分。"
            )
        return CommunityIdentityMutationResult(status=status, identity=identity)

    def commit_publication(
        self,
        request: PublicCommunityPublicationRequest,
        *,
        now: datetime | None = None,
    ) -> PublicCommunityPublicationResult:
        result = self._rpc(
            "exchange_commit_public_community_publication",
            {
                "p_mutation_id": request.mutation_id,
                "p_request_fingerprint": public_community_publication_fingerprint(
                    request
                ),
                "p_account_id": request.account_id,
                "p_identity_id": request.identity_id,
                "p_access_token_hash": request.access_token_hash.casefold(),
                "p_resource_type": request.resource_type.value,
                "p_content": request.content,
            },
        )
        status = self._parse_status(PublicCommunityPublicationStatus, result)
        content = result.get("content")
        if isinstance(content, Mapping) and "resource_type" not in content:
            content = {
                "resource_type": request.resource_type.value,
                "payload": _content_row_from_supabase(
                    request.resource_type,
                    content,
                ),
            }
        response = PublicCommunityPublicationResult(
            status=status,
            content=dict(content) if isinstance(content, Mapping) else None,
            retry_after_seconds=result.get("retry_after_seconds"),
        )
        if status == PublicCommunityPublicationStatus.COMMITTED:
            if response.content is None:
                raise CommunityRepositoryError(
                    "Supabase 公開社群發布未回傳已提交內容。"
                )
            response.parsed_content()
        return response

    def _list_content(
        self, resource_type: PublicCommunityResourceType
    ) -> list[PublicCommunityContent]:
        rows = self._request(
            "GET",
            self._TABLES[resource_type],
            params={"select": "*", "order": "created_at.asc"},
        )
        return [
            _content_from_payload(
                resource_type,
                _content_row_from_supabase(resource_type, row),
            )
            for row in rows
        ]

    def list_questions(self) -> list[CommunityQuestion]:
        return [
            CommunityQuestion.model_validate(row)
            for row in self._list_content(PublicCommunityResourceType.QUESTION)
        ]

    def list_answers(self) -> list[CommunityAnswer]:
        return [
            CommunityAnswer.model_validate(row)
            for row in self._list_content(PublicCommunityResourceType.ANSWER)
        ]

    def list_posts(self) -> list[CommunityPost]:
        return [
            CommunityPost.model_validate(row)
            for row in self._list_content(PublicCommunityResourceType.POST)
        ]

    def list_comments(self) -> list[CommunityPostComment]:
        return [
            CommunityPostComment.model_validate(row)
            for row in self._list_content(PublicCommunityResourceType.COMMENT)
        ]

    def list_reactions(self) -> list[CommunityReaction]:
        rows = []
        while True:
            batch = self._request("GET", "exchange_community_reactions", params={
                "select": "account_id,resource_type,resource_id,reaction", "order": "account_id,resource_type,resource_id",
                "offset": len(rows), "limit": 1000})
            rows.extend(batch)
            if len(batch) < 1000:
                return [CommunityReaction.model_validate(row) for row in rows]

    def purge_account_interactions(self, account_id):
        # SQL FK ON DELETE CASCADE owns this cleanup in the account transaction.
        return None

    def list_bookmarks(self, account_id):
        return [row["post_id"] for row in self._request("GET", "exchange_community_bookmarks", params={
            "select": "post_id", "account_id": "eq." + account_id, "limit": 100})]

    def set_bookmark(self, account_id, post_id, saved):
        return self._rpc("exchange_set_community_bookmark", {"p_account_id": account_id, "p_post_id": post_id, "p_saved": saved})

    def set_reaction(self, account_id, resource_type, resource_id, reaction, *, platform_admin=False):
        return self._rpc("exchange_set_community_reaction", {"p_account_id": account_id, "p_resource_type": resource_type, "p_resource_id": resource_id, "p_reaction": reaction, "p_is_platform_admin": platform_admin})

    def list_public_chat_messages(self) -> list[PublicChatMessage]:
        return [
            PublicChatMessage.model_validate(row)
            for row in self._list_content(PublicCommunityResourceType.CHAT)
        ]

    def list_experience_submissions(self) -> list[ExperienceSubmission]:
        return [
            ExperienceSubmission.model_validate(row)
            for row in self._list_content(PublicCommunityResourceType.EXPERIENCE)
        ]

    def delete_public_content(
        self,
        request: PublicCommunityDeleteRequest,
        *,
        now: datetime | None = None,
    ) -> PublicCommunityDeleteResult:
        result = self._rpc(
            "exchange_delete_public_community_content",
            {
                "p_mutation_id": request.mutation_id,
                "p_request_fingerprint": community_mutation_fingerprint(
                    "delete_public_content", request
                ),
                "p_account_id": request.account_id,
                "p_identity_id": request.identity_id,
                "p_access_token_hash": request.access_token_hash.casefold(),
                "p_resource_type": request.resource_type.value,
                "p_resource_id": request.resource_id,
            },
        )
        status = self._parse_status(PublicCommunityDeleteStatus, result)
        return PublicCommunityDeleteResult(
            status=status,
            resource_id=result.get("resource_id"),
            deleted_comment_count=int(result.get("deleted_comment_count") or 0),
        )

    def list_moderation_queue(self) -> PublicCommunityModerationQueue:
        return PublicCommunityModerationQueue(
            question=[
                row for row in self.list_questions() if row.status == ModerationStatus.PENDING
            ],
            answer=[
                row for row in self.list_answers() if row.status == ModerationStatus.PENDING
            ],
            post=[row for row in self.list_posts() if row.status == ModerationStatus.PENDING],
            comment=[
                row for row in self.list_comments() if row.status == ModerationStatus.PENDING
            ],
            chat=[
                row
                for row in self.list_public_chat_messages()
                if row.status == ModerationStatus.PENDING
            ],
            experience=[
                row
                for row in self.list_experience_submissions()
                if row.status == ModerationStatus.PENDING
            ],
        )

    def commit_moderation(
        self,
        request: PublicCommunityModerationRequest,
        *,
        now: datetime | None = None,
    ) -> PublicCommunityModerationResult:
        result = self._rpc(
            "exchange_commit_public_community_moderation",
            {
                "p_mutation_id": request.mutation_id,
                "p_request_fingerprint": community_mutation_fingerprint(
                    "moderation", request
                ),
                "p_moderator_id": request.moderator_id,
                "p_resource_type": request.resource_type.value,
                "p_resource_id": request.resource_id,
                "p_expected_status": request.expected_status.value,
                "p_status": request.status.value,
                "p_note": request.note,
            },
        )
        status = self._parse_status(PublicCommunityModerationStatus, result)
        content = result.get("content")
        if isinstance(content, Mapping) and "resource_type" not in content:
            content = {
                "resource_type": request.resource_type.value,
                "payload": _content_row_from_supabase(
                    request.resource_type,
                    content,
                ),
            }
        audit_payload = result.get("audit")
        response = PublicCommunityModerationResult(
            status=status,
            content=dict(content) if isinstance(content, Mapping) else None,
            audit=(
                CommunityModerationAudit.model_validate(
                    _moderation_audit_row_from_supabase(audit_payload)
                )
                if isinstance(audit_payload, Mapping)
                else None
            ),
        )
        if status == PublicCommunityModerationStatus.COMMITTED and (
            response.content is None or response.audit is None
        ):
            raise CommunityRepositoryError(
                "Supabase moderation 未回傳內容與 audit。"
            )
        return response

    def list_moderation_audits(self) -> list[CommunityModerationAudit]:
        rows = self._request(
            "GET",
            "exchange_community_moderation_audits",
            params={
                "select": "*",
                "order": "created_at.desc",
            },
        )
        return [
            CommunityModerationAudit.model_validate(
                _moderation_audit_row_from_supabase(row)
            )
            for row in rows
        ]

    def find_public_author(
        self,
        resource_type: PublicCommunityResourceType,
        resource_id: str,
    ) -> str | None:
        rows = self._request(
            "GET",
            self._TABLES[resource_type],
            params={
                "select": "author_identity_id",
                "id": f"eq.{resource_id}",
                "limit": "1",
            },
        )
        if not rows:
            return None
        # Preserve the distinction between an absent resource (None) and a
        # retained, already de-identified resource (empty string).
        return str(rows[0].get("author_identity_id") or "")

    def anonymize_public_author(
        self,
        request: PublicAuthorAnonymizationRequest,
        *,
        now: datetime | None = None,
    ) -> PublicAuthorAnonymizationResult:
        result = self._rpc(
            "exchange_anonymize_public_community_author",
            {
                "p_mutation_id": request.mutation_id,
                "p_request_fingerprint": community_mutation_fingerprint(
                    "anonymize_public_author", request
                ),
                "p_identity_id": request.identity_id,
                "p_expected_account_id": request.expected_account_id,
                "p_replacement_name": request.replacement_name,
            },
        )
        status = self._parse_status(PublicAuthorAnonymizationStatus, result)
        counts = result.get("counts")
        if counts is None:
            counts = {}
        if not isinstance(counts, Mapping):
            raise CommunityRepositoryError(
                "Supabase 公開作者去識別回傳無效計數。"
            )
        return PublicAuthorAnonymizationResult(
            status=status,
            counts={str(key): int(value) for key, value in counts.items()},
        )

    def list_private_conversations(self) -> list[PrivateConversation]:
        rows = self._request(
            "GET",
            "exchange_community_private_conversations",
            params={"select": "*", "order": "updated_at.desc"},
        )
        return [PrivateConversation.model_validate(row) for row in rows]

    def list_private_messages(self) -> list[PrivateMessage]:
        rows = self._request(
            "GET",
            "exchange_community_private_messages",
            params={"select": "*", "order": "created_at.asc"},
        )
        return [PrivateMessage.model_validate(row) for row in rows]

    def list_blocks(self) -> list[CommunityBlock]:
        rows = self._request(
            "GET",
            "exchange_community_blocks",
            params={"select": "*", "order": "created_at.asc"},
        )
        return [CommunityBlock.model_validate(row) for row in rows]

    def list_reports(self, *, now: datetime | None = None) -> list[CommunityReport]:
        del now
        self._rpc("exchange_purge_private_community_operational_data", {})
        rows = self._request(
            "GET",
            "exchange_community_reports",
            params={"select": "*", "order": "created_at.desc"},
        )
        return [CommunityReport.model_validate(row) for row in rows]

    def _private_result(
        self,
        function_name: str,
        operation: str,
        request: BaseModel,
        payload: Mapping[str, Any],
    ) -> PrivateCommunityMutationResult:
        result = self._rpc(
            function_name,
            {
                "p_mutation_id": str(request.mutation_id),
                "p_request_fingerprint": private_community_mutation_fingerprint(
                    operation, request
                ),
                **dict(payload),
            },
        )
        status = self._parse_status(PrivateCommunityMutationStatus, result)
        response = PrivateCommunityMutationResult(
            status=status,
            conversation=(
                PrivateConversation.model_validate(result["conversation"])
                if isinstance(result.get("conversation"), Mapping)
                else None
            ),
            message=(
                PrivateMessage.model_validate(result["message"])
                if isinstance(result.get("message"), Mapping)
                else None
            ),
            block=(
                CommunityBlock.model_validate(result["block"])
                if isinstance(result.get("block"), Mapping)
                else None
            ),
            report=(
                CommunityReport.model_validate(result["report"])
                if isinstance(result.get("report"), Mapping)
                else None
            ),
            audit=(
                CommunityModerationAudit.model_validate(
                    _moderation_audit_row_from_supabase(result["audit"])
                )
                if isinstance(result.get("audit"), Mapping)
                else None
            ),
            counts=(
                {str(key): int(value) for key, value in result["counts"].items()}
                if isinstance(result.get("counts"), Mapping)
                else {}
            ),
        )
        if status == PrivateCommunityMutationStatus.COMMITTED and not any(
            (
                response.conversation,
                response.message,
                response.block,
                response.report,
                response.audit,
                response.counts,
            )
        ):
            raise CommunityRepositoryError(
                "Supabase 私人社群原子操作未回傳已提交資源。"
            )
        return response

    def commit_private_conversation(
        self,
        request: PrivateConversationMutationRequest,
        *,
        now: datetime | None = None,
    ) -> PrivateCommunityMutationResult:
        del now
        return self._private_result(
            "exchange_commit_private_community_conversation",
            "private_conversation",
            request,
            {
                "p_account_id": request.account_id,
                "p_identity_id": request.identity_id,
                "p_access_token_hash": request.access_token_hash,
                "p_recipient_identity_id": request.recipient_identity_id,
                "p_conversation": request.conversation.model_dump(mode="json"),
                "p_initial_message": request.initial_message.model_dump(mode="json"),
            },
        )

    def commit_private_conversation_status(
        self,
        request: PrivateConversationStatusMutationRequest,
        *,
        now: datetime | None = None,
    ) -> PrivateCommunityMutationResult:
        del now
        return self._private_result(
            "exchange_commit_private_community_conversation_status",
            "private_conversation_status",
            request,
            {
                "p_account_id": request.account_id,
                "p_identity_id": request.identity_id,
                "p_access_token_hash": request.access_token_hash,
                "p_conversation_id": request.conversation_id,
                "p_expected_status": request.expected_status.value,
                "p_status": request.status.value,
            },
        )

    def commit_private_message(
        self,
        request: PrivateMessageMutationRequest,
        *,
        now: datetime | None = None,
    ) -> PrivateCommunityMutationResult:
        del now
        return self._private_result(
            "exchange_commit_private_community_message",
            "private_message",
            request,
            {
                "p_account_id": request.account_id,
                "p_identity_id": request.identity_id,
                "p_access_token_hash": request.access_token_hash,
                "p_message": request.message.model_dump(mode="json"),
            },
        )

    def commit_block(
        self,
        request: CommunityBlockMutationRequest,
        *,
        now: datetime | None = None,
    ) -> PrivateCommunityMutationResult:
        del now
        return self._private_result(
            "exchange_commit_private_community_block",
            "community_block",
            request,
            {
                "p_account_id": request.account_id,
                "p_identity_id": request.identity_id,
                "p_access_token_hash": request.access_token_hash,
                "p_block": request.block.model_dump(mode="json"),
            },
        )

    def commit_report(
        self,
        request: CommunityReportMutationRequest,
        *,
        now: datetime | None = None,
    ) -> PrivateCommunityMutationResult:
        del now
        return self._private_result(
            "exchange_commit_private_community_report",
            "community_report",
            request,
            {
                "p_account_id": request.account_id,
                "p_identity_id": request.identity_id,
                "p_access_token_hash": request.access_token_hash,
                "p_report": request.report.model_dump(mode="json"),
            },
        )

    def commit_report_review(
        self,
        request: CommunityReportReviewMutationRequest,
        *,
        now: datetime | None = None,
    ) -> PrivateCommunityMutationResult:
        del now
        return self._private_result(
            "exchange_commit_private_community_report_review",
            "community_report_review",
            request,
            {
                "p_moderator_id": request.moderator_id,
                "p_report_id": request.report_id,
                "p_expected_status": request.expected_status.value,
                "p_status": request.status.value,
                "p_note": request.note,
            },
        )

    def purge_private_identity(
        self,
        request: PrivateCommunityIdentityPurgeRequest,
        *,
        now: datetime | None = None,
    ) -> PrivateCommunityMutationResult:
        del now
        return self._private_result(
            "exchange_purge_private_community_identity",
            "purge_private_identity",
            request,
            {
                "p_identity_id": request.identity_id,
                "p_expected_account_id": request.expected_account_id,
                "p_pending_report_retention_days": request.pending_report_retention_days,
            },
        )


def create_community_repository(
    data_dir: Path,
    environ: Mapping[str, str] | None = None,
) -> CommunityRepository:
    environment = os.environ if environ is None else environ
    mode = environment.get("EXCHANGE_COMMUNITY_REPOSITORY", "auto").strip().casefold()
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
        raise CommunityRepositoryError(
            "EXCHANGE_COMMUNITY_REPOSITORY 必須是 auto、jsonl 或 supabase。"
        )
    if runtime in {"production", "prod"} and mode == "jsonl":
        raise CommunityRepositoryError(
            "正式環境禁止使用 JSONL 社群資料；請設定 Supabase repository。"
        )
    if mode == "jsonl":
        return JsonlCommunityRepository(data_dir)
    if bool(url) != bool(secret_key):
        raise CommunityRepositoryError("Supabase URL 與 secret key 必須同時設定。")
    if mode == "supabase" or (url and secret_key):
        if not url or not secret_key:
            raise CommunityRepositoryError(
                "Supabase community repository 尚未完成伺服器端設定。"
            )
        return SupabaseCommunityRepository(url, secret_key)
    if runtime in {"production", "prod"}:
        raise CommunityRepositoryError(
            "正式環境禁止使用 JSONL 社群資料；請設定 Supabase repository。"
        )
    return JsonlCommunityRepository(data_dir)
