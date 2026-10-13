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
    assert len(summary.results) == 36
    assert summary.statement_count == 568
    assert summary.sql_body_count == 11
    assert summary.plpgsql_unit_count == 74

    school_boards = next(result for result in summary.results
                         if result.path.name == "20261009135343_ccu_ncu_school_board_compatibility.sql")
    assert school_boards.statement_count == 1
    assert school_boards.plpgsql_unit_count == 1

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

    governance_results = [result for result in summary.results
                          if result.path.name.endswith("_atomic_governance_commands.sql")]
    assert len(governance_results) == 1
    governance = governance_results[0]
    assert governance.statement_count == 4
    assert governance.sql_body_count == 0
    assert governance.plpgsql_unit_count == 2

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
