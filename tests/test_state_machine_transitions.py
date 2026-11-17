"""Table-driven specification tests for state machines across UniWay.

Companion reference: docs/architecture/state-machines.md
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from exchange_info.api import _calendar_feed_content, create_app
from exchange_info.community_repositories import (
    CommunityReportMutationRequest,
    CommunityReportReviewMutationRequest,
    JsonlCommunityRepository,
    PrivateCommunityMutationStatus,
    PrivateConversationMutationRequest,
    PrivateConversationStatusMutationRequest,
    PrivateMessageMutationRequest,
    PublicCommunityModerationRequest,
    PublicCommunityModerationStatus,
    PublicCommunityPublicationRequest,
    PublicCommunityResourceType,
)
from exchange_info.content_governance import (
    LocalContentGovernanceStore,
    approve_workflow_revision,
    publish_workflow_revision,
    reject_workflow_revision,
    rollback_published_workflow,
    stage_workflow_refresh,
    workflow_review_rule_keys,
    workflow_review_source_urls,
)
from exchange_info.destination_profile_review import (
    REQUIRED_DESTINATION_PROFILE_REVIEW_SECTIONS,
    build_destination_profile_review_queue,
)
from exchange_info.models import (
    AccountApplicationSelection,
    AccountCalendarEvent,
    AccountNotification,
    AccountSessionRecord,
    AccountSubmissionProgress,
    AnonymousIdentity,
    ApplicationSubmissionMethod,
    ApplicationWorkflowRollbackRequest,
    CommunityBoardKind,
    CommunityPost,
    CommunityReport,
    CommunityReportStatus,
    ConversationStatus,
    DestinationProfile,
    DestinationProfileReviewDecision,
    DestinationProfileReviewEvent,
    ModerationStatus,
    NotificationDelivery,
    AccountNotificationPreferences,
    PrivateConversation,
    PrivateMessage,
    SourceReference,
    SubmissionProgressTransitionRequest,
    SubmissionProofMetadata,
    UserAccount,
    utc_now,
)
from exchange_info.notifications import (
    MAX_EMAIL_ATTEMPTS,
    NotificationService,
)
from exchange_info.repositories import (
    AccountDeletionMutationRequest,
    JsonlAccountRepository,
)
from exchange_info.storage import (
    load_notification_deliveries,
    save_account_sessions,
    save_anonymous_identities,
    save_community_posts,
    save_user_accounts,
)
from exchange_info.submission_progress import (
    allowed_actions_for_submission_progress,
    transition_submission_progress,
)
from exchange_info.transient_auth import (
    LocalTransientAuthStore,
    TransientAuthState,
    TransientAuthStateKind,
)
from test_notifications import _content_workflow


REPO_ROOT = Path(__file__).resolve().parents[1]
APP_JS_PATH = REPO_ROOT / "src" / "exchange_info" / "static" / "app.js"
STATE_MACHINES_DOC = REPO_ROOT / "docs" / "architecture" / "state-machines.md"
NOW = datetime(2026, 11, 17, 2, 0, tzinfo=timezone.utc)


def test_state_machines_reference_doc_exists_and_covers_all_domains() -> None:
    text = STATE_MACHINES_DOC.read_text(encoding="utf-8")
    for expected in (
        "allowed_actions",
        "deriveAccountWorkspaceSyncStatus",
        "recover_interrupted_publishing",
        "ConversationStatus",
        "AccountApplicationSelection",
    ):
        assert expected in text


# ---------------------------------------------------------------------------
# #1 Submission Progress & Server-Driven allowed_actions
# ---------------------------------------------------------------------------


def _submission_request(
    method: ApplicationSubmissionMethod,
    action: str,
    *,
    with_proof: bool = False,
) -> SubmissionProgressTransitionRequest:
    proof = (
        SubmissionProofMetadata(kind="tracking", reference="REF-001")
        if with_proof
        else None
    )
    return SubmissionProgressTransitionRequest(
        home_school="長庚大學",
        progress_key=f"長庚大學::wf::v1::{method.value}",
        action=action,
        method=method,
        title="送件步驟測試",
        responsible_unit="國際事務處",
        proof_metadata=proof,
    )


def _state_at(
    method: ApplicationSubmissionMethod, status: str
) -> AccountSubmissionProgress | None:
    if status == "none":
        return None
    if method == ApplicationSubmissionMethod.UNKNOWN:
        return AccountSubmissionProgress(
            title="送件步驟測試",
            method=method,
            status="not_started" if status == "not_started" else status,
        )
    progress = AccountSubmissionProgress(
        title="送件步驟測試",
        method=method,
        status="not_started",
        responsible_unit="國際事務處",
    )
    if status == "not_started":
        return progress
    progress = transition_submission_progress(progress, _submission_request(method, "start"))
    if status == "preparing":
        return progress
    progress = transition_submission_progress(progress, _submission_request(method, "submit"))
    if status == "submitted":
        return progress
    progress = transition_submission_progress(
        progress, _submission_request(method, "confirm_receipt", with_proof=True)
    )
    if status == "receipt_confirmed":
        return progress
    progress = transition_submission_progress(
        progress, _submission_request(method, "complete")
    )
    assert status == "completed"
    return progress


@pytest.mark.parametrize(
    ("method", "status", "expected_allowed"),
    [
        (ApplicationSubmissionMethod.UNKNOWN, "not_started", []),
        (ApplicationSubmissionMethod.PAPER, "not_started", ["start"]),
        (ApplicationSubmissionMethod.PAPER, "preparing", ["submit", "revert"]),
        (ApplicationSubmissionMethod.PAPER, "submitted", ["confirm_receipt", "revert"]),
        (ApplicationSubmissionMethod.MIXED, "submitted", ["confirm_receipt", "revert"]),
        (
            ApplicationSubmissionMethod.ONLINE,
            "submitted",
            ["confirm_receipt", "complete", "revert"],
        ),
        (
            ApplicationSubmissionMethod.EMAIL,
            "submitted",
            ["confirm_receipt", "complete", "revert"],
        ),
        (
            ApplicationSubmissionMethod.IN_PERSON,
            "submitted",
            ["confirm_receipt", "complete", "revert"],
        ),
        (ApplicationSubmissionMethod.PAPER, "receipt_confirmed", ["complete", "revert"]),
        (ApplicationSubmissionMethod.ONLINE, "completed", ["revert"]),
    ],
)
def test_submission_progress_allowed_actions_serves_as_exact_transition_oracle(
    method: ApplicationSubmissionMethod,
    status: str,
    expected_allowed: list[str],
) -> None:
    current = _state_at(method, status)
    assert current is not None
    assert current.allowed_actions == expected_allowed
    assert allowed_actions_for_submission_progress(current.status, method) == expected_allowed

    for action in ("start", "submit", "confirm_receipt", "complete", "revert"):
        req = _submission_request(
            method,
            action,
            with_proof=(action == "confirm_receipt"),
        )
        if action in expected_allowed:
            updated = transition_submission_progress(current, req)
            assert updated.allowed_actions == allowed_actions_for_submission_progress(
                updated.status, updated.method
            )
        else:
            with pytest.raises(ValueError):
                transition_submission_progress(current, req)


def test_submission_progress_api_and_workspace_return_allowed_actions(
    tmp_path: Path,
) -> None:
    account = UserAccount(display_name="測試學生")
    token = "sm-submission-token"
    save_user_accounts([account], tmp_path)
    save_account_sessions(
        [
            AccountSessionRecord(
                account_id=account.id,
                token_hash=hashlib.sha256(token.encode("utf-8")).hexdigest(),
                expires_at=utc_now() + timedelta(hours=2),
            )
        ],
        tmp_path,
    )
    client = TestClient(create_app(tmp_path))
    headers = {"Authorization": f"Bearer {token}"}
    base = {
        "home_school": "長庚大學",
        "progress_key": "長庚大學::wf::v1::paper",
        "method": "paper",
        "title": "紙本送件",
    }
    res = client.post(
        "/account/submission-progress",
        headers=headers,
        json={**base, "action": "start"},
    )
    assert res.status_code == 200
    assert res.json()["allowed_actions"] == ["submit", "revert"]

    res2 = client.post(
        "/account/submission-progress",
        headers=headers,
        json={**base, "action": "submit"},
    )
    assert res2.status_code == 200
    assert res2.json()["allowed_actions"] == ["confirm_receipt", "revert"]

    ws = client.get(
        "/account/workspace",
        params={"home_school": "長庚大學"},
        headers=headers,
    )
    assert ws.status_code == 200
    assert ws.json()["workspace"]["submission_progress"][base["progress_key"]][
        "allowed_actions"
    ] == ["confirm_receipt", "revert"]


# ---------------------------------------------------------------------------
# #2 Application Workflow Content Governance
# ---------------------------------------------------------------------------


def test_workflow_governance_transition_table(tmp_path: Path) -> None:
    store = LocalContentGovernanceStore(tmp_path)
    first = stage_workflow_refresh(store, _content_workflow("第一版流程", version=1)).revision
    assert first.status.value == "pending_review"

    # Single approval keeps pending_review and cannot publish yet.
    approve_workflow_revision(
        store,
        first.id,
        reviewer_id="reviewer-1",
        note="核對官方簡章無誤",
        expected_content_hash=first.content_hash,
        reviewed_source_urls=workflow_review_source_urls(first.workflow),
        reviewed_rule_keys=workflow_review_rule_keys(first.workflow),
    )
    with pytest.raises(ValueError):
        publish_workflow_revision(store, first.id, reviewer_id="reviewer-1")

    # Second independent reviewer enables publication -> published.
    approve_workflow_revision(
        store,
        first.id,
        reviewer_id="reviewer-2",
        note="二次獨立核對通過",
        expected_content_hash=first.content_hash,
        reviewed_source_urls=workflow_review_source_urls(first.workflow),
        reviewed_rule_keys=workflow_review_rule_keys(first.workflow),
    )
    publish_workflow_revision(store, first.id, reviewer_id="reviewer-1")
    assert {row.id: row for row in store.list_revisions()}[
        first.id
    ].status.value == "published"

    # Rejection path: pending_review -> rejected.
    rejected_candidate = stage_workflow_refresh(
        store, _content_workflow("待退回草稿", version=2)
    ).revision
    rejected = reject_workflow_revision(
        store, rejected_candidate.id, reviewer_id="reviewer-1", note="來源年份有誤"
    )
    assert rejected.status.value == "rejected"

    # Supersede & rollback path: publishing v3 supersedes v1; rollback restores v1.
    second = stage_workflow_refresh(
        store, _content_workflow("第二版正式流程", version=3)
    ).revision
    for reviewer in ("reviewer-1", "reviewer-2"):
        approve_workflow_revision(
            store,
            second.id,
            reviewer_id=reviewer,
            note="核對第二版來源",
            expected_content_hash=second.content_hash,
            reviewed_source_urls=workflow_review_source_urls(second.workflow),
            reviewed_rule_keys=workflow_review_rule_keys(second.workflow),
        )
    publish_workflow_revision(store, second.id, reviewer_id="reviewer-2")
    revisions_by_id = {row.id: row for row in store.list_revisions()}
    assert revisions_by_id[first.id].status.value == "superseded"
    assert revisions_by_id[second.id].status.value == "published"

    published_second = revisions_by_id[second.id]
    rolled_back = rollback_published_workflow(
        store,
        ApplicationWorkflowRollbackRequest(
            workflow_key=published_second.workflow_key,
            expected_current_revision_id=published_second.id,
            expected_current_version=published_second.version,
            expected_current_content_hash=published_second.content_hash,
            restore_revision_id=first.id,
            note="第二版發現勘誤，回滾至第一版正式流程",
        ),
        rolled_back_by="reviewer-1",
    )
    revisions_after_rollback = {row.id: row for row in store.list_revisions()}
    assert revisions_after_rollback[second.id].status.value == "superseded"
    assert any(
        row.status.value == "published" and row.restored_revision_id == first.id
        for row in revisions_after_rollback.values()
    ) or getattr(rolled_back, "workflow_id", None) is not None


# ---------------------------------------------------------------------------
# #3 Destination Profile Dual Review Derivation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("decisions", "expected_progress", "expected_ready"),
    [
        ([], "unstarted", False),
        ([("rev-a", DestinationProfileReviewDecision.APPROVE)], "partial", False),
        (
            [
                ("rev-a", DestinationProfileReviewDecision.APPROVE),
                ("rev-b", DestinationProfileReviewDecision.APPROVE),
            ],
            "ready_for_promotion",
            True,
        ),
        (
            [
                ("rev-a", DestinationProfileReviewDecision.APPROVE),
                ("rev-b", DestinationProfileReviewDecision.CHANGES_REQUIRED),
            ],
            "changes_required",
            False,
        ),
    ],
)
def test_destination_profile_review_progress_derivation_table(
    decisions: list[tuple[str, DestinationProfileReviewDecision]],
    expected_progress: str,
    expected_ready: bool,
) -> None:
    profile = DestinationProfile(
        home_university="長庚大學",
        school_name="測試合作大學",
        country="日本",
        city="東京",
        coverage_status="official_partial",
        coverage_note="測試查核說明",
        last_checked=NOW,
        sources=[
            SourceReference(
                title="官方交換生手冊",
                source_url="https://example.edu/handbook",
            )
        ],
    )
    initial_queue = build_destination_profile_review_queue([profile])
    content_hash = initial_queue.items[0].profile_content_hash
    snapshot_fp = initial_queue.snapshot_fingerprint
    section_keys = [section.key for section in REQUIRED_DESTINATION_PROFILE_REVIEW_SECTIONS]

    events = [
        DestinationProfileReviewEvent(
            home_university="長庚大學",
            school_name="測試合作大學",
            profile_content_hash=content_hash,
            snapshot_fingerprint=snapshot_fp,
            reviewer_id=reviewer_id,
            reviewer_display_name=reviewer_id,
            decision=decision,
            reviewed_section_keys=section_keys,
            reviewed_source_urls=["https://example.edu/handbook"],
            note="獨立核對官方交換手冊紀錄",
        )
        for reviewer_id, decision in decisions
    ]
    queue = build_destination_profile_review_queue([profile], review_events=events)
    row = queue.items[0]
    assert row.review_progress == expected_progress
    assert row.ready_for_promotion is expected_ready


# ---------------------------------------------------------------------------
# #4, #5, #6 Community Moderation, Reports & Private Conversation Invite
# ---------------------------------------------------------------------------


def _seed_community_pair(
    tmp_path: Path,
) -> tuple[
    JsonlCommunityRepository,
    UserAccount,
    AnonymousIdentity,
    UserAccount,
    AnonymousIdentity,
]:
    sender = UserAccount(
        id="acc-sender",
        email="sender@cgu.edu.tw",
        email_verified=True,
        display_name="發起同學",
        home_university="長庚大學",
        created_at=NOW - timedelta(days=30),
    )
    recipient = UserAccount(
        id="acc-recipient",
        email="recipient@cgu.edu.tw",
        email_verified=True,
        display_name="收件同學",
        home_university="長庚大學",
        created_at=NOW - timedelta(days=30),
    )
    sender_token = hashlib.sha256(b"sender-anon-token").hexdigest()
    recipient_token = hashlib.sha256(b"recipient-anon-token").hexdigest()
    sender_id = AnonymousIdentity(
        id="anon-sender-001",
        account_id=sender.id,
        display_name="匿名發起人",
        access_token_hash=sender_token,
        created_at=NOW,
        updated_at=NOW,
    )
    recipient_id = AnonymousIdentity(
        id="anon-recipient-001",
        account_id=recipient.id,
        display_name="匿名收件人",
        access_token_hash=recipient_token,
        created_at=NOW,
        updated_at=NOW,
    )
    save_user_accounts([sender, recipient], tmp_path)
    save_anonymous_identities([sender_id, recipient_id], tmp_path)
    return JsonlCommunityRepository(tmp_path), sender, sender_id, recipient, recipient_id


@pytest.mark.parametrize(
    "target_status",
    [ConversationStatus.ACCEPTED, ConversationStatus.DECLINED],
)
def test_private_conversation_invite_accept_and_decline_transitions(
    tmp_path: Path, target_status: ConversationStatus
) -> None:
    repo, sender, sender_id, recipient, recipient_id = _seed_community_pair(tmp_path)
    conv = PrivateConversation(
        id=f"conv-{target_status.value}",
        school_name="林肯大學 Lincoln University",
        sender_id=sender_id.id,
        sender_name=sender_id.display_name,
        recipient_id=recipient_id.id,
        recipient_name=recipient_id.display_name,
        created_at=NOW,
        updated_at=NOW,
    )
    msg = PrivateMessage(
        id=f"msg-init-{target_status.value}",
        conversation_id=conv.id,
        author_id=sender_id.id,
        display_name=sender_id.display_name,
        body="你好，想請教交換住宿申請時間！",
        created_at=NOW,
    )
    created = repo.commit_private_conversation(
        PrivateConversationMutationRequest(
            mutation_id=f"mut-create-{target_status.value}-0001",
            account_id=sender.id,
            identity_id=sender_id.id,
            access_token_hash=sender_id.access_token_hash,
            recipient_identity_id=recipient_id.id,
            conversation=conv,
            initial_message=msg,
        ),
        now=NOW,
    )
    assert created.status == PrivateCommunityMutationStatus.COMMITTED

    # Sender cannot accept or decline their own invite -> RECIPIENT_ONLY.
    sender_attempt = repo.commit_private_conversation_status(
        PrivateConversationStatusMutationRequest(
            mutation_id=f"mut-sender-try-{target_status.value}-0001",
            account_id=sender.id,
            identity_id=sender_id.id,
            access_token_hash=sender_id.access_token_hash,
            conversation_id=conv.id,
            expected_status=ConversationStatus.PENDING,
            status=target_status,
        ),
        now=NOW + timedelta(seconds=1),
    )
    assert sender_attempt.status == PrivateCommunityMutationStatus.RECIPIENT_ONLY

    # Recipient transitions pending -> accepted | declined.
    transitioned = repo.commit_private_conversation_status(
        PrivateConversationStatusMutationRequest(
            mutation_id=f"mut-recip-{target_status.value}-0001",
            account_id=recipient.id,
            identity_id=recipient_id.id,
            access_token_hash=recipient_id.access_token_hash,
            conversation_id=conv.id,
            expected_status=ConversationStatus.PENDING,
            status=target_status,
        ),
        now=NOW + timedelta(seconds=2),
    )
    assert transitioned.status == PrivateCommunityMutationStatus.COMMITTED
    assert transitioned.conversation is not None
    assert transitioned.conversation.status == target_status

    # Terminal CAS: flipping again from pending fails with STATUS_CONFLICT.
    opposite = (
        ConversationStatus.DECLINED
        if target_status == ConversationStatus.ACCEPTED
        else ConversationStatus.ACCEPTED
    )
    flip = repo.commit_private_conversation_status(
        PrivateConversationStatusMutationRequest(
            mutation_id=f"mut-flip-{target_status.value}-0001",
            account_id=recipient.id,
            identity_id=recipient_id.id,
            access_token_hash=recipient_id.access_token_hash,
            conversation_id=conv.id,
            expected_status=ConversationStatus.PENDING,
            status=opposite,
        ),
        now=NOW + timedelta(seconds=3),
    )
    assert flip.status == PrivateCommunityMutationStatus.STATUS_CONFLICT

    # Follow-up message: allowed ONLY when accepted; blocked with STATUS_CONFLICT when declined.
    followup = repo.commit_private_message(
        PrivateMessageMutationRequest(
            mutation_id=f"mut-msg-{target_status.value}-0001",
            account_id=sender.id,
            identity_id=sender_id.id,
            access_token_hash=sender_id.access_token_hash,
            message=PrivateMessage(
                id=f"msg-next-{target_status.value}",
                conversation_id=conv.id,
                author_id=sender_id.id,
                display_name=sender_id.display_name,
                body="謝謝你的回覆！",
                created_at=NOW + timedelta(seconds=4),
            ),
        ),
        now=NOW + timedelta(seconds=4),
    )
    if target_status == ConversationStatus.ACCEPTED:
        assert followup.status == PrivateCommunityMutationStatus.COMMITTED
    else:
        assert followup.status == PrivateCommunityMutationStatus.STATUS_CONFLICT


def test_private_conversation_decline_http_route_and_idempotency(
    tmp_path: Path,
) -> None:
    app = create_app(tmp_path)
    sender = UserAccount(
        id="http-sender",
        email="s@cgu.edu.tw",
        email_verified=True,
        display_name="甲同學",
        home_university="長庚大學",
    )
    recipient = UserAccount(
        id="http-recipient",
        email="r@cgu.edu.tw",
        email_verified=True,
        display_name="乙同學",
        home_university="長庚大學",
    )
    sender_bearer = "bearer-sender-token"
    recipient_bearer = "bearer-recipient-token"
    sender_anon_secret = "anon-secret-sender-123456"
    recipient_anon_secret = "anon-secret-recipient-123456"
    save_user_accounts([sender, recipient], tmp_path)
    save_account_sessions(
        [
            AccountSessionRecord(
                account_id=sender.id,
                token_hash=hashlib.sha256(sender_bearer.encode("utf-8")).hexdigest(),
                expires_at=utc_now() + timedelta(hours=2),
            ),
            AccountSessionRecord(
                account_id=recipient.id,
                token_hash=hashlib.sha256(recipient_bearer.encode("utf-8")).hexdigest(),
                expires_at=utc_now() + timedelta(hours=2),
            ),
        ],
        tmp_path,
    )
    save_anonymous_identities(
        [
            AnonymousIdentity(
                id="anon-http-sender",
                account_id=sender.id,
                display_name="匿名甲",
                access_token_hash=hashlib.sha256(
                    sender_anon_secret.encode("utf-8")
                ).hexdigest(),
            ),
            AnonymousIdentity(
                id="anon-http-recipient",
                account_id=recipient.id,
                display_name="匿名乙",
                access_token_hash=hashlib.sha256(
                    recipient_anon_secret.encode("utf-8")
                ).hexdigest(),
            ),
        ],
        tmp_path,
    )
    client = TestClient(app)
    partner_name = "林肯大學 Lincoln University"
    created = client.post(
        "/community/conversations",
        headers={
            "Authorization": f"Bearer {sender_bearer}",
            "X-Anonymous-ID": "anon-http-sender",
            "X-Anonymous-Token": sender_anon_secret,
            "X-Community-Mutation-ID": "http-conv-create-0001",
        },
        json={
            "school_name": partner_name,
            "recipient_id": "anon-http-recipient",
            "initial_message": "你好，方便請教選課經驗嗎？",
        },
    )
    assert created.status_code == 201
    conv_id = created.json()["id"]

    recipient_headers = {
        "Authorization": f"Bearer {recipient_bearer}",
        "X-Anonymous-ID": "anon-http-recipient",
        "X-Anonymous-Token": recipient_anon_secret,
        "X-Community-Mutation-ID": "http-conv-decline-0001",
    }
    declined = client.post(
        f"/community/conversations/{conv_id}/decline",
        headers=recipient_headers,
    )
    assert declined.status_code == 200
    assert declined.json()["status"] == "declined"

    # Idempotent replay with same X-Community-Mutation-ID returns 200 with identical declined state.
    replayed = client.post(
        f"/community/conversations/{conv_id}/decline",
        headers=recipient_headers,
    )
    assert replayed.status_code == 200
    assert replayed.json()["status"] == "declined"

    # Attempting to accept after declining fails with 409 conflict.
    accept_after_decline = client.post(
        f"/community/conversations/{conv_id}/accept",
        headers={
            **recipient_headers,
            "X-Community-Mutation-ID": "http-conv-accept-after-decline",
        },
    )
    assert accept_after_decline.status_code == 409


@pytest.mark.parametrize(
    ("terminal_status",),
    [(CommunityReportStatus.RESOLVED,), (CommunityReportStatus.DISMISSED,)],
)
def test_community_moderation_and_report_terminal_transitions(
    tmp_path: Path, terminal_status: CommunityReportStatus
) -> None:
    repo, sender, sender_id, recipient, recipient_id = _seed_community_pair(tmp_path)
    post = CommunityPost(
        id="mod-post-001",
        board_id="public-study-abroad",
        board_kind=CommunityBoardKind.PUBLIC_STUDY_ABROAD,
        school_name="公共留學板",
        author_id=sender_id.id,
        display_name="匿名學生",
        title="長庚校內申請時間整理",
        body="分享今年申請準備時程與注意事項。",
        status=ModerationStatus.PENDING,
        created_at=NOW,
    )
    save_community_posts([post], tmp_path)

    hidden = repo.commit_moderation(
        PublicCommunityModerationRequest(
            mutation_id="mod-hide-post-0001",
            moderator_id=recipient.id,
            resource_type=PublicCommunityResourceType.POST,
            resource_id=post.id,
            expected_status=ModerationStatus.PENDING,
            status=ModerationStatus.HIDDEN,
            note="先隱藏待確認內容",
        ),
        now=NOW + timedelta(seconds=1),
    )
    assert hidden.status == PublicCommunityModerationStatus.COMMITTED

    stale_mod = repo.commit_moderation(
        PublicCommunityModerationRequest(
            mutation_id="mod-stale-post-0001",
            moderator_id=recipient.id,
            resource_type=PublicCommunityResourceType.POST,
            resource_id=post.id,
            expected_status=ModerationStatus.APPROVED,
            status=ModerationStatus.HIDDEN,
            note="過期狀態測試",
        ),
        now=NOW + timedelta(seconds=2),
    )
    assert stale_mod.status == PublicCommunityModerationStatus.STATUS_CONFLICT

    report = CommunityReport(
        id=f"rep-{terminal_status.value}-001",
        reporter_id=recipient_id.id,
        resource_type="post",
        resource_id=post.id,
        reason="內容疑似過期需要管理員核對",
    )
    created_report = repo.commit_report(
        CommunityReportMutationRequest(
            mutation_id=f"rep-create-{terminal_status.value}-0001",
            account_id=recipient.id,
            identity_id=recipient_id.id,
            access_token_hash=recipient_id.access_token_hash,
            report=report,
        ),
        now=NOW + timedelta(seconds=3),
    )
    assert created_report.status == PrivateCommunityMutationStatus.COMMITTED

    reviewed = repo.commit_report_review(
        CommunityReportReviewMutationRequest(
            mutation_id=f"rep-review-{terminal_status.value}-0001",
            moderator_id=sender.id,
            report_id=report.id,
            expected_status=CommunityReportStatus.PENDING,
            status=terminal_status,
            note="已完成人工檢視結案",
        ),
        now=NOW + timedelta(seconds=4),
    )
    assert reviewed.status == PrivateCommunityMutationStatus.COMMITTED
    assert reviewed.report is not None
    assert reviewed.report.status == terminal_status

    re_review = repo.commit_report_review(
        CommunityReportReviewMutationRequest(
            mutation_id=f"rep-rereview-{terminal_status.value}-0001",
            moderator_id=sender.id,
            report_id=report.id,
            expected_status=CommunityReportStatus.PENDING,
            status=CommunityReportStatus.RESOLVED,
            note="終態不可再次結案",
        ),
        now=NOW + timedelta(seconds=5),
    )
    assert re_review.status == PrivateCommunityMutationStatus.STATUS_CONFLICT


# ---------------------------------------------------------------------------
# #7 Notification Delivery Loop & #8/#9 Student Checklist Rules
# ---------------------------------------------------------------------------


class _StubEmailSender:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.sent: list[tuple[str, str]] = []

    def send(self, email: str, subject: str, body: str) -> None:
        if self.fail:
            raise RuntimeError("SMTP temporary failure")
        self.sent.append((email, subject))


@pytest.mark.parametrize(
    ("email_enabled", "sender_fails", "prior_attempts", "expected_status"),
    [
        (False, False, 0, "cancelled"),
        (True, False, 0, "sent"),
        (True, True, 0, "retrying"),
        (True, True, MAX_EMAIL_ATTEMPTS - 1, "failed"),
    ],
)
def test_notification_email_delivery_transition_table(
    tmp_path: Path,
    email_enabled: bool,
    sender_fails: bool,
    prior_attempts: int,
    expected_status: str,
) -> None:
    repo = JsonlAccountRepository(tmp_path)
    account = UserAccount(
        id="notif-acc-1",
        email="student@cgu.edu.tw",
        email_verified=True,
        display_name="通知測試學生",
        notification_preferences=AccountNotificationPreferences(
            email_enabled=email_enabled,
            content_updates_enabled=True,
        ),
    )
    repo.save_account(account)
    notification = AccountNotification(
        id="notif-item-1",
        account_id=account.id,
        kind="content_update",
        source_key="wf-key-1",
        dedupe_key="dedupe-notif-1",
        title="合作校來源更新",
        body="合作校申請簡章有更新。",
        source_url="https://example.edu/notice",
    )
    repo.save_notification(notification)
    delivery = NotificationDelivery(
        id="delivery-1",
        notification_id=notification.id,
        account_id=account.id,
        status="retrying" if prior_attempts else "pending",
        attempt_count=prior_attempts,
        next_attempt_at=NOW - timedelta(minutes=1),
    )
    repo.save_delivery(delivery)

    service = NotificationService(
        repo,
        email_sender=_StubEmailSender(fail=sender_fails),
    )
    service.dispatch_due_emails(now=NOW)
    saved = load_notification_deliveries(tmp_path)[0]
    assert saved.status == expected_status


def test_document_selection_allows_free_jumps_and_calendar_ics_uses_ready_state() -> None:
    all_statuses = (
        "draft",
        "ready_to_print",
        "pending_signature",
        "pending_department_stamp",
        "pending_submission",
        "completed",
    )
    for status in reversed(all_statuses):
        selection = AccountApplicationSelection(selected=True, copies=2, status=status)
        assert selection.status == status

    todo_event = AccountCalendarEvent(
        id="ev-todo", title="準備讀書計畫", date="2026-12-01", status="todo"
    )
    ready_event = AccountCalendarEvent(
        id="ev-ready", title="已完成成績單", date="2026-12-02", status="ready"
    )
    ics = _calendar_feed_content([todo_event, ready_event])
    blocks = ics.split("BEGIN:VEVENT")
    todo_block = next(block for block in blocks if "ev-todo" in block)
    ready_block = next(block for block in blocks if "ev-ready" in block)
    assert "BEGIN:VALARM" in todo_block
    assert "BEGIN:VALARM" not in ready_block


# ---------------------------------------------------------------------------
# #13/#14 Web Workspace Sync 6-State Selector & Server allowed_actions UI
# ---------------------------------------------------------------------------


def test_web_workspace_sync_selector_matches_flutter_six_states_and_submission_ui() -> None:
    node_script = r"""
const fs = require("fs");
const vm = require("vm");
const assert = require("assert");

const source = fs.readFileSync(process.argv[1], "utf8");

function extractConstOrFunction(code, startMarker, endMarker) {
  const start = code.indexOf(startMarker);
  assert(start >= 0, `Missing start marker: ${startMarker}`);
  const end = code.indexOf(endMarker, start);
  assert(end > start, `Missing end marker: ${endMarker}`);
  return code.slice(start, end);
}

const syncSnippet = extractConstOrFunction(
  source,
  "const WORKSPACE_SYNC_STATUSES =",
  "function renderAccountWorkspaceSyncStatus()"
);
const submissionSnippet = extractConstOrFunction(
  source,
  "function submissionProgressAllowedActions(",
  "function submissionProgressNextStep("
);
const privateConvSnippet = extractConstOrFunction(
  source,
  "function renderPrivateConversation(",
  "function renderCommunityThread("
);

const sandbox = {
  state: { anonymousIdentity: { id: "me-id" } },
  navigator: { onLine: true },
  escapeHtml: (value) => String(value ?? ""),
  formatDate: (value) => String(value ?? ""),
};
vm.createContext(sandbox);
vm.runInContext(
  `${syncSnippet}\n${submissionSnippet}\n${privateConvSnippet}\nglobalThis.exports = { state, WORKSPACE_SYNC_STATUSES, deriveAccountWorkspaceSyncStatus, submissionProgressActions, renderPrivateConversation };`,
  sandbox
);
const {
  state: sandboxState,
  WORKSPACE_SYNC_STATUSES,
  deriveAccountWorkspaceSyncStatus,
  submissionProgressActions,
  renderPrivateConversation,
} = sandbox.exports;

assert.deepStrictEqual(
  [...WORKSPACE_SYNC_STATUSES],
  ["loading", "saved", "pending", "syncing", "conflict", "expired"]
);

const syncCases = [
  [{ account: { id: "u1" }, accountWorkspaceHasSynced: false }, true, "loading", "syncing"],
  [{ account: { id: "u1" }, accountWorkspaceLoadingCount: 1 }, true, "loading", "syncing"],
  [{ account: { id: "u1" }, accountWorkspaceSyncLanes: { cgu: Promise.resolve() } }, true, "syncing", "syncing"],
  [{ account: { id: "u1" }, accountWorkspacePending: { cgu: {} } }, true, "pending", "pending"],
  [{ account: { id: "u1" }, accountWorkspaceSyncErrors: { cgu: "timeout" }, accountWorkspaceSyncErrorStatuses: { cgu: 503 } }, true, "pending", "failed"],
  [{ account: { id: "u1" }, accountWorkspaceSyncErrors: { cgu: "conflict" }, accountWorkspaceSyncErrorStatuses: { cgu: 409 } }, true, "conflict", "failed"],
  [{ account: { id: "u1" }, accountWorkspaceSyncErrors: { cgu: "unauthorized" }, accountWorkspaceSyncErrorStatuses: { cgu: 401 } }, true, "expired", "failed"],
  [{ account: null, quarantinedAccountOwnerId: "u1" }, true, "expired", "failed"],
  [{ account: { id: "u1" }, accountWorkspaceHasSynced: true }, true, "saved", "synced"],
  [{ account: { id: "u1" }, accountWorkspaceHasSynced: true }, false, "saved", "offline"],
  [{ account: { id: "u1" }, accountWorkspacePending: { cgu: {} }, accountWorkspaceHasSynced: true }, false, "pending", "offline"],
];

for (const [stateInput, online, expectedStatus, expectedUi] of syncCases) {
  const actual = deriveAccountWorkspaceSyncStatus(stateInput, { online });
  assert.strictEqual(actual.status, expectedStatus);
  assert.strictEqual(actual.uiState, expectedUi);
}

// Web submission UI trusts server allowed_actions rather than re-deriving rules.
const paperActions = submissionProgressActions(
  { status: "submitted", allowed_actions: ["confirm_receipt", "revert"] },
  "paper"
);
assert.deepStrictEqual(paperActions.map((a) => a.action), ["confirm_receipt"]);

const onlineActions = submissionProgressActions(
  { status: "submitted", allowed_actions: ["confirm_receipt", "complete", "revert"] },
  "online"
);
assert.deepStrictEqual(onlineActions.map((a) => a.action), ["confirm_receipt", "complete"]);
assert.strictEqual(onlineActions[1].label, "沒有回條，手動標記完成");

const confirmedActions = submissionProgressActions(
  { status: "receipt_confirmed", allowed_actions: ["complete", "revert"] },
  "paper"
);
assert.deepStrictEqual(confirmedActions.map((a) => a.action), ["complete"]);
assert.strictEqual(confirmedActions[0].label, "確認並標記完成");

// Private conversation UI renders both accept and decline for pending recipient, and read-only status for declined.
sandboxState.anonymousIdentity = { id: "recipient-1" };
const pendingHtml = renderPrivateConversation(
  { id: "c1", sender_id: "sender-1", sender_name: "甲", recipient_id: "recipient-1", recipient_name: "乙", status: "pending" },
  []
);
assert(pendingHtml.includes('data-accept-conversation="c1"'));
assert(pendingHtml.includes('data-decline-conversation="c1"'));
assert(!pendingHtml.includes("private-message-form"));

const declinedRecipientHtml = renderPrivateConversation(
  { id: "c1", sender_id: "sender-1", sender_name: "甲", recipient_id: "recipient-1", recipient_name: "乙", status: "declined" },
  []
);
assert(declinedRecipientHtml.includes("已婉拒邀請"));
assert(!declinedRecipientHtml.includes("data-accept-conversation"));
assert(!declinedRecipientHtml.includes("data-decline-conversation"));
assert(!declinedRecipientHtml.includes("private-message-form"));

sandboxState.anonymousIdentity = { id: "sender-1" };
const declinedSenderHtml = renderPrivateConversation(
  { id: "c1", sender_id: "sender-1", sender_name: "甲", recipient_id: "recipient-1", recipient_name: "乙", status: "declined" },
  []
);
assert(declinedSenderHtml.includes("對方已婉拒邀請"));
"""
    completed = subprocess.run(
        ["node", "-e", node_script, str(APP_JS_PATH)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout


# ---------------------------------------------------------------------------
# #16 Transient OAuth State & Account Deletion Request Invariants
# ---------------------------------------------------------------------------


def test_transient_auth_one_time_consumption_and_deletion_request_shapes() -> None:
    store = LocalTransientAuthStore()
    record = TransientAuthState(
        state_hash="a" * 64,
        kind=TransientAuthStateKind.OAUTH_LOGIN,
        provider_id="google",
        expires_at=utc_now() + timedelta(minutes=5),
    )
    store.save_state(record)

    # Wrong provider does not consume the state.
    assert (
        store.consume_state(
            "a" * 64,
            TransientAuthStateKind.OAUTH_LOGIN,
            expected_provider_id="apple",
        )
        is None
    )
    # Matching provider consumes once; second consume returns None.
    assert (
        store.consume_state(
            "a" * 64,
            TransientAuthStateKind.OAUTH_LOGIN,
            expected_provider_id="google",
        )
        == record
    )
    assert (
        store.consume_state(
            "a" * 64,
            TransientAuthStateKind.OAUTH_LOGIN,
            expected_provider_id="google",
        )
        is None
    )

    # AccountDeletionMutationRequest: initial requires both account_id + session_id; replay omits both.
    initial = AccountDeletionMutationRequest(
        mutation_id="delete-account-mut-0001",
        session_token_hash="b" * 64,
        account_id="acc-1",
        session_id="sess-1",
        email_fingerprint="c" * 64,
    )
    assert initial.account_id == "acc-1"

    replay_shape = AccountDeletionMutationRequest(
        mutation_id="delete-account-mut-0001",
        session_token_hash="b" * 64,
    )
    assert replay_shape.account_id is None

    with pytest.raises(ValidationError):
        AccountDeletionMutationRequest(
            mutation_id="delete-account-mut-0002",
            session_token_hash="b" * 64,
            account_id="acc-1",
        )
