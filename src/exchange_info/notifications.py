from __future__ import annotations

import hashlib
import os
import smtplib
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from email.message import EmailMessage
from typing import TYPE_CHECKING, Iterable, Mapping, Protocol
from urllib.parse import urlparse, urlencode, quote
from zoneinfo import ZoneInfo

from .entitlements import product_feature_enabled
from .models import (
    AccountApplicationWorkspace,
    AccountNotification,
    ApplicationRuleScope,
    ApplicationSourceAuthority,
    ApplicationSubmissionMethod,
    ApplicationWorkflowRevision,
    ApplicationWorkflowReviewStatus,
    CatalogueSourceStatus,
    NotificationDelivery,
    NotificationRunResult,
    UniversityApplicationWorkflow,
    UserAccount,
    ProductFeature,
    utc_now,
)
from .repositories import AccountRepository
from .school_identity import school_identity_key

if TYPE_CHECKING:
    from .content_governance import ContentGovernanceStore


TAIPEI_TIMEZONE = ZoneInfo("Asia/Taipei")
MAX_EMAIL_ATTEMPTS = 4
EMAIL_RETRY_DELAYS = (
    timedelta(minutes=5),
    timedelta(minutes=30),
    timedelta(hours=2),
)


class NotificationConfigurationError(RuntimeError):
    pass


class EmailSender(Protocol):
    def send(self, recipient: str, subject: str, body: str) -> None: ...


class SmtpEmailSender:
    def __init__(
        self,
        *,
        host: str,
        port: int,
        from_address: str,
        username: str | None = None,
        password: str | None = None,
        use_ssl: bool = False,
        use_starttls: bool = True,
        timeout_seconds: float = 15.0,
    ) -> None:
        self.host = host
        self.port = port
        self.from_address = from_address
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.use_starttls = use_starttls
        self.timeout_seconds = timeout_seconds

    def send(self, recipient: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = self.from_address
        message["To"] = recipient
        message["Subject"] = " ".join(subject.splitlines())
        message.set_content(body)
        smtp_class = smtplib.SMTP_SSL if self.use_ssl else smtplib.SMTP
        with smtp_class(
            self.host,
            self.port,
            timeout=self.timeout_seconds,
        ) as client:
            if self.use_starttls and not self.use_ssl:
                client.starttls()
            if self.username:
                client.login(self.username, self.password or "")
            client.send_message(message)


def email_sender_from_env(
    environ: Mapping[str, str] | None = None,
) -> EmailSender | None:
    environment = os.environ if environ is None else environ
    if environment.get("EXCHANGE_NOTIFICATION_EMAIL_ENABLED", "0").strip() != "1":
        return None
    host = environment.get("EXCHANGE_SMTP_HOST", "").strip()
    from_address = environment.get("EXCHANGE_SMTP_FROM", "").strip()
    if not host or not from_address:
        raise NotificationConfigurationError(
            "啟用 Email 通知時必須設定 EXCHANGE_SMTP_HOST 與 EXCHANGE_SMTP_FROM。"
        )
    try:
        port = int(environment.get("EXCHANGE_SMTP_PORT", "587"))
    except ValueError as error:
        raise NotificationConfigurationError("EXCHANGE_SMTP_PORT 必須是整數。") from error
    use_ssl = environment.get("EXCHANGE_SMTP_SSL", "0").strip() == "1"
    return SmtpEmailSender(
        host=host,
        port=port,
        from_address=from_address,
        username=environment.get("EXCHANGE_SMTP_USERNAME", "").strip() or None,
        password=environment.get("EXCHANGE_SMTP_PASSWORD", "").strip() or None,
        use_ssl=use_ssl,
        use_starttls=(
            not use_ssl
            and environment.get("EXCHANGE_SMTP_STARTTLS", "1").strip() != "0"
        ),
    )


@dataclass(frozen=True)
class DeadlineTarget:
    source_key: str
    title: str
    deadline_at: datetime
    deadline_label: str
    source_url: str | None = None
    responsible_unit: str | None = None
    reminder_days: frozenset[int] | None = None
    action_url: str = "/#deadlines"


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=TAIPEI_TIMEZONE)
    return value.astimezone(timezone.utc)


def _calendar_deadline(value: str) -> datetime:
    parsed = date.fromisoformat(value)
    return datetime.combine(parsed, time(23, 59, 59), tzinfo=TAIPEI_TIMEZONE).astimezone(
        timezone.utc
    )


def deadline_targets(account: UserAccount) -> list[DeadlineTarget]:
    targets: dict[str, DeadlineTarget] = {}
    for workspace in account.application_workspaces:
        for progress_key, progress in workspace.submission_progress.items():
            if progress.status == "completed":
                continue
            if progress.method in {
                ApplicationSubmissionMethod.PAPER,
                ApplicationSubmissionMethod.MIXED,
            }:
                # Paper reminders must never substitute the send-by date for arrival.
                deadline = progress.arrival_deadline_at
                deadline_label = "必須送達"
            else:
                deadline = progress.arrival_deadline_at or progress.send_by_at
                deadline_label = "送件截止"
            if deadline is None:
                continue
            source_key = f"submission:{workspace.home_school}:{progress_key}"
            targets[source_key] = DeadlineTarget(
                source_key=source_key,
                title=progress.title,
                deadline_at=_aware_utc(deadline),
                deadline_label=deadline_label,
                responsible_unit=progress.responsible_unit,
            )
    calendar_events = {
        event.id: event
        for workspace in account.application_workspaces
        for event in workspace.deadline_events
    }
    calendar_events.update({event.id: event for event in account.calendar_events})
    smart_reminders = product_feature_enabled(account, ProductFeature.SMART_REMINDERS)
    for event in calendar_events.values():
        if event.generated_from_event_id or event.status == "ready":
            continue
        try:
            event_deadline = _calendar_deadline(event.date)
        except ValueError:
            continue
        source_key = f"calendar:{event.id}"
        targets[source_key] = DeadlineTarget(
            source_key=source_key,
            title=event.title,
            deadline_at=event_deadline,
            deadline_label="截止",
            source_url=event.source_url,
            reminder_days=(
                frozenset({event.reminder_days})
                if event.origin == "personal"
                else None
            ),
            action_url="/#calendar",
        )
        if smart_reminders and event.preparation_days > 0:
            deadline = date.fromisoformat(event.date) - timedelta(
                days=event.preparation_days
            )
            start_key = f"calendar-start:{event.id}"
            targets[start_key] = DeadlineTarget(
                source_key=start_key,
                title=event.title,
                deadline_at=_calendar_deadline(deadline.isoformat()),
                deadline_label="建議開始準備日",
                source_url=event.source_url,
                reminder_days=frozenset({0}),
                action_url="/#calendar",
            )
    return sorted(targets.values(), key=lambda target: target.deadline_at)


def _notification_dedupe_key(target: DeadlineTarget, reminder_days: int) -> str:
    return (
        f"deadline:{target.source_key}:{target.deadline_at.isoformat()}:"
        f"days-{reminder_days}"
    )


def _target_reminder_days(
    target: DeadlineTarget,
    configured: Iterable[int],
) -> set[int]:
    return set(target.reminder_days if target.reminder_days is not None else configured)


def _delivery_id(notification_id: str) -> str:
    return hashlib.sha256(f"{notification_id}:email".encode("utf-8")).hexdigest()[:32]


def _normal(value: str | None) -> str:
    return " ".join(str(value or "").strip().casefold().split())


def _school_matches(value: str | None, expected: str | None) -> bool:
    return bool(value and expected) and school_identity_key(value) == school_identity_key(
        expected
    )


def _matches_allowed(
    value: str | None,
    allowed: Iterable[str],
    *,
    school: bool = False,
) -> bool:
    values = [row for row in allowed if str(row).strip()]
    if not values:
        return True
    if not value:
        return False
    if school:
        key = school_identity_key(value)
        return key in {school_identity_key(row) for row in values}
    key = _normal(value)
    return key in {_normal(row) for row in values}


def _workspace_partner_names(workspace: AccountApplicationWorkspace) -> set[str]:
    names = set(workspace.application_schools)
    if workspace.application_context.target_school:
        names.add(workspace.application_context.target_school)
    return {name for name in names if name.strip()}


def _scope_matches_workspace(
    account: UserAccount,
    workspace: AccountApplicationWorkspace,
    scope: ApplicationRuleScope,
) -> bool:
    context = workspace.application_context
    if not _matches_allowed(
        workspace.home_school, scope.home_universities, school=True
    ):
        return False
    partner_names = _workspace_partner_names(workspace)
    if scope.partner_universities and not any(
        _matches_allowed(name, scope.partner_universities, school=True)
        for name in partner_names
    ):
        return False
    if not _matches_allowed(context.academic_year, scope.academic_years):
        return False
    if not _matches_allowed(context.application_round or context.semester, scope.application_rounds):
        return False
    # Content-change notices follow the established application plan. Student
    # verification controls community permissions, but it is not a prerequisite
    # for receiving a rule change that affects a plan the account already saved.
    department = context.department or account.verified_department
    if not _matches_allowed(department, scope.departments):
        return False
    if not _matches_allowed(context.college, scope.colleges):
        return False
    return True


def matching_workspaces(
    account: UserAccount,
    workflow: UniversityApplicationWorkflow,
    scopes: list[ApplicationRuleScope] | None,
) -> list[AccountApplicationWorkspace]:
    """Workspaces whose saved plan a published workflow change can affect."""

    matched: list[AccountApplicationWorkspace] = []
    for workspace in account.application_workspaces:
        context = workspace.application_context
        if not _school_matches(workspace.home_school, workflow.home_university):
            continue
        if not any(
            _school_matches(name, workflow.school_name)
            for name in _workspace_partner_names(workspace)
        ):
            continue
        if workflow.academic_year and _normal(context.academic_year) != _normal(
            workflow.academic_year
        ):
            continue
        allowed_rounds = set(workflow.effective_application_rounds)
        if workflow.application_round:
            allowed_rounds.add(workflow.application_round)
        if allowed_rounds and _normal(context.application_round or context.semester) not in {
            _normal(value) for value in allowed_rounds
        }:
            continue
        if scopes is not None and not any(
            _scope_matches_workspace(account, workspace, scope) for scope in scopes
        ):
            continue
        matched.append(workspace)
    return matched


def account_has_affected_plan(
    account: UserAccount,
    workflow: UniversityApplicationWorkflow,
    scopes: list[ApplicationRuleScope] | None,
) -> bool:
    return bool(matching_workspaces(account, workflow, scopes))


def _safe_web_url(value: str | None) -> str | None:
    candidate = str(value or "").strip()
    parsed = urlparse(candidate)
    if parsed.scheme.casefold() not in {"http", "https"} or not parsed.netloc:
        return None
    return candidate[:1000]


def _official_source_url(workflow: UniversityApplicationWorkflow) -> str | None:
    sources = [
        row
        for row in workflow.sources
        if row.authority != ApplicationSourceAuthority.COMMUNITY_EXPERIENCE
        and _safe_web_url(row.source_url)
    ]
    if sources:
        sources.sort(key=lambda row: (row.priority or 99, row.title.casefold()))
        return _safe_web_url(sources[0].source_url)
    return _safe_web_url(workflow.partner_website)


def _trim(value: str, limit: int) -> str:
    compact = " ".join(value.split())
    return compact if len(compact) <= limit else f"{compact[: limit - 1].rstrip()}…"


def workflow_action_url(workflow: UniversityApplicationWorkflow) -> str:
    return f"/?{urlencode({'home': workflow.home_university})}#school={quote(workflow.school_name, safe='')}"


def content_update_notification(
    account: UserAccount,
    revision: ApplicationWorkflowRevision,
    base_workflow: UniversityApplicationWorkflow,
    scopes: list[ApplicationRuleScope] | None,
    now: datetime | None = None,
) -> AccountNotification | None:
    preferences = account.notification_preferences
    if not preferences.content_updates_enabled:
        return None
    if not account_has_affected_plan(account, revision.workflow, scopes):
        return None
    channels: list[str] = []
    if preferences.web_enabled:
        channels.append("web")
    if preferences.email_enabled and account.email:
        channels.append("email")
    if not channels:
        return None
    current = _aware_utc(now or utc_now())
    summary = "；".join(revision.change_summary) or "官方申請流程內容已更新。"
    applicability = "、".join(
        value
        for value in (
            revision.workflow.academic_year,
            revision.workflow.application_round,
        )
        if value
    )
    applicability_note = f"適用：{applicability}。" if applicability else ""
    body = _trim(
        (
            f"{revision.workflow.home_university} → {revision.workflow.school_name} "
            f"已由第 {base_workflow.version} 版更新為第 {revision.version} 版。"
            f"變更摘要：{summary}。{applicability_note}"
            "請重新核對申請清單、文件與送件方式。"
        ),
        1000,
    )
    return AccountNotification(
        account_id=account.id,
        dedupe_key=f"content-update:{revision.id}",
        kind="content_update",
        channels=channels,
        title=_trim(f"「{revision.workflow.school_name}」申請規定已更新", 180),
        body=body,
        action_url=workflow_action_url(revision.workflow),
        source_key=(
            f"content-update:{revision.workflow_key}:v{revision.version}"
        )[:300],
        source_url=_official_source_url(revision.workflow),
        scheduled_for=current,
        created_at=current,
    )


def catalogue_source_notification(
    account: UserAccount,
    source: CatalogueSourceStatus,
    now: datetime | None = None,
) -> AccountNotification | None:
    """Turn each meaningful CGU catalogue-source generation into one web notice."""
    if (
        not account.notification_preferences.web_enabled
        or not _school_matches(account.home_university, "長庚大學")
    ):
        return None
    current = _aware_utc(now or utc_now())
    if source.status == "unavailable":
        title = "長庚合作校來源暫不可用"
    elif source.last_attempt_result == "failed":
        title = "長庚合作校來源更新暫不可用，保留歷次資料"
    elif source.status == "retrieved":
        title = "長庚合作校來源已取得"
    else:
        title = "長庚合作校使用歷次資料"
    source_time = (
        _aware_utc(source.last_success_at)
        .astimezone(TAIPEI_TIMEZONE)
        .strftime("%Y/%m/%d %H:%M")
        if source.last_success_at
        else "尚無成功取得時間"
    )
    generation = (
        source.last_attempt_at.isoformat()
        if source.last_attempt_result == "failed" and source.last_attempt_at
        else source.snapshot_hash
        or (source.last_success_at.isoformat() if source.last_success_at else "none")
    )
    return AccountNotification(
        account_id=account.id,
        dedupe_key=f"catalogue-source:cgu:{source.status}:{source.last_attempt_result or 'none'}:{generation}",
        kind="catalogue_update",
        channels=["web"],
        title=title,
        body=(
            f"來源取得時間：{source_time}。取得時間不代表當期已核實；"
            "年度、名額與開放狀態請依原資料及官方公告確認。"
        ),
        action_url="/#partners",
        source_key="catalogue-source:cgu",
        source_url=source.source_urls[0] if source.source_urls else None,
        scheduled_for=current,
        created_at=current,
    )


class NotificationService:
    def __init__(
        self,
        repository: AccountRepository,
        *,
        email_sender: EmailSender | None = None,
        content_store: ContentGovernanceStore | None = None,
    ) -> None:
        self.repository = repository
        self.email_sender = email_sender
        self.content_store = content_store

    def _persist_candidate(
        self,
        account: UserAccount,
        candidate: AccountNotification,
        current: datetime,
    ) -> tuple[int, int]:
        existing = self.repository.find_notification_by_dedupe(
            account.id, candidate.dedupe_key
        )
        if existing is not None and existing.deleted_at is not None:
            return 0, 0
        notification = existing or self.repository.save_notification(candidate)
        created_count = int(existing is None and notification.id == candidate.id)
        queued_email_count = 0
        if (
            candidate.kind != "catalogue_update"
            and account.notification_preferences.email_enabled
            and account.email
        ):
            delivery = self.repository.find_delivery(notification.id, "email")
            if delivery is None:
                self.repository.save_delivery(
                    NotificationDelivery(
                        id=_delivery_id(notification.id),
                        notification_id=notification.id,
                        account_id=account.id,
                        next_attempt_at=current,
                        created_at=current,
                        updated_at=current,
                    )
                )
                queued_email_count = 1
        return created_count, queued_email_count

    def due_notifications(
        self,
        account: UserAccount,
        now: datetime | None = None,
    ) -> list[AccountNotification]:
        current = _aware_utc(now or utc_now())
        current_local_date = current.astimezone(TAIPEI_TIMEZONE).date()
        preferences = account.notification_preferences
        if not preferences.web_enabled and not preferences.email_enabled:
            return []
        channels: list[str] = []
        if preferences.web_enabled:
            channels.append("web")
        if preferences.email_enabled and account.email:
            channels.append("email")
        if not channels:
            return []
        notifications: list[AccountNotification] = []
        for target in deadline_targets(account):
            deadline_local = target.deadline_at.astimezone(TAIPEI_TIMEZONE)
            days_remaining = (deadline_local.date() - current_local_date).days
            if days_remaining not in _target_reminder_days(
                target,
                preferences.deadline_reminder_days,
            ):
                continue
            if days_remaining == 0:
                title = f"今天是「{target.title}」{target.deadline_label}"
            else:
                title = f"距離「{target.title}」還有 {days_remaining} 天"
            unit_note = (
                f"；承辦單位：{target.responsible_unit}"
                if target.responsible_unit
                else ""
            )
            body = (
                f"{target.deadline_label}：{deadline_local:%Y/%m/%d %H:%M}"
                f"（台北時間）{unit_note}。請查看目前未完成項目。"
            )
            notifications.append(
                AccountNotification(
                    account_id=account.id,
                    dedupe_key=_notification_dedupe_key(target, days_remaining),
                    channels=channels,
                    title=title,
                    body=body,
                    action_url=target.action_url,
                    source_key=target.source_key,
                    source_url=target.source_url,
                    deadline_at=target.deadline_at,
                    reminder_days=days_remaining,
                    scheduled_for=current,
                    created_at=current,
                )
            )
        return notifications

    def refresh_account(
        self,
        account: UserAccount,
        now: datetime | None = None,
    ) -> tuple[int, int]:
        current = _aware_utc(now or utc_now())
        created_count = 0
        queued_email_count = 0
        for candidate in self.due_notifications(account, current):
            created, queued = self._persist_candidate(account, candidate, current)
            created_count += created
            queued_email_count += queued
        return created_count, queued_email_count

    def refresh_catalogue_source(
        self,
        account: UserAccount,
        source: CatalogueSourceStatus,
        now: datetime | None = None,
    ) -> tuple[int, int]:
        current = _aware_utc(now or utc_now())
        candidate = catalogue_source_notification(account, source, current)
        if candidate is None:
            return 0, 0
        return self._persist_candidate(account, candidate, current)

    def refresh_content_updates(
        self,
        now: datetime | None = None,
        *,
        accounts: list[UserAccount] | None = None,
    ) -> tuple[int, int]:
        if self.content_store is None:
            return 0, 0
        from .content_governance import (
            affected_workflow_scopes,
            base_workflow_for_revision,
            workflow_content_hash,
        )

        current = _aware_utc(now or utc_now())
        revisions = self.content_store.list_revisions()
        account_rows = accounts if accounts is not None else self.repository.list_accounts()
        created_count = 0
        queued_email_count = 0
        for revision in sorted(
            revisions,
            key=lambda row: row.reviewed_at or row.detected_at,
        ):
            # Only the currently published revision may create new notifications.
            # Already-created deliveries remain valid if a later version supersedes it.
            if (
                revision.status != ApplicationWorkflowReviewStatus.PUBLISHED
                or revision.base_version is None
                or revision.reviewed_at is None
                or not revision.reviewed_by
                or revision.reviewed_by == "legacy_import"
            ):
                continue
            base_workflow = base_workflow_for_revision(revisions, revision)
            if base_workflow is None:
                continue
            # A legacy workflow entering the dual-review system keeps identical
            # student-visible content and must not look like a content update.
            if workflow_content_hash(base_workflow) == workflow_content_hash(
                revision.workflow
            ):
                continue
            scopes = affected_workflow_scopes(base_workflow, revision.workflow)
            for account in account_rows:
                candidate = content_update_notification(
                    account,
                    revision,
                    base_workflow,
                    scopes,
                    current,
                )
                if candidate is None:
                    continue
                created, queued = self._persist_candidate(account, candidate, current)
                created_count += created
                queued_email_count += queued
        return created_count, queued_email_count

    def _delivery_still_allowed(
        self,
        account: UserAccount,
        notification: AccountNotification,
    ) -> bool:
        if notification.deleted_at is not None or notification.kind == "catalogue_update":
            return False
        preferences = account.notification_preferences
        if not preferences.email_enabled or not account.email:
            return False
        if notification.kind == "content_update":
            if not preferences.content_updates_enabled:
                return False
            if self.content_store is None:
                return True
            from .content_governance import (
                affected_workflow_scopes,
                base_workflow_for_revision,
            )

            revision_id = notification.dedupe_key.removeprefix("content-update:")
            revisions = self.content_store.list_revisions()
            revision = next((row for row in revisions if row.id == revision_id), None)
            if (
                revision is None
                or revision.status
                not in {
                    ApplicationWorkflowReviewStatus.PUBLISHED,
                    ApplicationWorkflowReviewStatus.SUPERSEDED,
                }
                or revision.reviewed_at is None
                or not revision.reviewed_by
            ):
                return False
            base_workflow = base_workflow_for_revision(revisions, revision)
            return bool(
                base_workflow
                and account_has_affected_plan(
                    account,
                    revision.workflow,
                    affected_workflow_scopes(base_workflow, revision.workflow),
                )
            )
        current_keys = {
            _notification_dedupe_key(target, reminder_day)
            for target in deadline_targets(account)
            for reminder_day in _target_reminder_days(
                target,
                preferences.deadline_reminder_days,
            )
        }
        return notification.dedupe_key in current_keys

    def dispatch_due_emails(
        self,
        now: datetime | None = None,
    ) -> tuple[int, int, int]:
        current = _aware_utc(now or utc_now())
        if self.email_sender is None:
            return 0, 0, 0
        sent_count = 0
        retry_count = 0
        failed_count = 0
        for delivery in self.repository.list_due_deliveries(current):
            account = self.repository.find_account_by_id(delivery.account_id)
            notification = self.repository.find_notification_by_id(
                delivery.account_id, delivery.notification_id
            )
            if (
                account is None
                or notification is None
                or not self._delivery_still_allowed(account, notification)
            ):
                self.repository.save_delivery(
                    delivery.model_copy(
                        update={
                            "status": "cancelled",
                            "last_error_code": None,
                            "updated_at": current,
                        }
                    )
                )
                continue
            try:
                source_line = (
                    f"\n官方來源：{notification.source_url}"
                    if notification.source_url
                    else ""
                )
                self.email_sender.send(
                    account.email or "",
                    notification.title,
                    (
                        f"{notification.body}{source_line}\n\n"
                        f"開啟申請計畫：{notification.action_url or '/'}"
                    ),
                )
            except Exception as error:  # provider errors are converted to retry metadata
                attempts = delivery.attempt_count + 1
                final_failure = attempts >= MAX_EMAIL_ATTEMPTS
                delay = EMAIL_RETRY_DELAYS[min(attempts - 1, len(EMAIL_RETRY_DELAYS) - 1)]
                self.repository.save_delivery(
                    delivery.model_copy(
                        update={
                            "status": "failed" if final_failure else "retrying",
                            "attempt_count": attempts,
                            "next_attempt_at": current + delay,
                            "last_error_code": type(error).__name__[:120],
                            "updated_at": current,
                        }
                    )
                )
                if final_failure:
                    failed_count += 1
                else:
                    retry_count += 1
                continue
            self.repository.save_delivery(
                delivery.model_copy(
                    update={
                        "status": "sent",
                        "attempt_count": delivery.attempt_count + 1,
                        "sent_at": current,
                        "last_error_code": None,
                        "updated_at": current,
                    }
                )
            )
            sent_count += 1
        return sent_count, retry_count, failed_count

    def run_due(self, now: datetime | None = None) -> NotificationRunResult:
        current = _aware_utc(now or utc_now())
        created_count = 0
        queued_email_count = 0
        account_rows = self.repository.list_accounts()
        content_created, content_queued = self.refresh_content_updates(
            current,
            accounts=account_rows,
        )
        created_count += content_created
        queued_email_count += content_queued
        for account in account_rows:
            created, queued = self.refresh_account(account, current)
            created_count += created
            queued_email_count += queued
        sent_count, retry_count, failed_count = self.dispatch_due_emails(current)
        return NotificationRunResult(
            account_count=len(account_rows),
            created_count=created_count,
            queued_email_count=queued_email_count,
            sent_count=sent_count,
            retry_count=retry_count,
            failed_count=failed_count,
            email_delivery_enabled=self.email_sender is not None,
            ran_at=current,
        )
