from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from threading import Barrier
from typing import Any

import pytest

import exchange_info.repositories as repository_module
from exchange_info.models import (
    AccountApplicationWorkspace,
    AccountSubmissionProgress,
    ApplicationCenterContext,
    ApplicationSubmissionMethod,
    CommunityModerationAudit,
    CommunitySuspensionRequest,
    UserAccount,
    utc_now,
)
from exchange_info.repositories import (
    AccountRepositoryError,
    CommunitySuspensionMutationRequest,
    CommunitySuspensionMutationStatus,
    JsonlAccountRepository,
    SupabaseAccountRepository,
    WorkspaceMutationKind,
    WorkspaceMutationRequest,
    WorkspaceMutationStatus,
)


MIGRATION = (
    Path(__file__).parents[1]
    / "supabase"
    / "migrations"
    / "20260823130000_atomic_workspace_and_suspension.sql"
)


def _workspace(
    home_school: str = "長庚大學",
    *,
    revision: int = 0,
    favorite_schools: list[str] | None = None,
    submission_progress: dict[str, AccountSubmissionProgress] | None = None,
) -> AccountApplicationWorkspace:
    return AccountApplicationWorkspace(
        home_school=home_school,
        revision=revision,
        favorite_schools=favorite_schools or [],
        application_context=ApplicationCenterContext(school_name=home_school),
        submission_progress=submission_progress or {},
    )


def _progress(
    status: str = "not_started",
    *,
    title: str = "紙本申請表",
) -> AccountSubmissionProgress:
    return AccountSubmissionProgress(
        title=title,
        method=ApplicationSubmissionMethod.PAPER,
        status=status,
    )


def _workspace_request(
    account_id: str,
    workspace: AccountApplicationWorkspace,
    *,
    kind: WorkspaceMutationKind = WorkspaceMutationKind.WORKSPACE_REPLACE,
    progress_key: str | None = None,
    progress: AccountSubmissionProgress | None = None,
) -> WorkspaceMutationRequest:
    return WorkspaceMutationRequest(
        account_id=account_id,
        expected_revision=workspace.revision,
        workspace=workspace,
        mutation_kind=kind,
        progress_key=progress_key,
        progress=progress,
    )


def test_jsonl_two_repository_instances_allow_one_same_revision_commit(
    tmp_path,
) -> None:
    account = UserAccount(id="workspace-race-account", display_name="Workspace Race")
    JsonlAccountRepository(tmp_path).create_account(account)
    barrier = Barrier(2)
    requests = [
        _workspace_request(
            account.id,
            _workspace(favorite_schools=[f"candidate-{index}"]),
        )
        for index in range(2)
    ]

    def commit(request: WorkspaceMutationRequest):
        repository = JsonlAccountRepository(tmp_path)
        barrier.wait()
        return repository.commit_workspace(request)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(commit, requests))

    assert [result.status for result in results].count(
        WorkspaceMutationStatus.COMMITTED
    ) == 1
    assert [result.status for result in results].count(
        WorkspaceMutationStatus.CONFLICT
    ) == 1
    persisted = JsonlAccountRepository(tmp_path).find_account_by_id(account.id)
    assert persisted is not None
    assert len(persisted.application_workspaces) == 1
    assert persisted.application_workspaces[0].revision == 1
    assert persisted.application_workspaces[0].favorite_schools in (
        ["candidate-0"],
        ["candidate-1"],
    )
    assert all(result.workspace is not None for result in results)
    assert {result.workspace.revision for result in results if result.workspace} == {1}


def test_jsonl_workspace_commit_preserves_other_home_schools(tmp_path) -> None:
    account = UserAccount(id="multi-school-account", display_name="Multi School")
    first_repository = JsonlAccountRepository(tmp_path)
    second_repository = JsonlAccountRepository(tmp_path)
    first_repository.create_account(account)

    first = first_repository.commit_workspace(
        _workspace_request(
            account.id,
            _workspace("長庚大學", favorite_schools=["Lincoln University"]),
        )
    )
    second = second_repository.commit_workspace(
        _workspace_request(
            account.id,
            _workspace("國立臺北大學", favorite_schools=["Osaka University"]),
        )
    )

    assert first.status == WorkspaceMutationStatus.COMMITTED
    assert second.status == WorkspaceMutationStatus.COMMITTED
    persisted = first_repository.find_account_by_id(account.id)
    assert persisted is not None
    by_school = {row.home_school: row for row in persisted.application_workspaces}
    assert set(by_school) == {"長庚大學", "國立臺北大學"}
    assert by_school["長庚大學"].favorite_schools == ["Lincoln University"]
    assert by_school["國立臺北大學"].favorite_schools == ["Osaka University"]
    assert {row.revision for row in by_school.values()} == {1}


def test_jsonl_workspace_replace_preserves_latest_submission_progress(
    tmp_path,
) -> None:
    latest_progress = _progress("submitted")
    stale_progress = _progress("not_started")
    account = UserAccount(
        id="replace-preserves-progress",
        display_name="Preserve Progress",
        application_workspaces=[
            _workspace(
                revision=7,
                favorite_schools=["Old Favorite"],
                submission_progress={"paper-form": latest_progress},
            )
        ],
    )
    repository = JsonlAccountRepository(tmp_path)
    repository.create_account(account)

    result = repository.commit_workspace(
        _workspace_request(
            account.id,
            _workspace(
                revision=7,
                favorite_schools=["New Favorite"],
                submission_progress={
                    "paper-form": stale_progress,
                    "client-only": stale_progress,
                },
            ),
        )
    )

    assert result.status == WorkspaceMutationStatus.COMMITTED
    assert result.workspace is not None
    assert result.workspace.revision == 8
    assert result.workspace.favorite_schools == ["New Favorite"]
    assert result.workspace.submission_progress == {"paper-form": latest_progress}
    persisted = repository.find_account_by_id(account.id)
    assert persisted is not None
    assert persisted.application_workspaces == [result.workspace]


def test_jsonl_submission_transition_uses_workspace_revision_cas(tmp_path) -> None:
    account = UserAccount(id="submission-cas-account", display_name="Submission CAS")
    repository = JsonlAccountRepository(tmp_path)
    repository.create_account(account)
    initial_workspace = _workspace()

    first = repository.commit_workspace(
        _workspace_request(
            account.id,
            initial_workspace,
            kind=WorkspaceMutationKind.SUBMISSION_PROGRESS_TRANSITION,
            progress_key="paper-form",
            progress=_progress("preparing"),
        )
    )
    stale = repository.commit_workspace(
        _workspace_request(
            account.id,
            initial_workspace,
            kind=WorkspaceMutationKind.SUBMISSION_PROGRESS_TRANSITION,
            progress_key="paper-form",
            progress=_progress("submitted"),
        )
    )

    assert first.status == WorkspaceMutationStatus.COMMITTED
    assert first.workspace is not None
    assert first.workspace.revision == 1
    assert stale.status == WorkspaceMutationStatus.CONFLICT
    assert stale.workspace is not None
    assert stale.workspace.revision == 1
    assert stale.workspace.submission_progress["paper-form"].status == "preparing"

    current = first.workspace.model_copy()
    committed = repository.commit_workspace(
        _workspace_request(
            account.id,
            current,
            kind=WorkspaceMutationKind.SUBMISSION_PROGRESS_TRANSITION,
            progress_key="paper-form",
            progress=_progress("submitted"),
        )
    )

    assert committed.status == WorkspaceMutationStatus.COMMITTED
    assert committed.workspace is not None
    assert committed.workspace.revision == 2
    assert committed.workspace.submission_progress["paper-form"].status == "submitted"


def test_jsonl_workspace_commit_cannot_recreate_deleted_account(tmp_path) -> None:
    account = UserAccount(id="deleted-before-workspace", display_name="Deleted")
    repository = JsonlAccountRepository(tmp_path)
    repository.create_account(account)
    repository.delete_account(account.id)

    result = repository.commit_workspace(
        _workspace_request(account.id, _workspace(favorite_schools=["Must Not Persist"]))
    )

    assert result.status == WorkspaceMutationStatus.ACCOUNT_MISSING
    assert result.workspace is None
    assert repository.find_account_by_id(account.id) is None
    assert repository.list_accounts() == []


@pytest.mark.parametrize(
    "field_name,value",
    [
        ("application_workspaces", []),
        ("community_suspended_until", None),
    ],
)
def test_jsonl_generic_profile_patch_rejects_dedicated_mutation_fields(
    tmp_path,
    field_name: str,
    value: object,
) -> None:
    repository = JsonlAccountRepository(tmp_path)
    account = UserAccount(id="patch-allowlist-account", display_name="Patch Allowlist")
    repository.create_account(account)

    with pytest.raises(ValueError, match=field_name):
        repository.patch_account_fields(account.id, {field_name: value})

    assert repository.find_account_by_id(account.id) == account


def test_jsonl_suspension_commit_is_audited_idempotent_and_cas_guarded(
    tmp_path,
) -> None:
    repository = JsonlAccountRepository(tmp_path)
    previous_until = utc_now() + timedelta(days=1)
    suspended_until = previous_until + timedelta(days=14)
    target = UserAccount(
        id="suspension-target",
        display_name="Suspension Target",
        community_suspended_until=previous_until,
    )
    moderator = UserAccount(id="suspension-moderator", display_name="Moderator")
    repository.create_account(target)
    repository.create_account(moderator)
    request = CommunitySuspensionMutationRequest(
        event_id="suspension-event-0001",
        identity_id="identity-for-target",
        account_id=target.id,
        moderator_id=moderator.id,
        expected_suspended_until=previous_until,
        suspended_until=suspended_until,
        reason="  repeated abuse  ",
    )

    committed = repository.commit_community_suspension(request)

    assert committed.status == CommunitySuspensionMutationStatus.COMMITTED
    assert committed.account is not None
    assert committed.account.community_suspended_until == suspended_until
    assert committed.audit is not None
    assert committed.audit.id == request.event_id
    assert committed.audit.resource_type == "identity"
    assert committed.audit.resource_id == request.identity_id
    assert committed.audit.moderator_id == moderator.id
    assert committed.audit.note == "repeated abuse"
    assert committed.audit.previous_suspended_until == previous_until
    assert committed.audit.new_suspended_until == suspended_until
    assert committed.audit.retained_until == committed.audit.created_at + timedelta(days=90)
    assert repository.list_community_suspension_audits() == [committed.audit]
    replay = repository.commit_community_suspension(request)

    assert replay.status == CommunitySuspensionMutationStatus.COMMITTED
    assert replay.audit == committed.audit
    assert replay.account == committed.account
    assert repository.list_community_suspension_audits() == [committed.audit]

    conflict = repository.commit_community_suspension(
        request.model_copy(
            update={
                "event_id": "suspension-event-0002",
                "suspended_until": suspended_until + timedelta(days=1),
            }
        )
    )

    assert conflict.status == CommunitySuspensionMutationStatus.CONFLICT
    assert conflict.account is not None
    assert conflict.account.community_suspended_until == suspended_until
    assert conflict.audit is None
    assert repository.list_community_suspension_audits() == [committed.audit]


def test_suspension_request_requires_timezone_and_nonblank_reason() -> None:
    with pytest.raises(ValueError, match="時區"):
        CommunitySuspensionRequest(
            suspended_until=(utc_now() + timedelta(days=1)).replace(tzinfo=None),
            reason="重複違規",
        )

    with pytest.raises(ValueError, match="至少"):
        CommunitySuspensionRequest(
            suspended_until=utc_now() + timedelta(days=1),
            reason="  ",
        )


def test_jsonl_suspension_audit_write_failure_leaves_account_unsuspended(
    tmp_path,
    monkeypatch,
) -> None:
    repository = JsonlAccountRepository(tmp_path)
    target = UserAccount(id="audit-failure-target", display_name="Audit Failure")
    moderator = UserAccount(id="audit-failure-moderator", display_name="Moderator")
    repository.create_account(target)
    repository.create_account(moderator)

    def fail_audit_write(*args: Any, **kwargs: Any) -> None:
        raise OSError("injected audit write failure")

    monkeypatch.setattr(
        repository_module,
        "save_community_moderation_audits",
        fail_audit_write,
    )

    with pytest.raises(AccountRepositoryError):
        repository.commit_community_suspension(
            CommunitySuspensionMutationRequest(
                event_id="audit-failure-event-01",
                identity_id="audit-failure-identity",
                account_id=target.id,
                moderator_id=moderator.id,
                expected_suspended_until=None,
                suspended_until=utc_now() + timedelta(days=7),
                reason="test write failure",
            )
        )

    persisted = repository.find_account_by_id(target.id)
    assert persisted is not None
    assert persisted.community_suspended_until is None
    assert repository.list_community_suspension_audits() == []


def test_jsonl_suspension_audit_list_purges_expired_identity_events(tmp_path) -> None:
    current = utc_now()
    expired = CommunityModerationAudit(
        id="expired-suspension-audit",
        resource_type="identity",
        resource_id="expired-identity",
        previous_status="active",
        new_status="suspended",
        moderator_id="moderator",
        note="expired event",
        retained_until=current - timedelta(seconds=1),
        created_at=current - timedelta(days=91),
    )
    retained = expired.model_copy(
        update={
            "id": "retained-suspension-audit",
            "resource_id": "retained-identity",
            "retained_until": current + timedelta(days=1),
        }
    )
    unrelated = expired.model_copy(
        update={
            "id": "unrelated-content-audit",
            "resource_type": "post",
            "resource_id": "post-1",
        }
    )
    repository_module.save_community_moderation_audits(
        [expired, retained, unrelated],
        tmp_path,
    )
    repository = JsonlAccountRepository(tmp_path)

    assert repository.list_community_suspension_audits() == [retained]
    assert repository_module.load_community_moderation_audits(tmp_path) == [
        retained,
        unrelated,
    ]


class _RpcResponse:
    def __init__(self, payload: object) -> None:
        self._payload = payload
        self.content = b"{...}"

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self._payload


class _RecordingSession:
    def __init__(self, *responses: object) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def request(self, method: str, url: str, **kwargs: Any) -> _RpcResponse:
        self.calls.append({"method": method, "url": url, **kwargs})
        if not self.responses:
            raise AssertionError(f"Unexpected repository request: {method} {url}")
        return _RpcResponse(self.responses.pop(0))


def test_supabase_account_create_rejects_suspension_without_audit_rpc() -> None:
    session = _RecordingSession()
    repository = SupabaseAccountRepository(
        "https://project.supabase.co",
        "server-secret",
        request_session=session,
    )

    with pytest.raises(AccountRepositoryError, match="停權"):
        repository.create_account(
            UserAccount(
                id="pre-suspended-account",
                display_name="Must Use Moderation RPC",
                community_suspended_until=utc_now() + timedelta(days=1),
            )
        )

    assert session.calls == []


def test_supabase_workspace_adapter_uses_exactly_one_atomic_rpc() -> None:
    candidate = _workspace(favorite_schools=["Lincoln University"])
    committed = candidate.model_copy(update={"revision": 1})
    session = _RecordingSession(
        {
            "status": WorkspaceMutationStatus.COMMITTED.value,
            "workspace": committed.model_dump(mode="json"),
        }
    )
    repository = SupabaseAccountRepository(
        "https://project.supabase.co",
        "server-secret",
        request_session=session,
    )
    request = _workspace_request("supabase-workspace-account", candidate)

    result = repository.commit_workspace(request)

    assert result.status == WorkspaceMutationStatus.COMMITTED
    assert result.workspace == committed
    assert len(session.calls) == 1
    call = session.calls[0]
    assert call["method"] == "POST"
    assert call["url"].endswith("/rest/v1/rpc/exchange_commit_account_workspace")
    assert call["json"] == {
        "p_account_id": request.account_id,
        "p_home_school_key": "長庚大學",
        "p_expected_revision": 0,
        "p_candidate_workspace": candidate.model_dump(mode="json"),
        "p_mutation_kind": WorkspaceMutationKind.WORKSPACE_REPLACE.value,
        "p_progress_key": None,
        "p_progress": None,
    }


def test_supabase_suspension_adapter_uses_exactly_one_atomic_rpc() -> None:
    suspended_until = utc_now() + timedelta(days=14)
    committed_at = utc_now()
    retained_until = committed_at + timedelta(days=90)
    account = UserAccount(
        id="supabase-suspension-account",
        display_name="Supabase Suspension",
        community_suspended_until=suspended_until,
    )
    audit = CommunityModerationAudit(
        id="supabase-suspension-event",
        resource_type="identity",
        resource_id="supabase-identity",
        previous_status="active",
        new_status="suspended",
        moderator_id="supabase-moderator",
        note="policy violation",
        previous_suspended_until=None,
        new_suspended_until=suspended_until,
        retained_until=retained_until,
        created_at=committed_at,
    )
    account_payload = {
        "id": account.id,
        "email": account.email,
        "profile": account.model_dump(mode="json", exclude={"application_workspaces"}),
        "community_suspended_until": suspended_until.isoformat(),
        "created_at": account.created_at.isoformat(),
        "updated_at": account.updated_at.isoformat(),
    }
    session = _RecordingSession(
        {
            "status": CommunitySuspensionMutationStatus.COMMITTED.value,
            "account": account_payload,
            "audit": audit.model_dump(mode="json"),
        }
    )
    repository = SupabaseAccountRepository(
        "https://project.supabase.co",
        "server-secret",
        request_session=session,
    )
    request = CommunitySuspensionMutationRequest(
        event_id=audit.id,
        identity_id=audit.resource_id,
        account_id=account.id,
        moderator_id=audit.moderator_id,
        expected_suspended_until=None,
        suspended_until=suspended_until,
        reason=audit.note,
    )

    result = repository.commit_community_suspension(request)

    assert result.status == CommunitySuspensionMutationStatus.COMMITTED
    assert result.account == account
    assert result.audit == audit
    assert len(session.calls) == 1
    call = session.calls[0]
    assert call["method"] == "POST"
    assert call["url"].endswith("/rest/v1/rpc/exchange_commit_community_suspension")
    assert call["json"] == {
        "p_event_id": request.event_id,
        "p_identity_id": request.identity_id,
        "p_account_id": request.account_id,
        "p_moderator_id": request.moderator_id,
        "p_expected_suspended_until": None,
        "p_suspended_until": suspended_until.isoformat(),
        "p_reason": request.reason,
    }


def test_supabase_suspension_audit_list_purges_then_reads_private_rows() -> None:
    created_at = utc_now()
    previous_until = created_at + timedelta(hours=1)
    new_until = created_at + timedelta(days=7)
    retained_until = created_at + timedelta(days=90)
    session = _RecordingSession(
        {"deleted_count": 0, "purged_at": created_at.isoformat()},
        [
            {
                "id": "listed-suspension-event",
                "identity_id": "listed-identity",
                "moderator_id": None,
                "reason": "repeated abuse",
                "previous_suspended_until": previous_until.isoformat(),
                "new_suspended_until": new_until.isoformat(),
                "created_at": created_at.isoformat(),
                "retained_until": retained_until.isoformat(),
            }
        ],
    )
    repository = SupabaseAccountRepository(
        "https://project.supabase.co",
        "server-secret",
        request_session=session,
    )

    audits = repository.list_community_suspension_audits()

    assert len(audits) == 1
    assert audits[0].resource_type == "identity"
    assert audits[0].resource_id == "listed-identity"
    assert audits[0].previous_status == "suspended"
    assert audits[0].new_suspended_until == new_until
    assert audits[0].moderator_id == "deleted-moderator"
    assert len(session.calls) == 2
    assert session.calls[0]["url"].endswith(
        "/rest/v1/rpc/exchange_purge_expired_community_suspension_audits"
    )
    assert session.calls[1]["url"].endswith(
        "/rest/v1/exchange_community_suspension_audits"
    )
    assert "new_suspended_until" in session.calls[1]["params"]["select"]


def test_atomic_workspace_migration_has_db_owned_revision_and_private_rpc() -> None:
    sql = MIGRATION.read_text(encoding="utf-8").casefold()
    normalized = " ".join(sql.split())
    function_sql = sql.split(
        "create or replace function public.exchange_commit_account_workspace(",
        maxsplit=1,
    )[1].split("$$;", maxsplit=1)[0]

    assert "add column revision bigint" in sql
    assert "exchange_account_workspaces_revision_nonnegative" in sql
    assert "exchange_account_workspaces_revision_matches_payload" in sql
    assert "select account.* into v_account" in function_sql
    assert function_sql.index("select account.* into v_account") < function_sql.index(
        "select workspace.* into v_workspace"
    )
    assert "for update" in function_sql
    assert "v_current_revision <> p_expected_revision" in function_sql
    assert "v_next_revision := v_current_revision + 1" in function_sql
    assert "clock_timestamp()" in function_sql
    assert "- 'submission_progress'" in function_sql
    assert "'submission_progress', v_preserved_progress" in function_sql
    assert "'home_school_identity'" in function_sql
    assert "jsonb_agg(" in function_sql
    assert "'calendar_events', v_calendar_events" in function_sql
    assert (
        "revoke insert, update, delete on table public.exchange_account_workspaces "
        "from service_role"
    ) in normalized
    assert (
        "grant execute on function public.exchange_commit_account_workspace" in normalized
    )
    assert (
        "from public, anon, authenticated, service_role" in normalized
    )


def test_atomic_suspension_migration_is_audited_retained_and_service_only() -> None:
    sql = MIGRATION.read_text(encoding="utf-8").casefold()
    normalized = " ".join(sql.split())
    profile_patch_sql = sql.split(
        "create or replace function public.exchange_patch_account_profile(",
        maxsplit=1,
    )[1].split("$$;", maxsplit=1)[0]
    suspension_sql = sql.split(
        "create or replace function public.exchange_commit_community_suspension(",
        maxsplit=1,
    )[1].split("$$;", maxsplit=1)[0]

    assert "add column community_suspended_until timestamptz" in sql
    assert "community_suspended_until" not in profile_patch_sql.split(
        "v_allowed_fields text[] := array[", maxsplit=1
    )[1].split("];", maxsplit=1)[0]
    assert "exchange_community_suspension_audits" in sql
    assert "previous_suspended_until" in suspension_sql
    assert "new_suspended_until" in suspension_sql
    assert "request_fingerprint" in suspension_sql
    assert "sha256(" in suspension_sql
    assert "order by account.id" in suspension_sql
    assert suspension_sql.count("where audit.id = v_event_id") >= 3
    assert "perform set_config('exchange.community_suspension_write', 'on', true)" in normalized
    assert "v_commit_at + interval '2160 hours'" in suspension_sql
    assert "exchange_purge_expired_community_suspension_audits" in sql
    assert (
        "revoke update on table public.exchange_accounts from service_role"
        in normalized
    )
    assert (
        "revoke all on table public.exchange_community_suspension_audits "
        "from public, anon, authenticated, service_role"
    ) in normalized
    assert (
        "grant select on table public.exchange_community_suspension_audits to service_role"
    ) in normalized
    assert (
        "grant execute on function public.exchange_commit_community_suspension"
        in normalized
    )
