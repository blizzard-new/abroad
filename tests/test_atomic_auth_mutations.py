from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
import re
from threading import Barrier
from typing import Any
from unittest.mock import patch

import pytest

from exchange_info.models import (
    AccountProviderLink,
    AccountSessionRecord,
    AuthProvider,
    StudentVerificationMethod,
    UserAccount,
    utc_now,
)
from exchange_info.repositories import (
    AccountConflictError,
    AccountNotFoundError,
    AccountRepositoryError,
    CommunitySuspensionMutationRequest,
    CommunitySuspensionMutationStatus,
    JsonlAccountRepository,
    OAuthLoginMutationRequest,
    OAuthLoginMutationStatus,
    StudentVerificationMutationRequest,
    StudentVerificationMutationStatus,
    SupabaseAccountRepository,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    REPOSITORY_ROOT
    / "supabase"
    / "migrations"
    / "20260823100000_atomic_auth_account_mutations.sql"
)


def _oauth_request(
    *,
    provider: AuthProvider = AuthProvider.GOOGLE,
    subject: str = "google-subject-a",
    trusted_email: str | None = "student@example.com",
    new_account_id: str = "account-created-by-oauth",
    session_id: str = "oauth-session-a",
    token_hash: str = "a" * 64,
) -> OAuthLoginMutationRequest:
    now = utc_now()
    return OAuthLoginMutationRequest(
        provider=provider,
        subject=subject,
        trusted_email=trusted_email,
        display_name="OAuth Student",
        avatar_url="https://example.com/avatar.png",
        home_university="長庚大學",
        new_account_id=new_account_id,
        session_id=session_id,
        session_token_hash=token_hash,
        session_expires_at=now + timedelta(days=30),
        occurred_at=now,
    )


def test_jsonl_oauth_login_commits_account_link_and_session_together(tmp_path) -> None:
    repository = JsonlAccountRepository(tmp_path)
    request = _oauth_request()

    result = repository.commit_oauth_login(request)

    assert result.status == OAuthLoginMutationStatus.COMMITTED
    assert result.account is not None
    assert result.session is not None
    assert result.account.id == request.new_account_id
    assert result.account.email == "student@example.com"
    assert result.account.email_verified is True
    assert result.account.provider_links == [
        AccountProviderLink(provider=AuthProvider.GOOGLE, subject="google-subject-a")
    ]
    assert result.session.account_id == result.account.id
    assert repository.find_session_by_token_hash(request.session_token_hash) == result.session


def test_jsonl_oauth_login_rejects_same_provider_conflict_without_session(tmp_path) -> None:
    repository = JsonlAccountRepository(tmp_path)
    first = repository.commit_oauth_login(_oauth_request())
    assert first.status == OAuthLoginMutationStatus.COMMITTED

    conflict_request = _oauth_request(
        subject="google-subject-b",
        new_account_id="must-not-exist",
        session_id="must-not-exist",
        token_hash="b" * 64,
    )
    conflict = repository.commit_oauth_login(conflict_request)

    assert conflict.status == OAuthLoginMutationStatus.SAME_PROVIDER_CONFLICT
    assert conflict.account is None
    assert conflict.session is None
    assert repository.find_account_by_id("must-not-exist") is None
    assert repository.find_session_by_token_hash("b" * 64) is None
    assert len(repository.list_accounts()) == 1


def test_jsonl_concurrent_same_oauth_identity_resolves_one_account(tmp_path) -> None:
    barrier = Barrier(2)
    requests = [
        _oauth_request(
            new_account_id=f"candidate-{index}",
            session_id=f"session-{index}",
            token_hash=str(index + 1) * 64,
        )
        for index in range(2)
    ]

    def commit(request: OAuthLoginMutationRequest):
        repository = JsonlAccountRepository(tmp_path)
        barrier.wait()
        return repository.commit_oauth_login(request)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(commit, requests))

    assert [result.status for result in results] == [
        OAuthLoginMutationStatus.COMMITTED,
        OAuthLoginMutationStatus.COMMITTED,
    ]
    account_ids = {result.account.id for result in results if result.account}
    assert len(account_ids) == 1
    repository = JsonlAccountRepository(tmp_path)
    assert len(repository.list_accounts()) == 1
    assert all(
        repository.find_session_by_token_hash(request.session_token_hash)
        is not None
        for request in requests
    )


def test_jsonl_concurrent_different_subjects_for_same_email_have_one_winner(
    tmp_path,
) -> None:
    barrier = Barrier(2)
    requests = [
        _oauth_request(
            subject=f"google-subject-{index}",
            new_account_id=f"candidate-{index}",
            session_id=f"session-{index}",
            token_hash=str(index + 3) * 64,
        )
        for index in range(2)
    ]

    def commit(request: OAuthLoginMutationRequest):
        repository = JsonlAccountRepository(tmp_path)
        barrier.wait()
        return repository.commit_oauth_login(request)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(commit, requests))

    assert {result.status for result in results} == {
        OAuthLoginMutationStatus.COMMITTED,
        OAuthLoginMutationStatus.SAME_PROVIDER_CONFLICT,
    }
    repository = JsonlAccountRepository(tmp_path)
    assert len(repository.list_accounts()) == 1
    assert sum(
        repository.find_session_by_token_hash(request.session_token_hash)
        is not None
        for request in requests
    ) == 1


def test_jsonl_known_oauth_identity_cannot_switch_trusted_email(tmp_path) -> None:
    repository = JsonlAccountRepository(tmp_path)
    first = repository.commit_oauth_login(_oauth_request())
    assert first.status == OAuthLoginMutationStatus.COMMITTED

    switched = repository.commit_oauth_login(
        _oauth_request(
            trusted_email="other@example.com",
            new_account_id="unused-account",
            session_id="unused-session",
            token_hash="9" * 64,
        )
    )

    assert switched.status == OAuthLoginMutationStatus.VERIFIED_EMAIL_CONFLICT
    assert repository.find_account_by_email("other@example.com") is None
    assert repository.find_session_by_token_hash("9" * 64) is None


def test_oauth_mutation_request_rejects_unsupported_provider_contracts() -> None:
    base = _oauth_request().model_dump()
    with pytest.raises(ValueError, match="Google.*Facebook"):
        OAuthLoginMutationRequest(**{**base, "provider": AuthProvider.APPLE})
    with pytest.raises(ValueError, match="Facebook Email"):
        OAuthLoginMutationRequest(**{**base, "provider": AuthProvider.FACEBOOK})


def test_jsonl_oauth_rechecks_expiry_immediately_before_write(tmp_path) -> None:
    repository = JsonlAccountRepository(tmp_path)
    start = utc_now()
    request = _oauth_request().model_copy(
        update={
            "occurred_at": start - timedelta(seconds=1),
            "session_expires_at": start + timedelta(seconds=1),
        }
    )

    with patch(
        "exchange_info.repositories.utc_now",
        side_effect=[start, start + timedelta(seconds=2)],
    ):
        result = repository.commit_oauth_login(request)

    assert result.status == OAuthLoginMutationStatus.INTEGRITY_CONFLICT
    assert repository.list_accounts() == []
    assert repository.find_session_by_token_hash(request.session_token_hash) is None


def test_jsonl_student_verification_is_exact_session_cas_and_never_upserts(
    tmp_path,
) -> None:
    repository = JsonlAccountRepository(tmp_path)
    account = UserAccount(
        id="student-account",
        email="student@example.com",
        display_name="Student",
        email_verified=True,
        provider_links=[
            AccountProviderLink(
                provider=AuthProvider.EMAIL,
                subject="student@example.com",
            )
        ],
    )
    session = AccountSessionRecord(
        id="student-session",
        account_id=account.id,
        token_hash="c" * 64,
        expires_at=utc_now() + timedelta(days=1),
    )
    repository.save_account(account)
    repository.save_session(session)
    request = StudentVerificationMutationRequest(
        account_id=account.id,
        session_id=session.id,
        session_token_hash=session.token_hash,
        school_name="國立臺北大學",
        department_name="資訊工程學系",
        verification_method=StudentVerificationMethod.STUDENT_CARD,
        school_email_verified=False,
        verified_at=utc_now(),
    )

    wrong_session = repository.commit_student_verification(
        request.model_copy(update={"session_id": "wrong-session"})
    )
    assert wrong_session.status == StudentVerificationMutationStatus.SESSION_INVALID
    assert repository.find_account_by_id(account.id).student_status_verified is False

    committed = repository.commit_student_verification(request)
    assert committed.status == StudentVerificationMutationStatus.COMMITTED
    assert committed.account is not None
    assert committed.account.student_status_verified is True
    assert committed.account.verified_university == "國立臺北大學"
    assert committed.account.verified_department == "資訊工程學系"

    repository.delete_account(account.id)
    missing = repository.commit_student_verification(request)
    assert missing.status == StudentVerificationMutationStatus.ACCOUNT_MISSING
    assert repository.find_account_by_id(account.id) is None


def test_jsonl_stale_profile_save_cannot_downgrade_committed_auth_fields(
    tmp_path,
) -> None:
    repository = JsonlAccountRepository(tmp_path)
    account = UserAccount(
        id="student-account",
        email="student@example.com",
        display_name="Before",
        email_verified=True,
        provider_links=[
            AccountProviderLink(
                provider=AuthProvider.EMAIL,
                subject="student@example.com",
            )
        ],
    )
    session = AccountSessionRecord(
        id="student-session",
        account_id=account.id,
        token_hash="d" * 64,
        expires_at=utc_now() + timedelta(days=1),
    )
    repository.save_account(account)
    repository.save_session(session)
    committed = repository.commit_student_verification(
        StudentVerificationMutationRequest(
            account_id=account.id,
            session_id=session.id,
            session_token_hash=session.token_hash,
            school_name="國立臺北大學",
            department_name="資訊工程學系",
            verification_method=StudentVerificationMethod.STUDENT_CARD,
            verified_at=utc_now(),
        )
    )
    assert committed.status == StudentVerificationMutationStatus.COMMITTED

    repository.save_account(account.model_copy(update={"display_name": "After"}))

    current = repository.find_account_by_id(account.id)
    assert current is not None
    assert current.display_name == "After"
    assert current.student_status_verified is True
    assert current.home_university == "國立臺北大學"
    assert current.verified_university == "國立臺北大學"
    assert current.verified_department == "資訊工程學系"
    assert current.student_verification_method == StudentVerificationMethod.STUDENT_CARD


def test_jsonl_update_only_never_resurrects_deleted_account(tmp_path) -> None:
    repository = JsonlAccountRepository(tmp_path)
    account = repository.create_account(
        UserAccount(
            id="deleted-account",
            email="deleted@example.com",
            display_name="Deleted",
        )
    )
    stale = account.model_copy(update={"display_name": "Stale update"})
    repository.delete_account(account.id)

    with pytest.raises(AccountNotFoundError):
        repository.update_account(stale)

    assert repository.find_account_by_id(account.id) is None


def test_jsonl_field_patch_preserves_disjoint_security_state(tmp_path) -> None:
    repository = JsonlAccountRepository(tmp_path)
    account = repository.create_account(
        UserAccount(
            id="field-patch-account",
            display_name="Before",
            calendar_feed_token="calendar-token-before-revoke",
        )
    )
    moderator = repository.create_account(
        UserAccount(id="field-patch-moderator", display_name="Moderator")
    )
    suspended_until = utc_now() + timedelta(days=3)

    repository.patch_account_fields(
        account.id,
        {
            "calendar_feed_token": None,
            "calendar_events": [],
            "calendar_last_synced_at": None,
        },
    )
    repository.patch_account_fields(account.id, {"display_name": "After"})
    with pytest.raises(ValueError, match="community_suspended_until"):
        repository.patch_account_fields(
            account.id,
            {"community_suspended_until": suspended_until},
        )
    with pytest.raises(ValueError, match="application_workspaces"):
        repository.patch_account_fields(
            account.id,
            {"application_workspaces": []},
        )
    suspension = repository.commit_community_suspension(
        CommunitySuspensionMutationRequest(
            event_id="field-patch-suspension-event",
            identity_id="field-patch-identity",
            account_id=account.id,
            moderator_id=moderator.id,
            expected_suspended_until=None,
            suspended_until=suspended_until,
            reason="Repeated policy violations.",
        )
    )
    assert suspension.status == CommunitySuspensionMutationStatus.COMMITTED
    repository.patch_account_fields(
        account.id,
        {"target_countries": ["日本", "德國"]},
    )

    current = repository.find_account_by_id(account.id)
    assert current is not None
    assert current.display_name == "After"
    assert current.target_countries == ["日本", "德國"]
    assert current.calendar_feed_token is None
    assert current.community_suspended_until == suspended_until


def test_jsonl_calendar_expected_token_blocks_stale_reenable(tmp_path) -> None:
    repository = JsonlAccountRepository(tmp_path)
    old_token = "calendar-token-before-revoke"
    account = repository.create_account(
        UserAccount(
            id="calendar-cas-account",
            display_name="Calendar",
            calendar_feed_token=old_token,
        )
    )

    repository.patch_account_fields(
        account.id,
        {"calendar_feed_token": None, "calendar_events": []},
    )
    with pytest.raises(AccountConflictError):
        repository.patch_account_fields(
            account.id,
            {
                "calendar_feed_token": old_token,
                "calendar_last_synced_at": utc_now(),
            },
            expected={"calendar_feed_token": old_token},
        )

    current = repository.find_account_by_id(account.id)
    assert current is not None
    assert current.calendar_feed_token is None


def test_jsonl_field_patch_rejects_auth_owned_fields(tmp_path) -> None:
    repository = JsonlAccountRepository(tmp_path)
    account = repository.create_account(
        UserAccount(id="protected-patch-account", display_name="Protected")
    )

    with pytest.raises(ValueError, match="provider_links"):
        repository.patch_account_fields(
            account.id,
            {"provider_links": []},
        )


def test_jsonl_student_session_expiry_uses_repository_clock(tmp_path) -> None:
    repository = JsonlAccountRepository(tmp_path)
    now = utc_now()
    account = repository.create_account(
        UserAccount(id="expired-account", display_name="Expired")
    )
    session = AccountSessionRecord(
        id="expired-session",
        account_id=account.id,
        token_hash="f" * 64,
        expires_at=now - timedelta(minutes=1),
    )
    repository.save_session(session)

    result = repository.commit_student_verification(
        StudentVerificationMutationRequest(
            account_id=account.id,
            session_id=session.id,
            session_token_hash=session.token_hash,
            school_name="長庚大學",
            verification_method=StudentVerificationMethod.STUDENT_CARD,
            verified_at=now - timedelta(minutes=2),
        )
    )

    assert result.status == StudentVerificationMutationStatus.SESSION_INVALID
    assert repository.find_account_by_id(account.id).student_status_verified is False


class _FakeResponse:
    def __init__(self, payload: object) -> None:
        self._payload = payload
        self.content = b"payload"

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self._payload


class _FakeSession:
    def __init__(self, *payloads: object) -> None:
        self.payloads = list(payloads)
        self.calls: list[dict[str, Any]] = []

    def request(self, method: str, url: str, **kwargs: Any) -> _FakeResponse:
        self.calls.append({"method": method, "url": url, **kwargs})
        return _FakeResponse(self.payloads.pop(0))


def test_supabase_repository_uses_atomic_auth_rpcs() -> None:
    oauth_request = _oauth_request()
    account = UserAccount(
        id=oauth_request.new_account_id,
        email=oauth_request.trusted_email,
        display_name=oauth_request.display_name,
        avatar_url=oauth_request.avatar_url,
        email_verified=True,
        provider_links=[
            AccountProviderLink(
                provider=oauth_request.provider,
                subject=oauth_request.subject,
            )
        ],
        created_at=oauth_request.occurred_at,
        updated_at=oauth_request.occurred_at,
    )
    session = AccountSessionRecord(
        id=oauth_request.session_id,
        account_id=account.id,
        token_hash=oauth_request.session_token_hash,
        expires_at=oauth_request.session_expires_at,
        created_at=oauth_request.occurred_at,
    )
    student_request = StudentVerificationMutationRequest(
        account_id=account.id,
        session_id=session.id,
        session_token_hash=session.token_hash,
        school_name="國立臺北大學",
        department_name=None,
        verification_method=StudentVerificationMethod.MICROSOFT_ENTRA,
        school_email_verified=True,
        verified_at=utc_now(),
    )
    fake = _FakeSession(
        {
            "status": "committed",
            "account": {
                "id": account.id,
                "email": account.email,
                "profile": account.model_dump(
                    mode="json",
                    exclude={"application_workspaces"},
                ),
            },
            "session": session.model_dump(mode="json"),
        },
        {
            "status": "committed",
            "account": {
                "id": account.id,
                "email": account.email,
                "profile": account.model_copy(
                    update={
                        "student_status_verified": True,
                        "verified_university": "國立臺北大學",
                    }
                ).model_dump(mode="json", exclude={"application_workspaces"}),
            },
        },
    )
    repository = SupabaseAccountRepository(
        "https://project.supabase.co",
        "server-secret",
        request_session=fake,
    )

    oauth_result = repository.commit_oauth_login(oauth_request)
    student_result = repository.commit_student_verification(student_request)

    assert oauth_result.status == OAuthLoginMutationStatus.COMMITTED
    assert student_result.status == StudentVerificationMutationStatus.COMMITTED
    assert fake.calls[0]["url"].endswith(
        "/rest/v1/rpc/exchange_commit_oauth_login"
    )
    assert fake.calls[0]["json"]["p_session_token_hash"] == "a" * 64
    assert "access_token" not in fake.calls[0]["json"]
    assert "oauth_token" not in fake.calls[0]["json"]
    assert fake.calls[1]["url"].endswith(
        "/rest/v1/rpc/exchange_commit_student_verification"
    )
    assert fake.calls[1]["json"]["p_expected_session_id"] == session.id
    assert fake.calls[1]["json"]["p_school_email_verified"] is True
    assert "access_token" not in fake.calls[1]["json"]
    assert "claims" not in fake.calls[1]["json"]


def test_supabase_repository_maps_controlled_auth_statuses() -> None:
    oauth_request = _oauth_request()
    student_request = StudentVerificationMutationRequest(
        account_id="missing-account",
        session_id="missing-session",
        session_token_hash="e" * 64,
        school_name="長庚大學",
        verification_method=StudentVerificationMethod.STUDENT_CARD,
        verified_at=utc_now(),
    )
    fake = _FakeSession(
        {"status": "unverified_email_conflict"},
        {"status": "account_missing"},
        {"status": "not-a-real-status"},
    )
    repository = SupabaseAccountRepository(
        "https://project.supabase.co",
        "server-secret",
        request_session=fake,
    )

    oauth = repository.commit_oauth_login(oauth_request)
    student = repository.commit_student_verification(student_request)

    assert oauth.status == OAuthLoginMutationStatus.UNVERIFIED_EMAIL_CONFLICT
    assert oauth.account is None
    assert oauth.session is None
    assert student.status == StudentVerificationMutationStatus.ACCOUNT_MISSING
    assert student.account is None
    with pytest.raises(AccountRepositoryError, match="未知"):
        repository.commit_oauth_login(oauth_request)


def test_supabase_repository_uses_field_patch_rpc_and_expected_values() -> None:
    account = UserAccount(
        id="field-patch-account",
        display_name="After",
        calendar_feed_token=None,
    )
    fake = _FakeSession(
        {
            "status": "committed",
            "id": account.id,
            "email": account.email,
            "profile": account.model_dump(
                mode="json",
                exclude={"application_workspaces"},
            ),
            "created_at": account.created_at.isoformat(),
            "updated_at": account.updated_at.isoformat(),
        },
        [],
    )
    repository = SupabaseAccountRepository(
        "https://project.supabase.co",
        "server-secret",
        request_session=fake,
    )

    persisted = repository.patch_account_fields(
        account.id,
        {"display_name": "After"},
        expected={"calendar_feed_token": None},
    )

    assert persisted.display_name == "After"
    assert fake.calls[0]["url"].endswith(
        "/rest/v1/rpc/exchange_patch_account_profile"
    )
    assert fake.calls[0]["json"] == {
        "p_account_id": account.id,
        "p_updates": {"display_name": "After"},
        "p_expected": {"calendar_feed_token": None},
    }
    assert fake.calls[1]["method"] == "GET"


@pytest.mark.parametrize(
    ("status", "error_type"),
    [
        ("account_missing", AccountNotFoundError),
        ("conflict", AccountConflictError),
        ("unknown", AccountRepositoryError),
    ],
)
def test_supabase_field_patch_maps_controlled_statuses(status, error_type) -> None:
    fake = _FakeSession({"status": status})
    repository = SupabaseAccountRepository(
        "https://project.supabase.co",
        "server-secret",
        request_session=fake,
    )

    with pytest.raises(error_type):
        repository.patch_account_fields(
            "field-patch-account",
            {"display_name": "After"},
        )


def test_supabase_full_account_update_is_disabled_without_request() -> None:
    fake = _FakeSession()
    repository = SupabaseAccountRepository(
        "https://project.supabase.co",
        "server-secret",
        request_session=fake,
    )
    account = UserAccount(id="deleted-account", display_name="Deleted")

    with pytest.raises(AccountRepositoryError, match="整份帳號 update"):
        repository.update_account(account)

    assert fake.calls == []


def test_supabase_compatibility_upsert_is_disabled() -> None:
    fake = _FakeSession()
    repository = SupabaseAccountRepository(
        "https://project.supabase.co",
        "server-secret",
        request_session=fake,
    )

    with pytest.raises(AccountRepositoryError, match="不允許.*upsert"):
        repository.save_account(
            UserAccount(id="must-not-resurrect", display_name="Deleted")
        )

    assert fake.calls == []


def test_supabase_create_returns_canonical_row_and_full_update_is_disabled() -> None:
    account = UserAccount(
        id="canonical-account",
        email="student@example.com",
        display_name="Before",
        email_verified=True,
    )
    canonical = account.model_copy(update={"display_name": "Canonical persisted"})
    created_row = {
        "id": account.id,
        "email": account.email,
        "profile": canonical.model_dump(
            mode="json",
            exclude={"application_workspaces"},
        ),
        "created_at": account.created_at.isoformat(),
        "updated_at": account.updated_at.isoformat(),
    }
    fake = _FakeSession([created_row])
    repository = SupabaseAccountRepository(
        "https://project.supabase.co",
        "server-secret",
        request_session=fake,
    )

    created = repository.create_account(account)
    with pytest.raises(AccountRepositoryError, match="整份帳號 update"):
        repository.update_account(
            account.model_copy(update={"display_name": "After"})
        )

    assert created.id == account.id
    assert created.display_name == "Canonical persisted"
    assert len(fake.calls) == 1
    assert fake.calls[0]["method"] == "POST"
    assert "on_conflict" not in fake.calls[0]["params"]


def test_supabase_hydrate_uses_table_identity_over_stale_profile() -> None:
    stale = UserAccount(
        id="wrong-profile-id",
        email="wrong@example.com",
        display_name="Canonical",
    )
    canonical_created_at = utc_now() - timedelta(days=2)
    canonical_updated_at = utc_now() - timedelta(days=1)
    fake = _FakeSession(
        [
            {
                "id": "canonical-id",
                "email": "canonical@example.com",
                "profile": stale.model_dump(
                    mode="json",
                    exclude={"application_workspaces"},
                ),
                "created_at": canonical_created_at.isoformat(),
                "updated_at": canonical_updated_at.isoformat(),
            }
        ],
        [],
    )
    repository = SupabaseAccountRepository(
        "https://project.supabase.co",
        "server-secret",
        request_session=fake,
    )

    restored = repository.find_account_by_id("canonical-id")

    assert restored is not None
    assert restored.id == "canonical-id"
    assert restored.email == "canonical@example.com"
    assert restored.created_at == canonical_created_at
    assert restored.updated_at == canonical_updated_at


def test_atomic_auth_migration_enforces_private_unique_transactional_mutations() -> None:
    sql = MIGRATION.read_text(encoding="utf-8").casefold()

    assert "exchange_account_provider_links" in sql
    assert "primary key (provider, subject)" in sql
    assert "unique (account_id, provider)" in sql
    assert "exchange_commit_oauth_login" in sql
    assert "exchange_commit_student_verification" in sql
    assert "pg_advisory_xact_lock" in sql
    assert "for update" in sql
    assert "exchange_account_sessions" in sql
    assert "exchange_protect_auth_owned_account_fields" in sql
    assert "student_status_verified" in sql
    assert "student_verification_method" in sql
    assert "clock_timestamp()" in sql
    assert "'home_university', old.profile -> 'home_university'" in sql
    assert "enable row level security" in sql
    assert "from public, anon, authenticated" in sql
    assert "to service_role" in sql
    assert (
        "grant select on table public.exchange_account_provider_links to service_role"
        in sql
    )
    assert (
        "grant select, insert, update, delete\n"
        "  on table public.exchange_account_provider_links to service_role"
    ) not in sql
    oauth_sql, student_sql = sql.split(
        "create or replace function public.exchange_commit_student_verification",
        maxsplit=1,
    )
    oauth_clock = oauth_sql.index("v_commit_at := clock_timestamp()")
    assert oauth_sql.rfind("for update", 0, oauth_clock) >= 0
    assert "p_session_expires_at <= clock_timestamp()" in oauth_sql
    student_clock = student_sql.index("v_commit_at := clock_timestamp()")
    assert student_sql[:student_clock].count("for update") >= 2


def test_atomic_auth_migration_exposes_service_only_field_level_profile_cas() -> None:
    sql = MIGRATION.read_text(encoding="utf-8").casefold()
    function_marker = (
        "create or replace function public.exchange_patch_account_profile("
    )
    profile_patch_sql = sql.split(function_marker, maxsplit=1)[1].split(
        "$$;", maxsplit=1
    )[0]
    normalized = " ".join(profile_patch_sql.split())
    normalized_migration = " ".join(sql.split())

    assert "p_account_id text" in profile_patch_sql
    assert "p_updates jsonb" in profile_patch_sql
    assert "p_expected jsonb default '{}'::jsonb" in profile_patch_sql
    assert "security definer" in profile_patch_sql
    assert "from public.exchange_accounts account" in profile_patch_sql
    assert "for update" in profile_patch_sql
    assert "v_commit_at := clock_timestamp()" in profile_patch_sql
    assert "'status', 'account_missing'" in profile_patch_sql
    assert "'status', 'conflict'" in profile_patch_sql
    assert "jsonb_object_keys(p_updates)" in profile_patch_sql
    assert profile_patch_sql.count("jsonb_object_keys(p_expected)") >= 2
    assert (
        "coalesce(v_account.profile -> v_key, 'null'::jsonb) is distinct from "
        "coalesce(p_expected -> v_key, 'null'::jsonb)"
    ) in normalized
    assert "profile = account.profile || p_updates || jsonb_build_object(" in profile_patch_sql
    for field in ("id", "email", "profile", "created_at", "updated_at"):
        assert f"'{field}', v_account.{field}" in profile_patch_sql

    allowed_match = re.search(
        r"v_allowed_fields text\[\] := array\[(.*?)\];",
        profile_patch_sql,
        re.DOTALL,
    )
    assert allowed_match is not None
    allowed_fields = set(re.findall(r"'([a-z_]+)'", allowed_match.group(1)))
    assert {
        "display_name",
        "avatar_url",
        "home_university",
        "target_countries",
        "application_stage",
        "followed_boards",
        "notification_preferences",
        "content_updates_seen_at",
        "email_verified",
        "community_suspended_until",
        "calendar_feed_token",
        "calendar_events",
        "calendar_last_synced_at",
        "product_tier",
    } <= allowed_fields
    assert {
        "id",
        "email",
        "password_hash",
        "provider_links",
        "school_email_verified",
        "student_status_verified",
        "verified_university",
        "verified_department",
        "student_verification_method",
        "student_verified_at",
        "application_workspaces",
        "created_at",
        "updated_at",
    }.isdisjoint(allowed_fields)

    assert (
        "revoke all on function public.exchange_patch_account_profile"
        "(text, jsonb, jsonb) from public, anon, authenticated"
    ) in normalized_migration
    assert (
        "grant execute on function public.exchange_patch_account_profile"
        "(text, jsonb, jsonb) to service_role"
    ) in normalized_migration
    assert (
        "revoke update on table public.exchange_accounts from service_role"
        in normalized_migration
    )
