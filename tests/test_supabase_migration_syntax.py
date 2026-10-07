from pathlib import Path
import pytest
from scripts.validate_supabase_migrations import (
    DEFAULT_MIGRATION_DIR,
    MigrationValidationError,
    validate_migration,
    validate_migrations,
)

def test_all_supabase_migrations_parse_including_nested_function_bodies() -> None:
    summary = validate_migrations(DEFAULT_MIGRATION_DIR.glob("*.sql"))
    assert len(summary.results) == 28
    assert summary.statement_count == 553
    assert summary.sql_body_count == 11
    assert summary.plpgsql_unit_count == 66

    account_deletion = next(
        result
        for result in summary.results
        if result.path.name == "20260829100000_atomic_account_deletion.sql"
    )
    assert account_deletion.statement_count == 27
    assert account_deletion.sql_body_count == 1
    assert account_deletion.plpgsql_unit_count == 6

    issue_reports = next(
        result
        for result in summary.results
        if result.path.name == "20260830100000_application_workflow_issue_reports.sql"
    )
    assert issue_reports.statement_count == 29
    assert issue_reports.sql_body_count == 0
    assert issue_reports.plpgsql_unit_count == 4

def test_nested_plpgsql_syntax_error_is_rejected(tmp_path: Path) -> None:
    migration = tmp_path / "20260829000000_invalid.sql"
    migration.write_text(
        """
        create function public.invalid_example()
        returns void
        language plpgsql
        as $$
        begin
          if then
            return;
          end if;
        end;
        $$;
        """,
        encoding="utf-8",
    )
    with pytest.raises(MigrationValidationError, match="body parse failed"):
        validate_migration(migration)
