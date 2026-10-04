from __future__ import annotations

import re
from pathlib import Path


MIGRATION = (
    Path(__file__).parents[1]
    / "supabase"
    / "migrations"
    / "20260824100000_atomic_private_community.sql"
)


def _sql() -> str:
    return MIGRATION.read_text(encoding="utf-8").casefold()


def _function(name: str) -> str:
    sql = _sql()
    match = re.search(
        rf"create or replace function public\.{re.escape(name)}\([\s\S]*?\n\$\$;",
        sql,
    )
    assert match is not None, f"missing function {name}"
    return match.group(0)


def test_private_community_tables_are_server_only_and_index_every_fk() -> None:
    sql = _sql()
    tables = (
        "exchange_community_private_conversations",
        "exchange_community_private_messages",
        "exchange_community_blocks",
        "exchange_community_reports",
    )
    for table in tables:
        assert f"create table public.{table}" in sql
        assert f"alter table public.{table} enable row level security" in sql
        assert f"revoke all on table public.{table} from anon, authenticated, service_role" in sql
        assert f"grant select on table public.{table} to service_role" in sql
    assert "exchange_private_conversations_sender_idx" in sql
    assert "exchange_private_conversations_recipient_idx" in sql
    assert "exchange_private_messages_conversation_idx" in sql
    assert "exchange_private_messages_author_idx" in sql
    assert "exchange_community_blocks_target_idx" in sql
    assert "exchange_community_reports_reporter_idx" in sql
    assert "exchange_community_reports_reviewer_idx" in sql


def test_private_mutations_share_idempotency_and_fixed_pair_lock_order() -> None:
    core = _function("exchange_commit_private_community_mutation")
    assert "exchange_community_request_fingerprint" in core
    assert "exchange_community_replay" in core
    assert "insert into public.exchange_community_mutation_receipts" in core
    account_lock = core.index("from public.exchange_accounts account")
    first_pair_lock = core.index("exchange.private.identity:")
    identity_lock = core.index("from public.exchange_community_identities identity")
    assert account_lock < first_pair_lock < identity_lock
    assert core.count("pg_advisory_xact_lock") == 2
    assert "least(v_identity_id" in core
    assert "greatest(v_identity_id" in core


def test_private_idempotency_hash_excludes_server_generated_resource_fields() -> None:
    core = _function("exchange_commit_private_community_mutation")
    fingerprint = core.index("v_expected_fingerprint :=")
    assert core.index("v_semantic_payload := jsonb_set") < fingerprint
    for field in (
        "- 'sender_name'",
        "- 'recipient_name'",
        "- 'conversation_id'",
        "- 'display_name'",
        "- 'reviewed_by'",
        "- 'retained_until'",
    ):
        assert field in core[:fingerprint]
    assert "'payload', v_semantic_payload" in core[fingerprint:]


def test_each_private_write_has_one_service_role_rpc_wrapper() -> None:
    sql = _sql()
    wrappers = {
        "exchange_commit_private_community_conversation": "private_conversation",
        "exchange_commit_private_community_conversation_status": "private_conversation_status",
        "exchange_commit_private_community_message": "private_message",
        "exchange_commit_private_community_block": "community_block",
        "exchange_commit_private_community_report": "community_report",
        "exchange_commit_private_community_report_review": "community_report_review",
    }
    for name, operation in wrappers.items():
        body = _function(name)
        assert "exchange_commit_private_community_mutation" in body
        assert f"'{operation}'" in body
        assert f"grant execute on function public.{name}" in sql
        assert f"revoke all on function public.{name}" in sql


def test_conversation_message_block_and_report_invariants_are_locked_in_sql() -> None:
    core = _function("exchange_commit_private_community_mutation")
    assert "conversation.sender_id = v_identity_id" in core
    assert "conversation.recipient_id = v_identity_id" in core
    assert "conversation.status <> 'accepted'" in core
    assert core.count("from public.exchange_community_blocks block") >= 3
    assert "return jsonb_build_object('status', 'blocked')" in core
    assert "return jsonb_build_object('status', 'conversation_required')" in core
    assert "exchange_community_reports_pending_unique" in _sql()
    assert "return jsonb_build_object('status', 'self_report')" in core
    report_message = core.index("select message.conversation_id into v_conversation_id")
    report_conversation_lock = core.index(
        "from public.exchange_community_private_conversations conversation",
        report_message,
    )
    report_message_lock = core.index(
        "select message.* into v_message",
        report_conversation_lock,
    )
    assert report_message < report_conversation_lock < report_message_lock


def test_report_review_updates_report_and_audit_in_one_transaction() -> None:
    sql = _sql()
    core = _function("exchange_commit_private_community_mutation")
    update_index = core.index("update public.exchange_community_reports report")
    audit_index = core.index("insert into public.exchange_community_moderation_audits")
    receipt_index = core.index("insert into public.exchange_community_mutation_receipts")
    assert update_index < audit_index < receipt_index
    assert "resource_type = 'report' and previous_status = 'pending'" in sql
    assert "resource_type = 'report' and new_status in ('resolved', 'dismissed')" in sql
    assert "retained_until <= v_now" in _function(
        "exchange_purge_private_community_operational_data"
    )


def test_account_deletion_preflight_removes_private_rows_and_deidentifies_pending_reports() -> None:
    sql = _sql()
    purge = _function("exchange_purge_private_community_identity")
    account_lock = purge.index("from public.exchange_accounts account")
    identity_lock = purge.index("from public.exchange_community_identities identity")
    conversation_delete = purge.index(
        "delete from public.exchange_community_private_conversations"
    )
    block_delete = purge.index("delete from public.exchange_community_blocks")
    report_update = purge.index("update public.exchange_community_reports report")
    receipt = purge.index("insert into public.exchange_community_mutation_receipts")
    assert account_lock < identity_lock < conversation_delete < block_delete < report_update < receipt
    assert "set reporter_id = null" in purge
    assert "make_interval(days => p_pending_report_retention_days)" in purge
    assert "where report.reporter_id = v_identity_id" in purge
    assert "and report.status = 'pending'" in purge
    assert "delete from public.exchange_community_reports report" in purge
    assert "grant execute on function public.exchange_purge_private_community_identity" in sql
    assert "revoke all on function public.exchange_purge_private_community_identity" in sql


def test_private_tables_cascade_identity_data_but_retain_deidentified_reports() -> None:
    sql = _sql()
    assert sql.count(
        "references public.exchange_community_identities(id) on delete cascade"
    ) >= 5
    reports = sql.split("create table public.exchange_community_reports", 1)[1].split(
        ");", 1
    )[0]
    assert "reporter_id text" in reports
    assert "on delete set null" in reports
    assert "reviewed_by text references public.exchange_accounts(id) on delete set null" in reports
