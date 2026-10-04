from __future__ import annotations

import re
from pathlib import Path


MIGRATION = (
    Path(__file__).parents[1]
    / "supabase"
    / "migrations"
    / "20260829100000_atomic_account_deletion.sql"
)


def _sql() -> str:
    return MIGRATION.read_text(encoding="utf-8").casefold()


def _function(name: str) -> str:
    match = re.search(
        rf"create or replace function public\.{re.escape(name)}\([\s\S]*?\n\$\$;",
        _sql(),
    )
    assert match is not None, f"missing function {name}"
    return match.group(0)


def test_account_deletion_receipt_is_private_durable_and_non_identifying() -> None:
    sql = _sql()
    table = sql.split(
        "create table public.exchange_account_deletion_receipts",
        maxsplit=1,
    )[1].split(");", maxsplit=1)[0]

    assert "request_fingerprint text not null" in table
    assert "replay_proof text not null" in table
    assert "response jsonb not null" in table
    assert "storage_completed_at timestamptz" in table
    assert "account_id" not in table
    assert "session_token_hash" not in table
    assert "enable row level security" in sql
    assert "force row level security" in sql
    assert (
        "revoke all on table public.exchange_account_deletion_receipts "
        "from public, anon, authenticated, service_role"
    ) in " ".join(sql.split())


def test_account_deletion_rebuilds_fingerprint_and_supports_authenticated_replay() -> None:
    commit = _function("exchange_commit_account_deletion")
    replay = _function("exchange_account_deletion_replay")

    assert "exchange_community_request_fingerprint" in commit
    assert "'operation', 'account_deletion'" in commit
    for field in (
        "'mutation_id', v_mutation_id",
        "'pending_report_retention_days', p_pending_report_retention_days",
        "'replacement_name', v_replacement_name",
        "'session_token_hash', v_session_token_hash",
    ):
        assert field in commit
    assert "exchange_account_deletion_replay_proof" in commit
    assert "v_receipt.request_fingerprint is distinct" in replay
    assert "v_receipt.replay_proof is distinct" in replay
    assert "jsonb_build_object('idempotent', true)" in replay
    assert commit.index("exchange_account_deletion_replay(") < commit.index(
        "if v_account_id is null or v_session_id is null"
    )


def test_account_deletion_uses_fixed_actor_lock_order_and_one_transaction() -> None:
    commit = _function("exchange_commit_account_deletion")
    account_lock = commit.index("from public.exchange_accounts account")
    session_lock = commit.index("from public.exchange_account_sessions session")
    identity_lock = commit.index("from public.exchange_community_identities identity")
    public_update = commit.index("update public.exchange_community_questions")
    account_delete = commit.index("delete from public.exchange_accounts account")
    receipt_insert = commit.index(
        "insert into public.exchange_account_deletion_receipts"
    )

    assert account_lock < session_lock < identity_lock < public_update
    assert public_update < account_delete < receipt_insert
    assert "order by identity.id" in commit
    assert commit.count("for update") >= 3
    assert "revoke delete on table public.exchange_accounts from service_role" in _sql()


def test_account_deletion_captures_storage_then_applies_retention_and_cascades() -> None:
    commit = _function("exchange_commit_account_deletion")
    storage_capture = commit.index("from public.exchange_vault_versions version")
    account_delete = commit.index("delete from public.exchange_accounts account")

    assert storage_capture < account_delete
    assert "'storage_object_keys', v_storage_object_keys" in commit
    assert "delete from public.exchange_community_private_conversations" in commit
    assert "delete from public.exchange_community_blocks" in commit
    assert "delete from public.exchange_community_mutation_receipts" in commit
    assert "receipt.actor_account_id = v_account_id" in commit
    assert "set reporter_id = null" in commit
    assert "make_interval(" in commit
    assert "delete from public.exchange_email_verifications" in commit
    assert "source_url = null" in commit


def test_storage_ack_is_proof_bound_and_only_completed_receipts_expire() -> None:
    sql = _sql()
    completion = _function("exchange_complete_account_deletion_storage")
    cleanup = _function("exchange_purge_account_deletion_receipts")

    assert "exchange_account_deletion_replay_proof" in completion
    assert "for update" in completion
    assert "v_receipt.replay_proof is distinct" in completion
    assert "storage_completed_at = coalesce" in completion
    assert "receipt.storage_completed_at is not null" in cleanup
    assert "receipt.retained_until <= clock_timestamp()" in cleanup
    assert (
        "grant execute on function public.exchange_commit_account_deletion( "
        "text, text, text, text, text, text, integer, text ) to service_role"
    ) in " ".join(sql.split())


def test_admin_cleanup_can_resume_pending_storage_without_exposing_table() -> None:
    sql = _sql()
    normalized = " ".join(sql.split())
    pending = _function("exchange_list_pending_account_deletion_storage")
    completion = _function(
        "exchange_complete_pending_account_deletion_storage"
    )

    assert "receipt.storage_completed_at is null" in pending
    assert "pending.response -> 'storage_object_keys'" in pending
    assert "order by receipt.created_at, receipt.mutation_id" in pending
    assert "limit p_limit" in pending
    assert "storage_completed_at = coalesce" in completion
    assert (
        "grant execute on function public.exchange_list_pending_account_deletion_storage"
        "(integer) to service_role"
    ) in normalized
