"""The browser roles may not call the function that turns row level security on for new tables."""
from __future__ import annotations

from pathlib import Path

SQL = Path("supabase/migrations/20261008110000_revoke_rls_auto_enable_api_access.sql").read_text(encoding="utf-8")


def test_the_browser_roles_lose_the_right_to_call_it() -> None:
    assert "revoke execute on function public.rls_auto_enable() from public, anon, authenticated;" in SQL


def test_the_owner_and_the_server_keep_it_and_the_trigger_is_left_alone() -> None:
    lowered = SQL.casefold()
    assert "service_role" not in lowered and "postgres" not in lowered.replace("owned by postgres", "")
    for forbidden in ("drop ", "alter function", "disable trigger", "drop event trigger"):
        assert forbidden not in lowered, forbidden


def test_a_project_without_the_function_is_not_an_error() -> None:
    assert "if to_regprocedure('public.rls_auto_enable()') is not null then" in SQL
