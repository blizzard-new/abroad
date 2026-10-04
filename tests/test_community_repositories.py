from __future__ import annotations

import hashlib
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from exchange_info import community_repositories as repositories
from exchange_info.community_repositories import (
    CommunityBlockMutationRequest,
    CommunityIdentityMutationRequest,
    CommunityIdentityMutationStatus,
    CommunityReportMutationRequest,
    CommunityReportReviewMutationRequest,
    CommunityRepositoryError,
    JsonlCommunityRepository,
    PrivateCommunityMutationStatus,
    PrivateCommunityIdentityPurgeRequest,
    PrivateConversationMutationRequest,
    PrivateConversationStatusMutationRequest,
    PrivateMessageMutationRequest,
    PublicAuthorAnonymizationRequest,
    PublicCommunityDeleteRequest,
    PublicCommunityDeleteStatus,
    PublicCommunityModerationRequest,
    PublicCommunityModerationStatus,
    PublicCommunityPublicationRequest,
    PublicCommunityPublicationStatus,
    PublicCommunityResourceType,
    SupabaseCommunityRepository,
    create_community_repository,
)
from exchange_info.models import (
    AnonymousIdentity,
    CommunityAnswer,
    CommunityBlock,
    CommunityBoardKind,
    CommunityIdentityMode,
    CommunityPost,
    CommunityPostComment,
    CommunityPublishEvent,
    CommunityQuestion,
    CommunityReport,
    CommunityReportStatus,
    CommunityTopic,
    ConversationStatus,
    ExperienceSubmission,
    ModerationStatus,
    PrivateConversation,
    PrivateMessage,
    PublicChatMessage,
    UserAccount,
)
from exchange_info.storage import (
    ensure_data_dirs,
    load_anonymous_identities,
    load_community_moderation_audits,
    load_community_post_comments,
    load_community_posts,
    load_community_publish_events,
    load_private_conversations,
    load_private_messages,
    save_anonymous_identities,
    save_community_posts,
    save_community_publish_events,
    save_private_conversations,
    save_private_messages,
    save_user_accounts,
)


NOW = datetime(2026, 8, 23, 12, 0, tzinfo=timezone.utc)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _seed_actor(
    data_dir: Path,
    *,
    email_verified: bool = True,
    suspended: bool = False,
    established: bool = False,
) -> tuple[UserAccount, AnonymousIdentity]:
    ensure_data_dirs(data_dir)
    account = UserAccount(
        id="account-student",
        email="student@example.edu.tw",
        display_name="測試學生",
        email_verified=email_verified,
        student_status_verified=True,
        verified_university="長庚大學",
        verified_department="資訊管理學系",
        community_suspended_until=(NOW + timedelta(hours=1) if suspended else None),
        created_at=NOW - timedelta(days=2 if established else 0, hours=1),
        updated_at=NOW - timedelta(hours=1),
    )
    identity = AnonymousIdentity(
        id="identity-student",
        account_id=account.id,
        display_name=account.display_name,
        access_token_hash=_hash("identity-token"),
        created_at=NOW - timedelta(hours=1),
    )
    save_user_accounts([account], data_dir)
    save_anonymous_identities([identity], data_dir)
    return account, identity


def _seed_private_pair(
    data_dir: Path,
) -> tuple[UserAccount, AnonymousIdentity, UserAccount, AnonymousIdentity]:
    sender, sender_identity = _seed_actor(data_dir, established=True)
    recipient = UserAccount(
        id="account-recipient",
        email="recipient@example.edu.tw",
        display_name="收件學生",
        email_verified=True,
        student_status_verified=True,
        verified_university="長庚大學",
        created_at=NOW - timedelta(days=2),
        updated_at=NOW - timedelta(hours=1),
    )
    recipient_identity = AnonymousIdentity(
        id="identity-recipient",
        account_id=recipient.id,
        display_name=recipient.display_name,
        access_token_hash=_hash("recipient-token"),
        created_at=NOW - timedelta(hours=1),
    )
    save_user_accounts([sender, recipient], data_dir)
    save_anonymous_identities([sender_identity, recipient_identity], data_dir)
    return sender, sender_identity, recipient, recipient_identity


def _private_actor_payload(
    account: UserAccount,
    identity: AnonymousIdentity,
    mutation_id: str,
) -> dict[str, str]:
    return {
        "mutation_id": mutation_id,
        "account_id": account.id,
        "identity_id": identity.id,
        "access_token_hash": identity.access_token_hash,
    }


def _publication(
    account: UserAccount,
    identity: AnonymousIdentity,
    mutation_id: str,
    resource_type: PublicCommunityResourceType,
    content: Any,
) -> PublicCommunityPublicationRequest:
    return PublicCommunityPublicationRequest(
        mutation_id=mutation_id,
        account_id=account.id,
        identity_id=identity.id,
        access_token_hash=identity.access_token_hash,
        resource_type=resource_type,
        content=content.model_dump(mode="json"),
    )


def _question(identifier: str = "question-1") -> CommunityQuestion:
    return CommunityQuestion(
        id=identifier,
        school_name="早稻田大學",
        home_university="長庚大學",
        topic=CommunityTopic.APPLICATION,
        title="交換申請應該怎麼準備",
        body="想請教交換申請文件與校內流程應該如何依序準備。",
        identity_mode=CommunityIdentityMode.ANONYMOUS,
        created_at=NOW,
    )


def _post(identifier: str = "post-1") -> CommunityPost:
    return CommunityPost(
        id=identifier,
        board_id="public-study-abroad",
        board_kind=CommunityBoardKind.PUBLIC_STUDY_ABROAD,
        school_name="公共留學板",
        author_id="placeholder",
        display_name="placeholder",
        title="交換申請流程整理分享",
        body="這篇整理交換申請文件與校內繳交流程，提供同學逐步核對。",
        created_at=NOW,
    )


def test_jsonl_identity_commit_rotates_linked_and_legacy_tokens_and_purges_locally(
    tmp_path: Path,
) -> None:
    account, _ = _seed_actor(tmp_path)
    repository = JsonlCommunityRepository(tmp_path)
    linked_request = CommunityIdentityMutationRequest(
        mutation_id="identity-mutation-0001",
        identity=AnonymousIdentity(
            id="candidate-identity",
            account_id=account.id,
            display_name="不應覆蓋帳號名稱",
            access_token_hash=_hash("linked-rotated-token"),
            created_at=NOW,
        ),
    )

    linked = repository.commit_identity(linked_request, now=NOW)
    replay = repository.commit_identity(linked_request, now=NOW + timedelta(minutes=1))

    assert linked.status == CommunityIdentityMutationStatus.COMMITTED
    assert replay == linked
    assert linked.identity is not None
    assert linked.identity.id == "identity-student"
    assert linked.identity.display_name == account.display_name
    assert linked.identity.access_token_hash == _hash("linked-rotated-token")

    legacy = AnonymousIdentity(
        id="legacy-identity",
        display_name="舊匿名身分",
        access_token_hash=_hash("legacy-original"),
        created_at=NOW - timedelta(days=5),
    )
    save_anonymous_identities(
        [*load_anonymous_identities(tmp_path), legacy],
        tmp_path,
    )
    legacy_request = CommunityIdentityMutationRequest(
        mutation_id="identity-mutation-0002",
        identity=legacy.model_copy(
            update={
                "display_name": "更新匿名身分",
                "access_token_hash": _hash("legacy-rotated"),
            }
        ),
    )
    rotated = repository.commit_identity(legacy_request, now=NOW)

    assert rotated.status == CommunityIdentityMutationStatus.COMMITTED
    assert rotated.identity is not None
    assert rotated.identity.created_at == legacy.created_at
    assert rotated.identity.access_token_hash == _hash("legacy-rotated")
    assert repository.purge_identity("legacy-identity") is True
    assert repository.purge_identity("legacy-identity") is False


def test_jsonl_six_type_publication_is_atomic_idempotent_and_rate_limited(
    tmp_path: Path,
) -> None:
    account, identity = _seed_actor(tmp_path, established=True)
    repository = JsonlCommunityRepository(tmp_path)
    question = _question()
    post = _post()
    commands = [
        _publication(
            account,
            identity,
            "publication-mutation-01",
            PublicCommunityResourceType.QUESTION,
            question,
        ),
        _publication(
            account,
            identity,
            "publication-mutation-02",
            PublicCommunityResourceType.ANSWER,
            CommunityAnswer(
                id="answer-1",
                question_id=question.id,
                body="建議先核對校內公告，再依序準備申請表與推薦文件。",
                created_at=NOW,
            ),
        ),
        _publication(
            account,
            identity,
            "publication-mutation-03",
            PublicCommunityResourceType.POST,
            post,
        ),
        _publication(
            account,
            identity,
            "publication-mutation-04",
            PublicCommunityResourceType.COMMENT,
            CommunityPostComment(
                id="comment-1",
                post_id=post.id,
                author_id="placeholder",
                display_name="placeholder",
                body="謝謝整理，我會照這個順序逐項確認。",
                created_at=NOW,
            ),
        ),
        _publication(
            account,
            identity,
            "publication-mutation-05",
            PublicCommunityResourceType.CHAT,
            PublicChatMessage(
                id="chat-1",
                school_name="早稻田大學",
                author_id="placeholder",
                display_name="placeholder",
                body="有人也在準備交換文件嗎？",
                created_at=NOW,
            ),
        ),
        _publication(
            account,
            identity,
            "publication-mutation-06",
            PublicCommunityResourceType.EXPERIENCE,
            ExperienceSubmission(
                id="experience-1",
                school_name="早稻田大學",
                home_university="長庚大學",
                title="交換申請準備心得",
                summary="我先依校內公告整理文件清單，再逐項確認簽章與紙本繳交期限。",
                exchange_year="2026",
                created_at=NOW,
            ),
        ),
    ]

    results = [
        repository.commit_publication(command, now=NOW + timedelta(seconds=index))
        for index, command in enumerate(commands)
    ]

    assert [result.status for result in results] == [
        PublicCommunityPublicationStatus.COMMITTED
    ] * 6
    assert len(load_community_publish_events(tmp_path)) == 6
    same_semantics_new_resource_id = commands[0].model_copy(
        update={"content": _question("question-generated-again").model_dump(mode="json")}
    )
    replay = repository.commit_publication(
        same_semantics_new_resource_id,
        now=NOW + timedelta(minutes=2),
    )
    assert replay == results[0]
    conflict = repository.commit_publication(
        commands[0].model_copy(
            update={
                "content": _question("question-other").model_copy(
                    update={"title": "相同 key 但不同語意內容"}
                ).model_dump(mode="json")
            }
        ),
        now=NOW,
    )
    assert conflict.status == PublicCommunityPublicationStatus.IDEMPOTENCY_CONFLICT


def test_jsonl_new_account_rate_limit_returns_fixed_retry_after(tmp_path: Path) -> None:
    account, identity = _seed_actor(tmp_path)
    repository = JsonlCommunityRepository(tmp_path)
    results = [
        repository.commit_publication(
            _publication(
                account,
                identity,
                f"rate-limit-mutation-{index}",
                PublicCommunityResourceType.POST,
                _post(f"rate-post-{index}").model_copy(
                    update={"title": f"交換申請流程整理分享第 {index} 篇"}
                ),
            ),
            now=NOW + timedelta(seconds=index),
        )
        for index in range(6)
    ]

    assert [result.status for result in results[:5]] == [
        PublicCommunityPublicationStatus.COMMITTED
    ] * 5
    assert results[5].status == PublicCommunityPublicationStatus.RATE_LIMITED
    assert results[5].retry_after_seconds == 600
    assert len(load_community_publish_events(tmp_path)) == 5


def test_jsonl_email_rules_match_existing_public_community_contract(
    tmp_path: Path,
) -> None:
    account, identity = _seed_actor(tmp_path, email_verified=False)
    repository = JsonlCommunityRepository(tmp_path)

    question = repository.commit_publication(
        _publication(
            account,
            identity,
            "email-contract-question",
            PublicCommunityResourceType.QUESTION,
            _question(),
        ),
        now=NOW,
    )
    chat = repository.commit_publication(
        _publication(
            account,
            identity,
            "email-contract-chat-01",
            PublicCommunityResourceType.CHAT,
            PublicChatMessage(
                id="chat-email-contract",
                school_name="早稻田大學",
                author_id="placeholder",
                display_name="placeholder",
                body="已驗證學生身分但尚未驗證 Email。",
                created_at=NOW,
            ),
        ),
        now=NOW,
    )
    experience = repository.commit_publication(
        _publication(
            account,
            identity,
            "email-contract-experience",
            PublicCommunityResourceType.EXPERIENCE,
            ExperienceSubmission(
                id="experience-email-contract",
                school_name="早稻田大學",
                home_university="長庚大學",
                title="交換申請文件準備經驗",
                summary="這份心得說明我如何依照校內公告整理文件，並逐項完成紙本繳交。",
                exchange_year="2026",
                created_at=NOW,
            ),
        ),
        now=NOW,
    )
    post = repository.commit_publication(
        _publication(
            account,
            identity,
            "email-contract-post-01",
            PublicCommunityResourceType.POST,
            _post(),
        ),
        now=NOW,
    )

    assert question.status == PublicCommunityPublicationStatus.COMMITTED
    assert chat.status == PublicCommunityPublicationStatus.COMMITTED
    assert experience.status == PublicCommunityPublicationStatus.COMMITTED
    assert post.status == PublicCommunityPublicationStatus.EMAIL_UNVERIFIED


def test_jsonl_delete_does_not_recheck_email_and_cascades_post_comments(
    tmp_path: Path,
) -> None:
    account, identity = _seed_actor(tmp_path, email_verified=False)
    repository = JsonlCommunityRepository(tmp_path)
    post = _post()
    post = post.model_copy(update={"author_id": identity.id, "comment_count": 1})
    comment = CommunityPostComment(
        id="delete-comment",
        post_id=post.id,
        author_id=identity.id,
        display_name="匿名學生",
        body="這則留言應隨貼文刪除。",
        created_at=NOW,
    )
    save_community_posts([post], tmp_path)
    repositories.save_community_post_comments([comment], tmp_path)

    result = repository.delete_public_content(
        PublicCommunityDeleteRequest(
            mutation_id="delete-mutation-00001",
            account_id=account.id,
            identity_id=identity.id,
            access_token_hash=identity.access_token_hash,
            resource_type=PublicCommunityResourceType.POST,
            resource_id=post.id,
        ),
        now=NOW,
    )

    assert result.status == PublicCommunityDeleteStatus.COMMITTED
    assert result.deleted_comment_count == 1
    assert load_community_posts(tmp_path) == []
    assert load_community_post_comments(tmp_path) == []


def test_jsonl_moderation_uses_expected_status_cas_and_appends_one_audit(
    tmp_path: Path,
) -> None:
    account, identity = _seed_actor(tmp_path)
    repository = JsonlCommunityRepository(tmp_path)
    post = _post().model_copy(
        update={
            "author_id": identity.id,
            "status": ModerationStatus.PENDING,
        }
    )
    save_community_posts([post], tmp_path)
    request = PublicCommunityModerationRequest(
        mutation_id="moderation-mutation-1",
        moderator_id=account.id,
        resource_type=PublicCommunityResourceType.POST,
        resource_id=post.id,
        expected_status=ModerationStatus.PENDING,
        status=ModerationStatus.APPROVED,
        note="已人工核對內容，可以公開。",
    )

    committed = repository.commit_moderation(request, now=NOW)
    stale = repository.commit_moderation(
        request.model_copy(update={"mutation_id": "moderation-mutation-2"}),
        now=NOW,
    )

    assert committed.status == PublicCommunityModerationStatus.COMMITTED
    assert stale.status == PublicCommunityModerationStatus.STATUS_CONFLICT
    assert len(load_community_moderation_audits(tmp_path)) == 1


def test_jsonl_anonymization_keeps_missing_and_deidentified_author_distinct(
    tmp_path: Path,
) -> None:
    account, identity = _seed_actor(tmp_path)
    repository = JsonlCommunityRepository(tmp_path)
    post = _post().model_copy(update={"author_id": identity.id})
    save_community_posts([post], tmp_path)
    save_community_publish_events(
        [
            CommunityPublishEvent(
                id="rate-event-before-delete",
                account_id=account.id,
                created_at=NOW,
            )
        ],
        tmp_path,
    )

    result = repository.anonymize_public_author(
        PublicAuthorAnonymizationRequest(
            mutation_id="anonymize-mutation-1",
            identity_id=identity.id,
            expected_account_id=account.id,
        ),
        now=NOW,
    )

    assert result.status.value == "committed"
    assert result.counts["publish_event"] == 1
    assert load_community_publish_events(tmp_path) == []
    assert repository.find_public_author(PublicCommunityResourceType.POST, post.id) == ""
    assert repository.find_public_author(PublicCommunityResourceType.POST, "missing") is None
    assert repository.find_identity_by_id(identity.id) is not None


def test_jsonl_private_conversation_and_initial_message_commit_atomically_and_replay(
    tmp_path: Path,
) -> None:
    sender, sender_identity, _, recipient_identity = _seed_private_pair(tmp_path)
    repository = JsonlCommunityRepository(tmp_path)
    conversation = PrivateConversation(
        id="private-conversation-1",
        school_name="林肯大學 Lincoln University",
        sender_id=sender_identity.id,
        sender_name="client supplied",
        recipient_id=recipient_identity.id,
        recipient_name="client supplied",
        created_at=NOW - timedelta(days=1),
        updated_at=NOW - timedelta(days=1),
    )
    message = PrivateMessage(
        id="private-message-1",
        conversation_id=conversation.id,
        author_id=sender_identity.id,
        display_name="client supplied",
        body="想請教住宿申請順序。",
        created_at=NOW - timedelta(days=1),
    )
    request = PrivateConversationMutationRequest(
        **_private_actor_payload(
            sender, sender_identity, "private-conversation-mutation-1"
        ),
        recipient_identity_id=recipient_identity.id,
        conversation=conversation,
        initial_message=message,
    )

    committed = repository.commit_private_conversation(request, now=NOW)
    replay = repository.commit_private_conversation(
        request.model_copy(
            update={
                "conversation": conversation.model_copy(
                    update={
                        "id": "retry-generated-conversation",
                        "sender_name": "retry generated name",
                        "recipient_name": "retry generated recipient",
                        "status": ConversationStatus.ACCEPTED,
                        "created_at": NOW + timedelta(minutes=1),
                        "updated_at": NOW + timedelta(minutes=1),
                    }
                ),
                "initial_message": message.model_copy(
                    update={
                        "id": "retry-generated-message",
                        "conversation_id": "retry-generated-conversation",
                        "display_name": "retry generated display name",
                        "created_at": NOW + timedelta(minutes=1),
                    }
                ),
            }
        ),
        now=NOW + timedelta(minutes=1),
    )
    conflict = repository.commit_private_conversation(
        request.model_copy(
            update={
                "initial_message": message.model_copy(
                    update={"body": "相同 mutation 不同內容。"}
                )
            }
        ),
        now=NOW,
    )

    assert committed.status == PrivateCommunityMutationStatus.COMMITTED
    assert replay == committed
    assert conflict.status == PrivateCommunityMutationStatus.IDEMPOTENCY_CONFLICT
    assert committed.conversation is not None
    assert committed.conversation.sender_name == sender_identity.display_name
    assert committed.conversation.recipient_name == recipient_identity.display_name
    assert committed.message is not None
    assert committed.message.display_name == sender_identity.display_name
    assert load_private_conversations(tmp_path) == [committed.conversation]
    assert load_private_messages(tmp_path) == [committed.message]


def test_jsonl_private_status_cas_and_block_prevent_further_messages(
    tmp_path: Path,
) -> None:
    sender, sender_identity, recipient, recipient_identity = _seed_private_pair(
        tmp_path
    )
    repository = JsonlCommunityRepository(tmp_path)
    conversation = PrivateConversation(
        id="private-conversation-2",
        school_name="林肯大學 Lincoln University",
        sender_id=sender_identity.id,
        sender_name=sender_identity.display_name,
        recipient_id=recipient_identity.id,
        recipient_name=recipient_identity.display_name,
        created_at=NOW,
        updated_at=NOW,
    )
    save_private_conversations([conversation], tmp_path)

    accepted = repository.commit_private_conversation_status(
        PrivateConversationStatusMutationRequest(
            **_private_actor_payload(
                recipient, recipient_identity, "private-accept-mutation-001"
            ),
            conversation_id=conversation.id,
            expected_status=ConversationStatus.PENDING,
            status=ConversationStatus.ACCEPTED,
        ),
        now=NOW + timedelta(seconds=1),
    )
    stale = repository.commit_private_conversation_status(
        PrivateConversationStatusMutationRequest(
            **_private_actor_payload(
                recipient, recipient_identity, "private-accept-mutation-002"
            ),
            conversation_id=conversation.id,
            expected_status=ConversationStatus.PENDING,
            status=ConversationStatus.ACCEPTED,
        ),
        now=NOW + timedelta(seconds=2),
    )
    blocked = repository.commit_block(
        CommunityBlockMutationRequest(
            **_private_actor_payload(
                recipient, recipient_identity, "private-block-mutation-001"
            ),
            block=CommunityBlock(
                id="private-block-1",
                owner_id=recipient_identity.id,
                target_id=sender_identity.id,
                created_at=NOW,
            ),
        ),
        now=NOW + timedelta(seconds=3),
    )
    rejected_message = repository.commit_private_message(
        PrivateMessageMutationRequest(
            **_private_actor_payload(
                sender, sender_identity, "private-message-mutation-001"
            ),
            message=PrivateMessage(
                id="private-message-after-block",
                conversation_id=conversation.id,
                author_id=sender_identity.id,
                display_name=sender_identity.display_name,
                body="這則訊息不能寫入。",
                created_at=NOW,
            ),
        ),
        now=NOW + timedelta(seconds=4),
    )

    assert accepted.status == PrivateCommunityMutationStatus.COMMITTED
    assert stale.status == PrivateCommunityMutationStatus.STATUS_CONFLICT
    assert blocked.status == PrivateCommunityMutationStatus.COMMITTED
    assert rejected_message.status == PrivateCommunityMutationStatus.BLOCKED
    assert load_private_messages(tmp_path) == []


def test_jsonl_report_duplicate_and_review_are_atomic_with_audit(
    tmp_path: Path,
) -> None:
    reporter, reporter_identity, moderator, author_identity = _seed_private_pair(
        tmp_path
    )
    repository = JsonlCommunityRepository(tmp_path)
    post = _post().model_copy(update={"author_id": author_identity.id})
    save_community_posts([post], tmp_path)
    report = CommunityReport(
        id="community-report-1",
        reporter_id=reporter_identity.id,
        resource_type="post",
        resource_id=post.id,
        reason="內容可能使用了過期資訊。",
        created_at=NOW,
    )
    request = CommunityReportMutationRequest(
        **_private_actor_payload(
            reporter, reporter_identity, "community-report-mutation-1"
        ),
        report=report,
    )

    created = repository.commit_report(request, now=NOW)
    duplicate = repository.commit_report(
        request.model_copy(update={"mutation_id": "community-report-mutation-2"}),
        now=NOW + timedelta(seconds=1),
    )
    reviewed = repository.commit_report_review(
        CommunityReportReviewMutationRequest(
            mutation_id="community-report-review-1",
            moderator_id=moderator.id,
            report_id=report.id,
            expected_status=CommunityReportStatus.PENDING,
            status=CommunityReportStatus.RESOLVED,
            note="已核對並隱藏錯誤資訊。",
        ),
        now=NOW + timedelta(seconds=2),
    )
    stale = repository.commit_report_review(
        CommunityReportReviewMutationRequest(
            mutation_id="community-report-review-2",
            moderator_id=moderator.id,
            report_id=report.id,
            expected_status=CommunityReportStatus.PENDING,
            status=CommunityReportStatus.DISMISSED,
            note="這筆 stale 操作不得覆蓋結果。",
        ),
        now=NOW + timedelta(seconds=3),
    )

    assert created.status == PrivateCommunityMutationStatus.COMMITTED
    assert duplicate.report == created.report
    assert reviewed.status == PrivateCommunityMutationStatus.COMMITTED
    assert reviewed.report is not None
    assert reviewed.report.status == CommunityReportStatus.RESOLVED
    assert reviewed.audit is not None
    assert stale.status == PrivateCommunityMutationStatus.STATUS_CONFLICT
    assert len(load_community_moderation_audits(tmp_path)) == 1


def test_jsonl_private_identity_purge_removes_private_content_and_retains_pending_report(
    tmp_path: Path,
) -> None:
    sender, sender_identity, recipient, recipient_identity = _seed_private_pair(
        tmp_path
    )
    repository = JsonlCommunityRepository(tmp_path)
    conversation = PrivateConversation(
        id="private-conversation-delete",
        school_name="林肯大學 Lincoln University",
        sender_id=sender_identity.id,
        sender_name=sender_identity.display_name,
        recipient_id=recipient_identity.id,
        recipient_name=recipient_identity.display_name,
        status=ConversationStatus.ACCEPTED,
        created_at=NOW,
        updated_at=NOW,
    )
    save_private_conversations([conversation], tmp_path)
    save_private_messages(
        [
            PrivateMessage(
                id="private-message-delete",
                conversation_id=conversation.id,
                author_id=sender_identity.id,
                display_name=sender_identity.display_name,
                body="刪帳時必須移除。",
                created_at=NOW,
            )
        ],
        tmp_path,
    )
    block_result = repository.commit_block(
        CommunityBlockMutationRequest(
            **_private_actor_payload(
                recipient, recipient_identity, "block-before-private-purge"
            ),
            block=CommunityBlock(
                id="block-before-delete",
                owner_id=recipient_identity.id,
                target_id=sender_identity.id,
                created_at=NOW,
            ),
        ),
        now=NOW,
    )
    assert block_result.status == PrivateCommunityMutationStatus.COMMITTED
    report = CommunityReport(
        id="pending-report-before-delete",
        reporter_id=sender_identity.id,
        resource_type="message",
        resource_id="private-message-delete",
        reason="需要保留待處理安全檢舉。",
        created_at=NOW,
    )
    repositories.save_community_reports([report], tmp_path)

    purged = repository.purge_private_identity(
        PrivateCommunityIdentityPurgeRequest(
            mutation_id="purge-private-identity-001",
            identity_id=sender_identity.id,
            expected_account_id=sender.id,
        ),
        now=NOW + timedelta(minutes=1),
    )

    assert purged.status == PrivateCommunityMutationStatus.COMMITTED
    assert purged.counts == {
        "conversation": 1,
        "message": 1,
        "block": 1,
        "report_deidentified": 1,
        "report_deleted": 0,
        "report_review_cleared": 0,
    }
    assert repository.list_private_conversations() == []
    assert repository.list_private_messages() == []
    assert repository.list_blocks() == []
    retained_report = repository.list_reports(now=NOW + timedelta(minutes=2))[0]
    assert retained_report.reporter_id == ""
    assert retained_report.retained_until == NOW + timedelta(days=90, minutes=1)


def test_jsonl_locks_every_related_path_in_stable_sorted_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ensure_data_dirs(tmp_path)
    repository = JsonlCommunityRepository(tmp_path)
    entered: list[Path] = []

    @contextmanager
    def tracking_lock(path: Path):
        entered.append(path)
        yield

    monkeypatch.setattr(repositories, "storage_path_lock", tracking_lock)
    with repository._locked_all():
        pass

    assert entered == sorted(
        entered,
        key=lambda path: str(path.absolute()).casefold(),
    )
    assert len(entered) == len(set(entered)) == 17
    assert tmp_path / "processed" / "community_reactions.jsonl" in entered
    assert tmp_path / "processed" / "community_bookmarks.jsonl" in entered


class _FakeResponse:
    def __init__(self, payload: Any) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> Any:
        return self._payload


class _FakeSession:
    def __init__(self, responses: list[Any]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def request(self, method: str, url: str, **kwargs: Any) -> _FakeResponse:
        self.calls.append({"method": method, "url": url, **kwargs})
        return _FakeResponse(self.responses.pop(0))


def _sql_post_row(*, author_identity_id: str | None = "identity-student") -> dict[str, Any]:
    row = _post().model_dump(mode="json")
    row.pop("author_id")
    row.pop("comment_count")
    row.pop("viewer_can_delete")
    row["author_identity_id"] = author_identity_id
    row["revision"] = 4
    row["updated_at"] = NOW.isoformat()
    return row


def test_supabase_reads_translate_real_sql_rows_and_deleted_authors() -> None:
    fake = _FakeSession(
        [
            [_sql_post_row(author_identity_id=None)],
            [{"author_identity_id": None}],
            [],
        ]
    )
    repository = SupabaseCommunityRepository(
        "https://project.supabase.co",
        "service-role-secret",
        session=fake,  # type: ignore[arg-type]
    )

    posts = repository.list_posts()
    deidentified = repository.find_public_author(
        PublicCommunityResourceType.POST,
        "post-1",
    )
    missing = repository.find_public_author(
        PublicCommunityResourceType.POST,
        "missing",
    )

    assert posts[0].author_id == ""
    assert posts[0].comment_count == 0
    assert deidentified == ""
    assert missing is None
    assert "exchange_community_posts" in fake.calls[0]["url"]
    assert fake.calls[1]["params"]["select"] == "author_identity_id"


def test_supabase_each_public_write_is_exactly_one_rpc_and_models_validate() -> None:
    account = UserAccount(
        id="account-student",
        display_name="測試學生",
        email_verified=True,
        created_at=NOW,
        updated_at=NOW,
    )
    identity = AnonymousIdentity(
        id="identity-student",
        account_id=account.id,
        display_name=account.display_name,
        access_token_hash=_hash("identity-token"),
        created_at=NOW,
    )
    post_row = _sql_post_row()
    audit = {
        "id": "moderation-mutation-1",
        "resource_type": "post",
        "resource_id": "post-1",
        "previous_status": "pending",
        "new_status": "approved",
        "moderator_id": account.id,
        "note": "已人工核對內容，可以公開。",
        "created_at": NOW.isoformat(),
        "retained_until": (NOW + timedelta(days=90)).isoformat(),
        "request_fingerprint": _hash("audit"),
    }
    fake = _FakeSession(
        [
            {
                "status": "committed",
                "identity": {
                    "id": identity.id,
                    "account_id": account.id,
                    "display_name": account.display_name,
                    "created_at": NOW.isoformat(),
                    "updated_at": NOW.isoformat(),
                },
            },
            {"status": "committed", "content": post_row},
            {
                "status": "committed",
                "resource_id": "post-1",
                "deleted_comment_count": 2,
            },
            {"status": "committed", "content": post_row, "audit": audit},
            {"status": "committed", "counts": {"post": 1}},
        ]
    )
    repository = SupabaseCommunityRepository(
        "https://project.supabase.co",
        "service-role-secret",
        session=fake,  # type: ignore[arg-type]
    )

    identity_result = repository.commit_identity(
        CommunityIdentityMutationRequest(
            mutation_id="identity-mutation-0001",
            identity=identity,
        )
    )
    publication_result = repository.commit_publication(
        _publication(
            account,
            identity,
            "publication-mutation-01",
            PublicCommunityResourceType.POST,
            _post(),
        )
    )
    delete_result = repository.delete_public_content(
        PublicCommunityDeleteRequest(
            mutation_id="delete-mutation-00001",
            account_id=account.id,
            identity_id=identity.id,
            access_token_hash=identity.access_token_hash,
            resource_type=PublicCommunityResourceType.POST,
            resource_id="post-1",
        )
    )
    moderation_result = repository.commit_moderation(
        PublicCommunityModerationRequest(
            mutation_id="moderation-mutation-1",
            moderator_id=account.id,
            resource_type=PublicCommunityResourceType.POST,
            resource_id="post-1",
            expected_status=ModerationStatus.PENDING,
            status=ModerationStatus.APPROVED,
            note="已人工核對內容，可以公開。",
        )
    )
    anonymized = repository.anonymize_public_author(
        PublicAuthorAnonymizationRequest(
            mutation_id="anonymize-mutation-1",
            identity_id=identity.id,
            expected_account_id=account.id,
        )
    )

    assert identity_result.identity is not None
    assert identity_result.identity.access_token_hash == identity.access_token_hash
    assert publication_result.parsed_content() is not None
    assert publication_result.parsed_content().author_id == identity.id  # type: ignore[union-attr]
    assert delete_result.deleted_comment_count == 2
    assert moderation_result.audit is not None
    assert anonymized.counts == {"post": 1}
    assert len(fake.calls) == 5
    assert all(call["method"] == "POST" and "/rpc/" in call["url"] for call in fake.calls)
    assert [call["url"].rsplit("/", 1)[-1] for call in fake.calls] == [
        "exchange_commit_community_identity",
        "exchange_commit_public_community_publication",
        "exchange_delete_public_community_content",
        "exchange_commit_public_community_moderation",
        "exchange_anonymize_public_community_author",
    ]
    assert [set(call["json"]) for call in fake.calls] == [
        {"p_mutation_id", "p_request_fingerprint", "p_identity"},
        {
            "p_mutation_id",
            "p_request_fingerprint",
            "p_account_id",
            "p_identity_id",
            "p_access_token_hash",
            "p_resource_type",
            "p_content",
        },
        {
            "p_mutation_id",
            "p_request_fingerprint",
            "p_account_id",
            "p_identity_id",
            "p_access_token_hash",
            "p_resource_type",
            "p_resource_id",
        },
        {
            "p_mutation_id",
            "p_request_fingerprint",
            "p_moderator_id",
            "p_resource_type",
            "p_resource_id",
            "p_expected_status",
            "p_status",
            "p_note",
        },
        {
            "p_mutation_id",
            "p_request_fingerprint",
            "p_identity_id",
            "p_expected_account_id",
            "p_replacement_name",
        },
    ]
    assert fake.calls[3]["json"]["p_expected_status"] == "pending"


def test_supabase_each_private_write_is_exactly_one_rpc_and_models_validate() -> None:
    sender = UserAccount(
        id="account-student",
        display_name="測試學生",
        created_at=NOW,
        updated_at=NOW,
    )
    sender_identity = AnonymousIdentity(
        id="identity-student",
        account_id=sender.id,
        display_name=sender.display_name,
        access_token_hash=_hash("identity-token"),
        created_at=NOW,
    )
    recipient = UserAccount(
        id="account-recipient",
        display_name="收件學生",
        created_at=NOW,
        updated_at=NOW,
    )
    recipient_identity = AnonymousIdentity(
        id="identity-recipient",
        account_id=recipient.id,
        display_name=recipient.display_name,
        access_token_hash=_hash("recipient-token"),
        created_at=NOW,
    )
    conversation = PrivateConversation(
        id="private-conversation-sql",
        school_name="林肯大學 Lincoln University",
        sender_id=sender_identity.id,
        sender_name=sender_identity.display_name,
        recipient_id=recipient_identity.id,
        recipient_name=recipient_identity.display_name,
        created_at=NOW,
        updated_at=NOW,
    )
    accepted_conversation = conversation.model_copy(
        update={"status": ConversationStatus.ACCEPTED}
    )
    message = PrivateMessage(
        id="private-message-sql",
        conversation_id=conversation.id,
        author_id=sender_identity.id,
        display_name=sender_identity.display_name,
        body="想請教住宿申請順序。",
        created_at=NOW,
    )
    block = CommunityBlock(
        id="private-block-sql",
        owner_id=recipient_identity.id,
        target_id=sender_identity.id,
        created_at=NOW,
    )
    report = CommunityReport(
        id="private-report-sql",
        reporter_id=sender_identity.id,
        resource_type="post",
        resource_id="post-1",
        reason="內容可能含有過期資訊。",
        created_at=NOW,
    )
    resolved_report = report.model_copy(
        update={
            "status": CommunityReportStatus.RESOLVED,
            "reviewed_by": recipient.id,
            "reviewed_at": NOW,
            "resolution_note": "已完成來源核對。",
        }
    )
    audit = {
        "id": "private-report-review-1",
        "resource_type": "report",
        "resource_id": report.id,
        "previous_status": "pending",
        "new_status": "resolved",
        "moderator_id": recipient.id,
        "note": "已完成來源核對。",
        "created_at": NOW.isoformat(),
        "retained_until": (NOW + timedelta(days=90)).isoformat(),
    }
    fake = _FakeSession(
        [
            {
                "status": "committed",
                "conversation": conversation.model_dump(mode="json"),
                "message": message.model_dump(mode="json"),
            },
            {
                "status": "committed",
                "conversation": accepted_conversation.model_dump(mode="json"),
            },
            {
                "status": "committed",
                "conversation": accepted_conversation.model_dump(mode="json"),
                "message": message.model_dump(mode="json"),
            },
            {"status": "committed", "block": block.model_dump(mode="json")},
            {"status": "committed", "report": report.model_dump(mode="json")},
            {
                "status": "committed",
                "report": resolved_report.model_dump(mode="json"),
                "audit": audit,
            },
            {
                "status": "committed",
                "counts": {
                    "conversation": 1,
                    "message": 2,
                    "block": 1,
                    "report_deidentified": 1,
                    "report_deleted": 0,
                    "report_review_cleared": 0,
                },
            },
        ]
    )
    repository = SupabaseCommunityRepository(
        "https://project.supabase.co",
        "service-role-secret",
        session=fake,  # type: ignore[arg-type]
    )

    conversation_result = repository.commit_private_conversation(
        PrivateConversationMutationRequest(
            **_private_actor_payload(
                sender, sender_identity, "private-conversation-rpc-1"
            ),
            recipient_identity_id=recipient_identity.id,
            conversation=conversation,
            initial_message=message,
        )
    )
    status_result = repository.commit_private_conversation_status(
        PrivateConversationStatusMutationRequest(
            **_private_actor_payload(
                recipient, recipient_identity, "private-status-rpc-00001"
            ),
            conversation_id=conversation.id,
            expected_status=ConversationStatus.PENDING,
            status=ConversationStatus.ACCEPTED,
        )
    )
    message_result = repository.commit_private_message(
        PrivateMessageMutationRequest(
            **_private_actor_payload(sender, sender_identity, "private-message-rpc-001"),
            message=message,
        )
    )
    block_result = repository.commit_block(
        CommunityBlockMutationRequest(
            **_private_actor_payload(
                recipient, recipient_identity, "private-block-rpc-00001"
            ),
            block=block,
        )
    )
    report_result = repository.commit_report(
        CommunityReportMutationRequest(
            **_private_actor_payload(sender, sender_identity, "private-report-rpc-0001"),
            report=report,
        )
    )
    review_result = repository.commit_report_review(
        CommunityReportReviewMutationRequest(
            mutation_id="private-report-review-1",
            moderator_id=recipient.id,
            report_id=report.id,
            expected_status=CommunityReportStatus.PENDING,
            status=CommunityReportStatus.RESOLVED,
            note="已完成來源核對。",
        )
    )
    purge_result = repository.purge_private_identity(
        PrivateCommunityIdentityPurgeRequest(
            mutation_id="private-identity-purge-rpc-1",
            identity_id=sender_identity.id,
            expected_account_id=sender.id,
        )
    )

    assert conversation_result.conversation == conversation
    assert status_result.conversation == accepted_conversation
    assert message_result.message == message
    assert block_result.block == block
    assert report_result.report == report
    assert review_result.report == resolved_report
    assert review_result.audit is not None
    assert purge_result.counts["message"] == 2
    assert len(fake.calls) == 7
    assert [call["url"].rsplit("/", 1)[-1] for call in fake.calls] == [
        "exchange_commit_private_community_conversation",
        "exchange_commit_private_community_conversation_status",
        "exchange_commit_private_community_message",
        "exchange_commit_private_community_block",
        "exchange_commit_private_community_report",
        "exchange_commit_private_community_report_review",
        "exchange_purge_private_community_identity",
    ]
    assert all(call["method"] == "POST" for call in fake.calls)


def test_factory_fails_closed_for_jsonl_in_production(tmp_path: Path) -> None:
    with pytest.raises(CommunityRepositoryError, match="正式環境禁止"):
        create_community_repository(
            tmp_path,
            {
                "EXCHANGE_ENVIRONMENT": "production",
                "EXCHANGE_COMMUNITY_REPOSITORY": "jsonl",
            },
        )
