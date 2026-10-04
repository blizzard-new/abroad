from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.content_governance import (
    LocalContentGovernanceStore,
    approve_workflow_revision,
    publish_workflow_revision,
    rollback_published_workflow,
    stage_existing_workflow_for_review,
    stage_workflow_refresh,
    workflow_content_hash,
    workflow_review_rule_keys,
    workflow_review_source_urls,
    workflow_storage_key,
)
from exchange_info.models import (
    AccountApplicationWorkspace,
    AccountCalendarEvent,
    AccountNotificationPreferences,
    AccountSessionRecord,
    AccountSubmissionProgress,
    ApplicationCenterContext,
    ApplicationRuleScope,
    ApplicationSourceAuthority,
    ApplicationSourceRole,
    ApplicationStep,
    ApplicationSubmissionMethod,
    ApplicationWorkflowReviewStatus,
    ApplicationWorkflowRollbackRequest,
    ApplicationWorkflowRevision,
    ApplicationWorkflowSource,
    UniversityApplicationWorkflow,
    UserAccount,
    utc_now,
)
from exchange_info.notifications import NotificationService
from exchange_info.repositories import JsonlAccountRepository


TAIPEI = ZoneInfo("Asia/Taipei")


def _paper_account(
    deadline: datetime,
    *,
    reminder_days: list[int] | None = None,
    web_enabled: bool = True,
    email_enabled: bool = False,
) -> UserAccount:
    progress = AccountSubmissionProgress(
        title="紙本交換申請",
        method=ApplicationSubmissionMethod.PAPER,
        status="preparing",
        responsible_unit="國際事務處",
        send_by_at=deadline - timedelta(days=4),
        arrival_deadline_at=deadline,
    )
    workspace = AccountApplicationWorkspace(
        home_school="長庚大學",
        application_context=ApplicationCenterContext(school_name="長庚大學"),
        submission_progress={"paper-application": progress},
    )
    return UserAccount(
        email="student@example.com",
        display_name="提醒測試",
        application_workspaces=[workspace],
        notification_preferences=AccountNotificationPreferences(
            deadline_reminder_days=reminder_days or [30, 14, 7, 3, 1],
            web_enabled=web_enabled,
            email_enabled=email_enabled,
        ),
    )


def _content_workflow(
    title: str,
    *,
    version: int,
    department: str | None = "資訊工程學系",
    college: str | None = None,
) -> UniversityApplicationWorkflow:
    return UniversityApplicationWorkflow(
        workflow_id="lincoln-workflow",
        home_university="長庚大學",
        school_name="林肯大學 Lincoln University",
        partner_website="https://www.lincoln.ac.nz/study/exchange/",
        program_type="exchange",
        academic_year="116",
        application_round="第一梯次",
        effective_application_rounds=["第一梯次"],
        applicability_status="verified",
        version=version,
        review_status=ApplicationWorkflowReviewStatus.PUBLISHED,
        steps=[
            ApplicationStep(
                rule_id="eligibility",
                order=1,
                phase="校內準備",
                title=title,
                responsible_party="學生",
                summary="核對資格與申請文件。",
                source_urls=[
                    "https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554"
                ],
                scope=ApplicationRuleScope(
                    colleges=[college] if college else [],
                    departments=[department] if department else [],
                ),
                checked_at=datetime(2026, 8, 1, tzinfo=timezone.utc),
            )
        ],
        sources=[
            ApplicationWorkflowSource(
                title="長庚大學交換學生公告",
                source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
                role=ApplicationSourceRole.HOME_UNIVERSITY,
                authority=ApplicationSourceAuthority.HOME_OFFICIAL_NOTICE,
                priority=1,
                effective_academic_year="116",
                application_round="第一梯次",
                checked_at=datetime(2026, 8, 1, tzinfo=timezone.utc),
            )
        ],
        last_checked=datetime(2026, 8, 1, tzinfo=timezone.utc),
        coverage_status="official_verified",
    )


def _content_account(
    *,
    home_school: str = "長庚大學",
    partner: str = "林肯大學 Lincoln University",
    academic_year: str = "116",
    application_round: str = "第一梯次",
    department: str | None = "資訊工程學系",
    college: str | None = "工學院",
    student_verified: bool = True,
    content_updates_enabled: bool = True,
    email_enabled: bool = False,
) -> UserAccount:
    workspace = AccountApplicationWorkspace(
        home_school=home_school,
        application_schools=[partner],
        application_context=ApplicationCenterContext(
            school_name=home_school,
            target_school=partner,
            academic_year=academic_year,
            semester=application_round,
            college=college or "",
            department=department or "",
        ),
    )
    return UserAccount(
        email=f"student-{hash((home_school, partner, academic_year, application_round, college, department, student_verified))}@example.com",
        display_name="內容更新測試",
        home_university=home_school,
        verified_university=home_school,
        verified_department=department if student_verified else None,
        student_status_verified=student_verified,
        application_workspaces=[workspace],
        notification_preferences=AccountNotificationPreferences(
            web_enabled=True,
            email_enabled=email_enabled,
            content_updates_enabled=content_updates_enabled,
        ),
    )


def _published_content_store(
    tmp_path,
    *,
    department: str | None = "資訊工程學系",
    college: str | None = None,
) -> tuple[
    LocalContentGovernanceStore,
    ApplicationWorkflowRevision,
]:
    store = LocalContentGovernanceStore(tmp_path)
    base = _content_workflow(
        "舊版資格",
        version=1,
        department=department,
        college=college,
    )
    changed = _content_workflow(
        "新版資格與文件",
        version=2,
        department=department,
        college=college,
    )
    baseline = ApplicationWorkflowRevision(
        workflow_key="lincoln-workflow",
        version=1,
        status=ApplicationWorkflowReviewStatus.SUPERSEDED,
        content_hash=workflow_content_hash(base),
        workflow=base,
        reviewed_by="legacy_import",
        reviewed_at=utc_now() - timedelta(days=1),
    )
    published = ApplicationWorkflowRevision(
        workflow_key="lincoln-workflow",
        version=2,
        base_version=1,
        status=ApplicationWorkflowReviewStatus.PUBLISHED,
        content_hash=workflow_content_hash(changed),
        change_summary=["調整資格門檻", "新增文件要求"],
        workflow=changed,
        reviewed_by="content-admin",
        reviewed_at=utc_now(),
        review_note="已核對正式公告。",
    )
    store.save_revision(baseline)
    store.save_revision(published)
    return store, published


def test_five_default_deadline_nodes_are_idempotent(tmp_path) -> None:
    repository = JsonlAccountRepository(tmp_path)
    deadline = datetime(2026, 10, 1, 16, 30, tzinfo=TAIPEI)
    account = _paper_account(deadline)
    repository.save_account(account)
    service = NotificationService(repository)

    for days in [30, 14, 7, 3, 1]:
        now = deadline - timedelta(days=days)
        assert service.refresh_account(account, now) == (1, 0)
        assert service.refresh_account(account, now) == (0, 0)

    notifications = repository.list_notifications(account.id)
    assert {row.reminder_days for row in notifications} == {30, 14, 7, 3, 1}
    assert len(notifications) == 5


def test_paper_reminder_uses_arrival_deadline_not_send_by_date(tmp_path) -> None:
    repository = JsonlAccountRepository(tmp_path)
    deadline = datetime(2026, 10, 1, 0, 30, tzinfo=TAIPEI)
    account = _paper_account(deadline, reminder_days=[7])
    repository.save_account(account)
    service = NotificationService(repository)
    now = datetime(2026, 9, 23, 16, 30, tzinfo=timezone.utc)

    created, _ = service.refresh_account(account, now)

    assert created == 1
    notification = repository.list_notifications(account.id)[0]
    assert notification.reminder_days == 7
    assert notification.deadline_at == deadline
    assert "必須送達" in notification.body
    assert "國際事務處" in notification.body
    assert "days-3" not in notification.dedupe_key


def test_deadline_reminders_can_be_customized_or_fully_disabled(tmp_path) -> None:
    repository = JsonlAccountRepository(tmp_path)
    deadline = datetime(2026, 10, 1, 16, 30, tzinfo=TAIPEI)
    custom = _paper_account(deadline, reminder_days=[14, 3])
    disabled = _paper_account(
        deadline,
        reminder_days=[14, 3],
        web_enabled=False,
        email_enabled=False,
    )
    repository.save_account(custom)
    repository.save_account(disabled)
    service = NotificationService(repository)

    assert service.refresh_account(custom, deadline - timedelta(days=14)) == (1, 0)
    assert service.refresh_account(custom, deadline - timedelta(days=7)) == (0, 0)
    assert service.refresh_account(custom, deadline - timedelta(days=3)) == (1, 0)
    assert service.refresh_account(disabled, deadline - timedelta(days=14)) == (0, 0)

    assert {
        row.reminder_days for row in repository.list_notifications(custom.id)
    } == {14, 3}
    assert repository.list_notifications(disabled.id) == []


def _calendar_task_account(
    deadline: datetime,
    *,
    preparation_days: int,
    status: str = "todo",
    reminder_days: int = 7,
) -> UserAccount:
    event = AccountCalendarEvent(
        id="personal-task",
        title="完成讀書計畫",
        date=deadline.astimezone(TAIPEI).date().isoformat(),
        school_name="林肯大學 Lincoln University",
        reminder_days=reminder_days,
        preparation_days=preparation_days,
        status=status,
        origin="personal",
    )
    workspace = AccountApplicationWorkspace(
        home_school="長庚大學",
        application_context=ApplicationCenterContext(school_name="長庚大學"),
        deadline_events=[event],
    )
    return UserAccount(
        email="calendar-task@example.com",
        display_name="智慧提醒測試",
        application_workspaces=[workspace],
        notification_preferences=AccountNotificationPreferences(
            deadline_reminder_days=[30, 14, 7, 3, 1],
            web_enabled=True,
        ),
    )


def test_smart_reminder_uses_user_estimated_start_and_stops_when_ready(
    tmp_path,
) -> None:
    repository = JsonlAccountRepository(tmp_path)
    current = datetime(2027, 5, 1, 9, 0, tzinfo=TAIPEI)
    deadline = current + timedelta(days=10)
    active = _calendar_task_account(deadline, preparation_days=10)
    repository.save_account(active)
    service = NotificationService(repository)

    assert service.refresh_account(active, current) == (1, 0)
    notification = repository.list_notifications(active.id)[0]
    assert notification.source_key == "calendar-start:personal-task"
    assert notification.reminder_days == 0
    assert notification.action_url == "/#calendar"
    assert "建議開始準備日" in notification.body

    completed = active.model_copy(
        update={
            "application_workspaces": [
                active.application_workspaces[0].model_copy(
                    update={
                        "deadline_events": [
                            active.application_workspaces[0].deadline_events[0].model_copy(
                                update={"status": "ready"}
                            )
                        ]
                    }
                )
            ]
        }
    )
    repository.save_account(completed)
    assert service.due_notifications(completed, current) == []


def test_personal_calendar_task_uses_its_own_reminder_offset(tmp_path) -> None:
    repository = JsonlAccountRepository(tmp_path)
    deadline = datetime(2027, 6, 15, 23, 59, tzinfo=TAIPEI)
    account = _calendar_task_account(
        deadline,
        preparation_days=0,
        reminder_days=14,
    )
    repository.save_account(account)

    created, _ = NotificationService(repository).refresh_account(
        account,
        deadline - timedelta(days=14),
    )

    assert created == 1
    assert repository.list_notifications(account.id)[0].reminder_days == 14


def test_public_free_account_does_not_receive_smart_start_reminder(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("EXCHANGE_PRODUCT_RELEASE_MODE", "public")
    repository = JsonlAccountRepository(tmp_path)
    current = datetime(2027, 5, 1, 9, 0, tzinfo=TAIPEI)
    account = _calendar_task_account(
        current + timedelta(days=10),
        preparation_days=10,
    )
    repository.save_account(account)

    assert NotificationService(repository).due_notifications(account, current) == []


def test_email_is_not_queued_without_account_opt_in(tmp_path) -> None:
    repository = JsonlAccountRepository(tmp_path)
    deadline = datetime(2026, 10, 1, 16, 30, tzinfo=TAIPEI)
    account = _paper_account(deadline, reminder_days=[7], email_enabled=False)
    repository.save_account(account)
    service = NotificationService(repository)

    assert service.refresh_account(account, deadline - timedelta(days=7)) == (1, 0)
    assert repository.list_due_deliveries(deadline) == []


class _FailOnceSender:
    def __init__(self) -> None:
        self.calls = 0

    def send(self, recipient: str, subject: str, body: str) -> None:
        self.calls += 1
        assert recipient == "student@example.com"
        assert "紙本交換申請" in subject
        if self.calls == 1:
            raise ConnectionError("provider unavailable")


class _AlwaysFailSender:
    def send(self, recipient: str, subject: str, body: str) -> None:
        raise TimeoutError("provider included a private diagnostic")


def test_email_failure_retries_without_storing_raw_error(tmp_path) -> None:
    repository = JsonlAccountRepository(tmp_path)
    deadline = datetime(2026, 10, 1, 16, 30, tzinfo=TAIPEI)
    account = _paper_account(deadline, reminder_days=[7], email_enabled=True)
    repository.save_account(account)
    sender = _FailOnceSender()
    service = NotificationService(repository, email_sender=sender)
    now = deadline - timedelta(days=7)

    first = service.run_due(now)

    assert first.created_count == 1
    assert first.queued_email_count == 1
    assert first.retry_count == 1
    notification = repository.list_notifications(account.id)[0]
    delivery = repository.find_delivery(notification.id, "email")
    assert delivery is not None
    assert delivery.status == "retrying"
    assert delivery.attempt_count == 1
    assert delivery.last_error_code == "ConnectionError"
    assert "provider unavailable" not in delivery.model_dump_json()

    second = service.run_due(delivery.next_attempt_at)

    assert second.created_count == 0
    assert second.queued_email_count == 0
    assert second.sent_count == 1
    sent = repository.find_delivery(notification.id, "email")
    assert sent is not None
    assert sent.status == "sent"
    assert sent.sent_at == delivery.next_attempt_at


def test_email_stops_after_four_failed_attempts(tmp_path) -> None:
    repository = JsonlAccountRepository(tmp_path)
    deadline = datetime(2026, 10, 1, 16, 30, tzinfo=TAIPEI)
    account = _paper_account(deadline, reminder_days=[7], email_enabled=True)
    repository.save_account(account)
    service = NotificationService(repository, email_sender=_AlwaysFailSender())
    current = deadline - timedelta(days=7)

    first = service.run_due(current)
    assert first.retry_count == 1
    notification = repository.list_notifications(account.id)[0]

    for expected_attempt in (2, 3, 4):
        pending = repository.find_delivery(notification.id, "email")
        assert pending is not None
        current = pending.next_attempt_at
        sent, retrying, failed = service.dispatch_due_emails(current)
        assert sent == 0
        assert retrying == int(expected_attempt < 4)
        assert failed == int(expected_attempt == 4)

    exhausted = repository.find_delivery(notification.id, "email")
    assert exhausted is not None
    assert exhausted.status == "failed"
    assert exhausted.attempt_count == 4
    assert exhausted.last_error_code == "TimeoutError"
    assert "private diagnostic" not in exhausted.model_dump_json()
    assert repository.list_due_deliveries(exhausted.next_attempt_at) == []


def test_pending_email_is_cancelled_after_user_opt_out(tmp_path) -> None:
    repository = JsonlAccountRepository(tmp_path)
    deadline = datetime(2026, 10, 1, 16, 30, tzinfo=TAIPEI)
    account = _paper_account(deadline, reminder_days=[7], email_enabled=True)
    repository.save_account(account)
    now = deadline - timedelta(days=7)
    service = NotificationService(repository, email_sender=_FailOnceSender())
    assert service.refresh_account(account, now) == (1, 1)
    notification = repository.list_notifications(account.id)[0]

    opted_out = account.model_copy(
        update={
            "notification_preferences": account.notification_preferences.model_copy(
                update={"email_enabled": False}
            )
        }
    )
    repository.save_account(opted_out)
    assert service.dispatch_due_emails(now) == (0, 0, 0)

    delivery = repository.find_delivery(notification.id, "email")
    assert delivery is not None
    assert delivery.status == "cancelled"


def test_content_update_targets_only_matching_established_plan(tmp_path) -> None:
    repository = JsonlAccountRepository(tmp_path / "accounts")
    store, published = _published_content_store(tmp_path / "content")
    affected = _content_account()
    unrelated = [
        _content_account(home_school="臺北大學"),
        _content_account(partner="坎特伯雷大學 University of Canterbury"),
        _content_account(academic_year="117"),
        _content_account(application_round="第二梯次"),
        _content_account(department="護理學系"),
        _content_account(content_updates_enabled=False),
    ]
    for account in [affected, *unrelated]:
        repository.save_account(account)
    service = NotificationService(repository, content_store=store)

    assert service.refresh_content_updates() == (1, 0)
    assert service.refresh_content_updates() == (0, 0)

    notification = repository.list_notifications(affected.id)[0]
    assert notification.kind == "content_update"
    assert notification.dedupe_key == f"content-update:{published.id}"
    assert "第 1 版更新為第 2 版" in notification.body
    assert "調整資格門檻；新增文件要求" in notification.body
    assert "116、第一梯次" in notification.body
    assert notification.source_url == (
        "https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554"
    )
    from urllib.parse import parse_qs, urlparse, unquote
    target=urlparse(notification.action_url)
    assert parse_qs(target.query)['home']==["長庚大學"]
    assert unquote(target.fragment)==f"school={published.workflow.school_name}"
    assert all(repository.list_notifications(account.id) == [] for account in unrelated)


def test_content_update_uses_saved_plan_department_without_student_verification(
    tmp_path,
) -> None:
    repository = JsonlAccountRepository(tmp_path / "accounts")
    store, _ = _published_content_store(tmp_path / "content")
    affected = _content_account(student_verified=False)
    unrelated = _content_account(
        department="護理學系",
        college="醫學院",
        student_verified=False,
    )
    repository.save_account(affected)
    repository.save_account(unrelated)

    created, _ = NotificationService(
        repository,
        content_store=store,
    ).refresh_content_updates()

    assert created == 1
    assert len(repository.list_notifications(affected.id)) == 1
    assert repository.list_notifications(unrelated.id) == []


def test_content_update_matches_college_scoped_rule_to_saved_plan(tmp_path) -> None:
    repository = JsonlAccountRepository(tmp_path / "accounts")
    store, _ = _published_content_store(
        tmp_path / "content",
        department=None,
        college="工學院",
    )
    affected = _content_account(department="電機工程學系", college="工學院")
    unrelated = [
        _content_account(department="護理學系", college="醫學院"),
        _content_account(department="電機工程學系", college=None),
    ]
    for account in [affected, *unrelated]:
        repository.save_account(account)

    created, _ = NotificationService(
        repository,
        content_store=store,
    ).refresh_content_updates()

    assert created == 1
    assert len(repository.list_notifications(affected.id)) == 1
    assert all(repository.list_notifications(account.id) == [] for account in unrelated)


class _RecordingSender:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str, str]] = []

    def send(self, recipient: str, subject: str, body: str) -> None:
        self.messages.append((recipient, subject, body))


def test_content_update_email_is_opt_in_idempotent_and_includes_source(tmp_path) -> None:
    repository = JsonlAccountRepository(tmp_path / "accounts")
    store, _ = _published_content_store(tmp_path / "content")
    account = _content_account(email_enabled=True)
    repository.save_account(account)
    sender = _RecordingSender()
    service = NotificationService(
        repository,
        email_sender=sender,
        content_store=store,
    )

    first = service.run_due()
    second = service.run_due()

    assert first.created_count == 1
    assert first.queued_email_count == 1
    assert first.sent_count == 1
    assert second.created_count == 0
    assert second.queued_email_count == 0
    assert second.sent_count == 0
    assert len(sender.messages) == 1
    assert "申請規定已更新" in sender.messages[0][1]
    assert "官方來源：https://www.cgu.edu.tw" in sender.messages[0][2]


def test_content_update_email_is_cancelled_when_plan_no_longer_matches(tmp_path) -> None:
    repository = JsonlAccountRepository(tmp_path / "accounts")
    store, _ = _published_content_store(tmp_path / "content")
    account = _content_account(email_enabled=True)
    repository.save_account(account)
    service = NotificationService(
        repository,
        email_sender=_RecordingSender(),
        content_store=store,
    )
    assert service.refresh_content_updates() == (1, 1)
    notification = repository.list_notifications(account.id)[0]

    repository.save_account(account.model_copy(update={"application_workspaces": []}))
    assert service.dispatch_due_emails() == (0, 0, 0)

    delivery = repository.find_delivery(notification.id, "email")
    assert delivery is not None
    assert delivery.status == "cancelled"


def test_safe_workflow_rollback_notifies_only_affected_saved_plan(tmp_path) -> None:
    repository = JsonlAccountRepository(tmp_path / "accounts")
    store = LocalContentGovernanceStore(tmp_path / "content")
    affected = _content_account()
    unrelated = _content_account(department="護理學系")
    repository.save_account(affected)
    repository.save_account(unrelated)

    def approved_publication(title: str, first_reviewer: str, second_reviewer: str):
        staged = stage_workflow_refresh(
            store,
            _content_workflow(title, version=1),
            detected_by=first_reviewer,
        ).revision
        assert staged is not None
        for reviewer in (first_reviewer, second_reviewer):
            approve_workflow_revision(
                store,
                staged.id,
                reviewer_id=reviewer,
                note=f"{reviewer} 已逐頁核對全部來源與規定。",
                expected_content_hash=staged.content_hash,
                reviewed_source_urls=workflow_review_source_urls(staged.workflow),
                reviewed_rule_keys=workflow_review_rule_keys(staged.workflow),
            )
        publish_workflow_revision(
            store,
            staged.id,
            reviewer_id=second_reviewer,
            note="雙人審查完成，正式發布。",
        )
        return staged

    first = approved_publication("先前正確版本", "admin-a", "admin-b")
    second = approved_publication("誤發布版本", "admin-a", "admin-b")
    rollback = rollback_published_workflow(
        store,
        ApplicationWorkflowRollbackRequest(
            workflow_key=second.workflow_key,
            expected_current_revision_id=second.id,
            expected_current_version=second.version,
            expected_current_content_hash=second.content_hash,
            restore_revision_id=first.id,
            note="目前版本內容有重大疑義，立即恢復先前完整雙審版本。",
        ),
        rolled_back_by="emergency-admin",
    )

    service = NotificationService(repository, content_store=store)
    assert service.refresh_content_updates() == (1, 0)
    assert service.refresh_content_updates() == (0, 0)
    notifications = repository.list_notifications(affected.id)
    assert len(notifications) == 1
    assert notifications[0].dedupe_key == f"content-update:{rollback.id}"
    assert rollback.change_summary[0] in notifications[0].body
    assert "第 2 版更新為第 3 版" in notifications[0].body
    assert repository.list_notifications(unrelated.id) == []


def test_pending_or_rejected_revision_never_creates_content_notification(
    tmp_path,
) -> None:
    repository = JsonlAccountRepository(tmp_path / "accounts")
    store, published = _published_content_store(tmp_path / "content")
    account = _content_account()
    repository.save_account(account)
    service = NotificationService(repository, content_store=store)

    store.save_revision(
        published.model_copy(
            update={
                "status": ApplicationWorkflowReviewStatus.PENDING_REVIEW,
                "reviewed_by": None,
                "reviewed_at": None,
            }
        )
    )
    assert service.refresh_content_updates() == (0, 0)
    store.save_revision(
        published.model_copy(update={"status": ApplicationWorkflowReviewStatus.REJECTED})
    )
    assert service.refresh_content_updates() == (0, 0)
    store.save_revision(
        published.model_copy(update={"status": ApplicationWorkflowReviewStatus.SUPERSEDED})
    )
    assert service.refresh_content_updates() == (0, 0)
    store.save_revision(
        published.model_copy(
            update={
                "status": ApplicationWorkflowReviewStatus.PUBLISHED,
                "reviewed_by": None,
                "reviewed_at": None,
            }
        )
    )
    assert service.refresh_content_updates() == (0, 0)
    assert repository.list_notifications(account.id) == []


def test_admin_publish_immediately_creates_one_content_update_notification(
    tmp_path, monkeypatch
) -> None:
    app_data = tmp_path / "app-data"
    repository = JsonlAccountRepository(tmp_path / "accounts")
    content_store = LocalContentGovernanceStore(app_data)
    base = _content_workflow("已發布舊版", version=1)
    content_store.publish_workflow(base, "baseline")
    staged = stage_workflow_refresh(
        content_store,
        _content_workflow("人工核對新版", version=1),
        detected_by="collector",
    )
    assert staged.revision is not None

    admin = UserAccount(email="admin@example.com", display_name="內容審查者 A")
    second_admin = UserAccount(
        email="second-admin@example.com", display_name="內容審查者 B"
    )
    student = _content_account()
    unrelated = _content_account(department="護理學系")
    token = "content-publish-admin-token"
    second_token = "content-publish-second-admin-token"
    for account in (admin, second_admin, student, unrelated):
        repository.save_account(account)
    repository.save_session(
        AccountSessionRecord(
            account_id=admin.id,
            token_hash=hashlib.sha256(token.encode("utf-8")).hexdigest(),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
    )
    repository.save_session(
        AccountSessionRecord(
            account_id=second_admin.id,
            token_hash=hashlib.sha256(second_token.encode("utf-8")).hexdigest(),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
    )
    monkeypatch.setenv(
        "EXCHANGE_CONTENT_ADMIN_EMAILS",
        f"{admin.email},{second_admin.email}",
    )
    client = TestClient(create_app(app_data, account_repository=repository))

    assert repository.list_notifications(student.id) == []
    first_approval = client.post(
        f"/admin/application-workflow-revisions/{staged.revision.id}/approve",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "expected_content_hash": staged.revision.content_hash,
            "reviewed_source_urls": workflow_review_source_urls(
                staged.revision.workflow
            ),
            "reviewed_rule_keys": workflow_review_rule_keys(
                staged.revision.workflow
            ),
            "note": "已核對當期正式簡章與來源。",
        },
    )
    assert first_approval.status_code == 200
    second_approval = client.post(
        f"/admin/application-workflow-revisions/{staged.revision.id}/approve",
        headers={"Authorization": f"Bearer {second_token}"},
        json={
            "expected_content_hash": staged.revision.content_hash,
            "reviewed_source_urls": workflow_review_source_urls(
                staged.revision.workflow
            ),
            "reviewed_rule_keys": workflow_review_rule_keys(
                staged.revision.workflow
            ),
            "note": "已獨立複核年度、文件與期限。",
        },
    )
    assert second_approval.status_code == 200
    assert repository.list_notifications(student.id) == []
    response = client.post(
        f"/admin/application-workflow-revisions/{staged.revision.id}/publish",
        headers={"Authorization": f"Bearer {second_token}"},
        json={"note": "雙審完成，正式發布。"},
    )

    assert response.status_code == 200
    assert len(repository.list_notifications(student.id)) == 1
    assert repository.list_notifications(unrelated.id) == []
    assert (
        client.post(
            f"/admin/application-workflow-revisions/{staged.revision.id}/publish",
            headers={"Authorization": f"Bearer {second_token}"},
            json={"note": "重複發布"},
        ).status_code
        == 409
    )
    assert len(repository.list_notifications(student.id)) == 1


def test_dual_review_formalization_with_identical_content_sends_no_update(
    tmp_path,
) -> None:
    repository = JsonlAccountRepository(tmp_path / "accounts")
    store = LocalContentGovernanceStore(tmp_path / "content")
    legacy = _content_workflow("既有流程", version=1).model_copy(
        update={
            "review_status": ApplicationWorkflowReviewStatus.LEGACY,
            "published_at": None,
        }
    )
    store.publish_workflow(legacy, "legacy-import")
    account = _content_account()
    repository.save_account(account)
    staged = stage_existing_workflow_for_review(
        store,
        workflow_storage_key(legacy),
        detected_by="admin-1",
    )
    approve_workflow_revision(
        store,
        staged.id,
        reviewer_id="admin-1",
        note="已核對既有內容。",
        expected_content_hash=staged.content_hash,
        reviewed_source_urls=workflow_review_source_urls(staged.workflow),
        reviewed_rule_keys=workflow_review_rule_keys(staged.workflow),
    )
    approve_workflow_revision(
        store,
        staged.id,
        reviewer_id="admin-2",
        note="已獨立複核既有內容。",
        expected_content_hash=staged.content_hash,
        reviewed_source_urls=workflow_review_source_urls(staged.workflow),
        reviewed_rule_keys=workflow_review_rule_keys(staged.workflow),
    )
    publish_workflow_revision(
        store,
        staged.id,
        reviewer_id="admin-2",
        note="完成雙審。",
    )

    service = NotificationService(repository, content_store=store)
    assert service.refresh_content_updates() == (0, 0)
    assert repository.list_notifications(account.id) == []


def test_notifications_migration_is_server_only() -> None:
    migration = (
        Path(__file__).parents[1]
        / "supabase"
        / "migrations"
        / "20260728121446_notifications.sql"
    ).read_text(encoding="utf-8")
    normalized = " ".join(migration.casefold().split())

    for table in ("exchange_notifications", "exchange_notification_deliveries"):
        assert f"alter table public.{table} enable row level security" in normalized
        assert f"revoke all on table public.{table} from anon, authenticated" in normalized
        assert (
            f"grant select, insert, update, delete on table public.{table} to service_role"
            in normalized
        )
    assert "unique (account_id, dedupe_key)" in normalized
    assert "unique (notification_id, channel)" in normalized


def _notification_api(tmp_path, monkeypatch, *, email_enabled: bool = False):
    repository = JsonlAccountRepository(tmp_path / "repository")
    deadline = datetime.now(TAIPEI) + timedelta(days=7)
    account = _paper_account(
        deadline,
        reminder_days=[7],
        email_enabled=email_enabled,
    )
    token = "notification-api-token"
    repository.save_account(account)
    repository.save_session(
        AccountSessionRecord(
            account_id=account.id,
            token_hash=hashlib.sha256(token.encode("utf-8")).hexdigest(),
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )
    )
    monkeypatch.setenv("EXCHANGE_CONTENT_ADMIN_EMAILS", account.email or "")
    app = create_app(tmp_path / "app-data", account_repository=repository)
    return (
        TestClient(app),
        {"Authorization": f"Bearer {token}"},
        repository,
        account,
    )


def test_notification_center_requires_login_and_supports_read_state(
    tmp_path, monkeypatch
) -> None:
    client, headers, repository, account = _notification_api(tmp_path, monkeypatch)

    assert client.get("/account/notifications").status_code == 401
    first = client.get("/account/notifications", headers=headers)
    assert first.status_code == 200
    assert first.json()["unread_count"] == 1
    notification = first.json()["items"][0]
    assert notification["reminder_days"] == 7
    assert "必須送達" in notification["body"]

    read = client.patch(
        f"/account/notifications/{notification['id']}/read",
        headers=headers,
    )
    assert read.status_code == 200
    assert read.json()["read_at"] is not None
    assert client.get("/account/notifications", headers=headers).json()["unread_count"] == 0

    other = _paper_account(datetime.now(TAIPEI) + timedelta(days=7))
    repository.save_account(other)
    foreign = repository.save_notification(
        repository.list_notifications(account.id)[0].model_copy(
            update={"id": "foreign-notification", "account_id": other.id, "dedupe_key": "foreign"}
        )
    )
    assert foreign.account_id == other.id
    assert (
        client.patch(
            "/account/notifications/foreign-notification/read",
            headers=headers,
        ).status_code
        == 404
    )


def test_notification_center_can_mark_all_owned_notifications_read(
    tmp_path, monkeypatch
) -> None:
    client, headers, repository, account = _notification_api(tmp_path, monkeypatch)
    first = client.get("/account/notifications", headers=headers)
    assert first.status_code == 200
    original = repository.list_notifications(account.id)[0]
    repository.save_notification(
        original.model_copy(
            update={
                "id": "second-owned-notification",
                "dedupe_key": "second-owned",
                "created_at": original.created_at + timedelta(seconds=1),
            }
        )
    )

    marked = client.patch("/account/notifications/read-all", headers=headers)

    assert marked.status_code == 200
    assert marked.json()["unread_count"] == 0
    assert len(marked.json()["items"]) == 2
    assert all(item["read_at"] is not None for item in marked.json()["items"])


def test_notification_center_queues_email_only_after_opt_in(tmp_path, monkeypatch) -> None:
    client, headers, repository, _ = _notification_api(
        tmp_path,
        monkeypatch,
        email_enabled=True,
    )

    response = client.get("/account/notifications", headers=headers)

    assert response.status_code == 200
    notification = response.json()["items"][0]
    delivery = repository.find_delivery(notification["id"], "email")
    assert delivery is not None
    assert delivery.status == "pending"


def test_admin_can_run_due_notification_job(tmp_path, monkeypatch) -> None:
    client, headers, _, _ = _notification_api(tmp_path, monkeypatch)

    assert client.post("/admin/notifications/run-due").status_code == 401
    response = client.post("/admin/notifications/run-due", headers=headers)

    assert response.status_code == 200
    assert response.json()["account_count"] == 1
    assert response.json()["email_delivery_enabled"] is False
