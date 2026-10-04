from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    ROOT
    / "supabase"
    / "migrations"
    / "20260823160000_atomic_public_community.sql"
)


def _sql() -> str:
    return MIGRATION.read_text(encoding="utf-8").casefold()


def _normalized() -> str:
    return " ".join(_sql().split())


def _function(
    name: str,
    first_parameter: str | None = None,
    *,
    last: bool = False,
) -> str:
    sql = _sql()
    signature = f"create or replace function public.{name}("
    if first_parameter is None:
        signature += ")"
    else:
        signature += f"\n  {first_parameter}"
    start = sql.rindex(signature) if last else sql.index(signature)
    return sql[start : sql.index("$$;", start) + 3]


PUBLIC_TABLES = (
    "exchange_community_identities",
    "exchange_community_questions",
    "exchange_community_answers",
    "exchange_community_posts",
    "exchange_community_post_comments",
    "exchange_community_public_chat_messages",
    "exchange_community_experience_submissions",
    "exchange_community_publish_events",
    "exchange_community_moderation_audits",
    "exchange_community_mutation_receipts",
)


def test_schema_has_identity_six_public_resources_and_operational_tables() -> None:
    sql = _sql()
    for table in PUBLIC_TABLES:
        assert f"create table public.{table} (" in sql

    identity_table = sql.split(
        "create table public.exchange_community_identities (", maxsplit=1
    )[1].split("create table public.exchange_community_questions (", maxsplit=1)[0]
    assert "account_id text unique" in identity_table
    assert "account_id text not null" not in identity_table
    assert "references public.exchange_accounts(id) on delete cascade" in identity_table
    assert "access_token_hash text not null unique" in identity_table

    assert "'question', 'answer', 'post', 'comment', 'chat', 'experience'" in sql
    assert "'public_chat'" not in sql
    assert "check (status in ('pending', 'approved', 'hidden'))" in sql
    assert "revision bigint not null default 0" in sql


def test_every_fk_lookup_and_retention_path_has_an_index() -> None:
    sql = _sql()
    required_indexes = (
        "exchange_community_questions_author_idx",
        "exchange_community_answers_question_idx",
        "exchange_community_answers_author_idx",
        "exchange_community_posts_author_idx",
        "exchange_community_post_comments_post_idx",
        "exchange_community_post_comments_author_idx",
        "exchange_community_public_chat_messages_author_idx",
        "exchange_community_experience_submissions_author_idx",
        "exchange_community_publish_events_account_window_idx",
        "exchange_community_publish_events_identity_idx",
        "exchange_community_moderation_audits_moderator_idx",
        "exchange_community_moderation_audits_retention_idx",
        "exchange_community_mutation_receipts_account_idx",
        "exchange_community_mutation_receipts_identity_idx",
        "exchange_community_mutation_receipts_retention_idx",
    )
    for index in required_indexes:
        assert f"create index {index}" in sql
    assert sql.count("where status = 'approved'") >= 4
    assert sql.count("where status = 'pending'") >= 6


def test_tables_are_force_rls_and_service_role_has_read_only_table_access() -> None:
    sql = _sql()
    normalized = _normalized()
    assert sql.count(" enable row level security;") == len(PUBLIC_TABLES)
    assert sql.count(" force row level security;") == len(PUBLIC_TABLES)
    for table in PUBLIC_TABLES:
        assert f"alter table public.{table} enable row level security;" in sql
        assert f"alter table public.{table} force row level security;" in sql
        assert (
            f"revoke all on table public.{table} "
            "from public, anon, authenticated, service_role"
        ) in normalized
        assert f"grant select on table public.{table} to service_role" in normalized
    assert "grant insert" not in normalized
    assert "grant update" not in normalized
    assert "grant delete" not in normalized


def test_adapter_rpcs_are_security_definer_and_service_role_only() -> None:
    sql = _sql()
    normalized = _normalized()
    rpc_signatures = (
        "exchange_commit_community_identity( text, text, jsonb )",
        "exchange_commit_public_community_publication( text, text, text, text, text, text, jsonb )",
        "exchange_delete_public_community_content( text, text, text, text, text, text, text )",
        "exchange_commit_public_community_moderation( text, text, text, text, text, text, text, text )",
        "exchange_anonymize_public_community_author( text, text, text, text, text )",
        "exchange_purge_public_community_operational_data()",
    )
    for signature in rpc_signatures:
        assert f"revoke all on function public.{signature}" in normalized
        assert f"grant execute on function public.{signature} to service_role" in normalized

    assert sql.count("security definer") >= 12
    grant_statements = [
        statement.strip()
        for statement in normalized.split(";")
        if "grant execute on function" in statement
    ]
    assert grant_statements
    assert all(statement.endswith("to service_role") for statement in grant_statements)
    assert (
        "revoke all on function public.exchange_commit_public_community_content( "
        "text, text, text, text, text, text, jsonb )"
    ) in normalized
    identity_create = normalized.index(
        "create or replace function public.exchange_commit_community_identity( "
        "p_mutation_id text"
    )
    identity_revoke = normalized.index(
        "revoke all on function public.exchange_commit_community_identity( "
        "text, text, jsonb )"
    )
    identity_grant = normalized.index(
        "grant execute on function public.exchange_commit_community_identity( "
        "text, text, jsonb )"
    )
    assert identity_create < identity_revoke < identity_grant


def test_identity_rpc_supports_legacy_but_publish_requires_exact_link() -> None:
    identity = _function("exchange_commit_community_identity", "p_mutation_id text")
    publish = _function(
        "exchange_commit_public_community_publication", "p_mutation_id text"
    )
    internal_publish = _function(
        "exchange_commit_public_community_content", "p_event_id text", last=True
    )
    suspension_binding = _function(
        "exchange_validate_community_suspension_identity_binding"
    )

    assert "if v_account_id is not null then" in identity
    assert "-- legacy path has no account row" in identity
    assert "if found and v_identity.account_id is not null" in identity
    assert "id, account_id, display_name, access_token_hash" in identity
    assert identity.index("from public.exchange_accounts account") < identity.index(
        "from public.exchange_community_identities identity"
    )
    assert "order by identity.id" in identity
    assert "identity.account_id is distinct from v_account_id" in internal_publish
    assert "identity.access_token_hash is distinct from v_token_hash" in internal_publish
    assert "v_resource_id text := nullif(btrim(p_content ->> 'id'), '')" in publish

    assert "from public.exchange_community_identities identity" in suspension_binding
    assert "for update" in suspension_binding
    assert "v_bound_account_id is distinct from new.target_account_id" in suspension_binding
    assert "before insert on public.exchange_community_suspension_audits" in _sql()


def test_database_rebuilds_canonical_fingerprint_and_publication_uses_semantics() -> None:
    sql = _sql()
    publication = _function(
        "exchange_commit_public_community_publication", "p_mutation_id text"
    )
    fingerprint_block = publication.split(
        "v_fingerprint := public.exchange_community_request_fingerprint(", maxsplit=1
    )[1].split("if v_supplied_fingerprint", maxsplit=1)[0]

    assert "exchange_community_canonical_json" in sql
    assert "string_agg(" in sql
    assert "sha256(" in sql
    assert "convert_to(public.exchange_community_canonical_json" in sql
    assert "v_supplied_fingerprint is distinct from v_fingerprint" in publication
    assert "'operation', 'publication'" in fingerprint_block
    assert "'mutation_id'" not in fingerprint_block
    assert "'content', v_semantic_content" in fingerprint_block
    assert "v_semantic_content := v_payload - 'status'" in publication
    assert "'id', 'author_id', 'author_identity_id', 'display_name', 'created_at'" in publication
    # API-computed moderation status is excluded only from the hash; the locked
    # persistence payload still carries and allowlists it.
    assert "v_payload := p_content - array[" in publication
    assert "'viewer_can_delete', 'verified_experience'" in publication
    assert "v_payload := p_content - array[" in publication
    assert "v_payload - 'status'" in publication
    assert "v_payload\n" in publication


def test_publish_is_atomic_parent_validated_and_rate_limited_under_account_lock() -> None:
    publish = _function(
        "exchange_commit_public_community_content", "p_event_id text", last=True
    )
    display_name = _function(
        "exchange_community_display_name", "p_profile jsonb"
    )
    assert publish.index("select account.* into v_account") < publish.index(
        "select identity.* into v_identity"
    )
    assert publish.index("select identity.* into v_identity") < publish.index(
        "select question.* into v_question"
    )
    assert "for update" in publish
    assert "v_account.community_suspended_until" in publish
    assert "v_publish_limit := case" in publish
    assert "then 5" in publish
    assert "else 20" in publish
    assert "interval '10 minutes'" in publish
    assert "clock_timestamp()" in publish
    assert "'retry_after_seconds', 600" in publish
    assert publish.count("coalesce(") >= 2
    assert "v_account.profile -> 'email_verified' = 'true'::jsonb" in publish
    assert "v_account.profile -> 'student_status_verified' = 'true'::jsonb" in publish
    assert "v_student_verified boolean := coalesce(" in display_name
    assert "if not found or v_question.status = 'hidden'" in publish
    assert "if not found or v_post.status = 'hidden'" in publish
    assert "insert into public.exchange_community_publish_events" in publish
    assert "insert into public.exchange_community_mutation_receipts" in publish
    assert "exception" in publish
    assert publish.count("returning * into") >= 6


def test_delete_uses_owner_binding_parent_before_child_and_same_receipt() -> None:
    delete = _function(
        "exchange_delete_public_community_content", "p_event_id text", last=True
    )
    assert delete.index("select account.* into v_account") < delete.index(
        "select identity.* into v_identity"
    )
    assert delete.index("select post.* into v_post") < delete.index(
        "select comment.* into v_comment"
    )
    assert "author_identity_id is distinct from v_identity_id" in delete
    assert "'status', 'not_owner'" in delete
    assert "delete from public.exchange_community_posts" in delete
    assert "delete from public.exchange_community_post_comments" in delete
    assert "select count(*) into v_deleted_comment_count" in delete
    assert "'deleted_comment_count', v_deleted_comment_count" in delete
    assert "insert into public.exchange_community_mutation_receipts" in delete


def test_moderation_is_status_cas_with_parent_locks_audit_and_receipt() -> None:
    moderation = _function(
        "exchange_commit_public_community_moderation", "p_mutation_id text"
    )
    assert "p_expected_status text" in moderation
    assert moderation.index("select account.* into v_moderator") < moderation.index(
        "select question.* into v_question"
    )
    assert moderation.index("select question.* into v_question") < moderation.index(
        "select answer.* into v_answer"
    )
    assert moderation.index("select post.* into v_post") < moderation.index(
        "select comment.* into v_comment"
    )
    assert "v_current_status is distinct from v_expected_status" in moderation
    assert "'status', 'status_conflict'" in moderation
    assert "'status', 'no_change'" in moderation
    assert "revision = question.revision + 1" in moderation
    assert "insert into public.exchange_community_moderation_audits" in moderation
    assert "v_now + interval '2160 hours'" in moderation
    assert "insert into public.exchange_community_mutation_receipts" in moderation
    assert "when integrity_constraint_violation or data_exception" in moderation


def test_moderation_audits_are_append_only_retained_90_days_and_purge_guarded() -> None:
    sql = _sql()
    normalized = _normalized()
    audit_table = sql.split(
        "create table public.exchange_community_moderation_audits (", maxsplit=1
    )[1].split(
        "create table public.exchange_community_mutation_receipts (", maxsplit=1
    )[0]
    purge = _function("exchange_purge_public_community_operational_data")
    assert "retained_until = created_at + interval '2160 hours'" in audit_table
    assert "community moderation audits are append-only" in sql
    assert "exchange.community_moderation_audit_purge" in purge
    assert "where audit.retained_until <= v_now" in purge
    assert "where receipt.retained_until <= v_now" in purge
    assert "event.occurred_at <= v_now - interval '24 hours'" in purge
    assert "grant execute on function public.exchange_purge_public_community_operational_data() to service_role" in normalized


def test_account_delete_anonymization_is_atomic_and_keeps_identity_for_later_fk() -> None:
    anonymize = _function(
        "exchange_anonymize_public_community_author", "p_mutation_id text"
    )
    assert anonymize.index("from public.exchange_accounts account") < anonymize.index(
        "from public.exchange_community_identities identity"
    )
    for table in (
        "exchange_community_questions",
        "exchange_community_answers",
        "exchange_community_posts",
        "exchange_community_post_comments",
        "exchange_community_public_chat_messages",
        "exchange_community_experience_submissions",
    ):
        assert f"update public.{table}" in anonymize
    assert anonymize.count("set author_identity_id = null") == 6
    assert "source_url = null" in anonymize
    assert "delete from public.exchange_community_publish_events" in anonymize
    assert "'publish_event', v_count" in anonymize
    assert "insert into public.exchange_community_mutation_receipts" in anonymize
    assert "delete from public.exchange_community_identities" not in anonymize


def test_private_chat_block_and_report_persistence_remain_out_of_this_stage() -> None:
    sql = _sql()
    assert "create table public.exchange_community_private" not in sql
    assert "create table public.exchange_community_blocks" not in sql
    assert "create table public.exchange_community_reports" not in sql
    assert "exchange_commit_private" not in sql
    assert "exchange_commit_community_report" not in sql
