"""The feedback table: only the server may touch it, and its limits match what the server accepts."""
from __future__ import annotations

import re
from pathlib import Path

from exchange_info.feedback import FeedbackSubmission, SupabaseFeedbackRepository

SQL = Path("supabase/migrations/20261008100000_user_feedback.sql").read_text(encoding="utf-8")


def test_the_table_is_the_one_the_server_writes_to() -> None:
    assert f"create table if not exists public.{SupabaseFeedbackRepository.TABLE} (" in SQL


def test_the_browser_roles_get_nothing_and_every_row_is_protected() -> None:
    table = SupabaseFeedbackRepository.TABLE
    assert f"alter table public.{table} enable row level security;" in SQL
    assert f"alter table public.{table} force row level security;" in SQL
    assert f"revoke all on public.{table} from public, anon, authenticated;" in SQL
    grants = re.findall(r"grant ([^;]+) on public\.[a-z_]+ to ([a-z_, ]+);", SQL)
    assert grants == [("select, insert, update, delete", "service_role")]
    assert "policy" not in SQL.casefold(), "no policy: nobody but the service role can reach a row"


def test_nothing_that_identifies_the_sender_has_a_column() -> None:
    columns = re.findall(r"^  ([a-z_]+) ", SQL.split("create table", 1)[1].split(");", 1)[0], flags=re.M)
    assert columns == ["id", "created_at", "kind", "rating", "message", "contact", "route", "home_school", "signed_in",
                       "status", "admin_note", "handled_at"]
    for word in ("ip", "email", "account_id", "user_id", "user_agent"):
        assert word not in columns


def test_the_database_limits_match_what_the_server_accepts() -> None:
    fields = FeedbackSubmission.model_fields
    assert f"char_length(message) between {fields['message'].metadata[0].min_length} and {fields['message'].metadata[1].max_length}" in SQL
    assert f"char_length(contact) <= {fields['contact'].metadata[0].max_length}" in SQL
    assert f"char_length(route) <= {fields['route'].metadata[0].max_length}" in SQL
    assert f"char_length(home_school) <= {fields['home_school'].metadata[0].max_length}" in SQL
    assert "kind in ('suggestion', 'bug', 'praise', 'other')" in SQL
    assert "status in ('new', 'read', 'done')" in SQL
    assert "rating between 1 and 5" in SQL
