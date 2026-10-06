"""The migration that lets a picked school replace the student-card check patches four deployed functions in place.

It was not run against a real PostgreSQL here, so these tests check what can be checked offline: every line it searches for
really is in the latest source of the function it patches, it refuses to continue when a line is missing, and it can be run
again without effect.
"""
from __future__ import annotations

import re
from pathlib import Path

MIGRATIONS = Path(__file__).parents[1] / "supabase" / "migrations"
MIGRATION = MIGRATIONS / "20261007100000_school_choice_replaces_student_card.sql"

# (function, how many search strings the migration holds for it)
PATCHED = (
    ("exchange_patch_account_profile", 1),
    ("exchange_community_display_name", 2),
    ("exchange_commit_public_community_content", 1),
    ("exchange_submit_application_workflow_issue_report", 1),
)


def _sql() -> str:
    return MIGRATION.read_text(encoding="utf-8").replace("\r\n", "\n")


def _latest_source(function: str) -> str:
    pattern = re.compile(rf"create\s+or\s+replace\s+function\s+public\.{function}\b", re.IGNORECASE)
    owners = [path for path in sorted(MIGRATIONS.glob("*.sql")) if path != MIGRATION and pattern.search(path.read_text(encoding="utf-8"))]
    assert owners, f"no migration defines {function}"
    return owners[-1].read_text(encoding="utf-8").replace("\r\n", "\n")


def test_every_search_string_is_in_the_latest_source_of_its_function() -> None:
    searches = re.findall(r"v_old := \$p\$(.*?)\$p\$;", _sql(), re.DOTALL)
    assert len(searches) == sum(count for _, count in PATCHED)
    cursor = 0
    for function, count in PATCHED:
        source = _latest_source(function)
        for search in searches[cursor:cursor + count]:
            assert search in source, f"{function}: the migration looks for text that is not there:\n{search}"
        cursor += count


def test_each_step_stops_when_its_text_is_missing_and_is_skipped_once_applied() -> None:
    sql = _sql()
    assert sql.count("raise exception") >= 8, "a missing function or missing text must abort, not silently do nothing"
    for function, _ in PATCHED:
        assert f"p.proname = '{function}'" in sql
    # Each step is guarded by a marker that only the patched function contains.
    assert "position('''home_university_changed_at''' in v_def) = 0" in sql
    assert "position('v_account.profile ->> ''home_university''' in v_def) = 0" in sql


def test_the_school_counts_as_long_as_it_is_set_and_not_the_unset_placeholder() -> None:
    sql = _sql()
    assert sql.count("'尚未選擇'") == 3, "the placeholder an account has before it picks a school never counts as a school"
    assert "coalesce(v_verified_school_key, '') <> ''" in sql, "a null key must not turn the check into null"
    assert "if p_identity_mode = 'verified_school' and v_school is not null then" in sql


def test_the_migration_only_changes_functions_and_touches_no_data() -> None:
    body = re.sub(r"\$p\$.*?\$p\$", "", _sql(), flags=re.DOTALL).casefold()
    for forbidden in ("drop ", "delete ", "truncate ", "update public.", "insert into", "alter table"):
        assert forbidden not in body, forbidden


def test_the_sql_parses() -> None:
    pglast = __import__("pytest").importorskip("pglast")
    assert pglast.parse_sql(_sql())
