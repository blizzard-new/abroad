"""Parse Supabase migrations, including SQL and PL/pgSQL function bodies."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from pglast import parse_sql
from pglast.parser import parse_plpgsql_json
from pglast.stream import RawStream


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MIGRATION_DIR = PROJECT_ROOT / "supabase" / "migrations"


class MigrationValidationError(RuntimeError):
    """Raised when a migration or a nested function body cannot be parsed."""


@dataclass(frozen=True)
class MigrationValidationResult:
    path: Path
    statement_count: int
    sql_body_count: int
    plpgsql_unit_count: int


@dataclass(frozen=True)
class MigrationValidationSummary:
    results: tuple[MigrationValidationResult, ...]

    @property
    def statement_count(self) -> int:
        return sum(result.statement_count for result in self.results)

    @property
    def sql_body_count(self) -> int:
        return sum(result.sql_body_count for result in self.results)

    @property
    def plpgsql_unit_count(self) -> int:
        return sum(result.plpgsql_unit_count for result in self.results)


def _function_options(statement: object) -> dict[str, object]:
    return {
        option.defname: option.arg
        for option in (getattr(statement, "options", None) or ())
    }


def _function_name(statement: object) -> str:
    return ".".join(
        part.sval for part in (getattr(statement, "funcname", None) or ())
    )


def validate_migration(path: Path) -> MigrationValidationResult:
    try:
        statements = parse_sql(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pglast exposes parser-specific exception types.
        raise MigrationValidationError(
            f"{path.name}: top-level SQL parse failed: {exc}"
        ) from exc

    sql_body_count = 0
    plpgsql_unit_count = 0
    for raw_statement in statements:
        statement = raw_statement.stmt
        statement_kind = type(statement).__name__
        try:
            if statement_kind == "DoStmt":
                parse_plpgsql_json(RawStream()(statement))
                plpgsql_unit_count += 1
                continue
            if statement_kind != "CreateFunctionStmt":
                continue

            options = _function_options(statement)
            language = getattr(options.get("language"), "sval", "sql").lower()
            if language == "plpgsql":
                parse_plpgsql_json(RawStream()(statement))
                plpgsql_unit_count += 1
            elif language == "sql":
                bodies = options.get("as") or ()
                if bodies:
                    parse_sql(bodies[0].sval)
                    sql_body_count += 1
        except Exception as exc:
            unit = (
                f"function {_function_name(statement)}"
                if statement_kind == "CreateFunctionStmt"
                else f"DO block at byte {raw_statement.stmt_location}"
            )
            raise MigrationValidationError(
                f"{path.name}: {unit} body parse failed: {exc}"
            ) from exc

    return MigrationValidationResult(
        path=path,
        statement_count=len(statements),
        sql_body_count=sql_body_count,
        plpgsql_unit_count=plpgsql_unit_count,
    )


def validate_migrations(paths: Iterable[Path]) -> MigrationValidationSummary:
    migration_paths = tuple(sorted(paths))
    if not migration_paths:
        raise MigrationValidationError("no Supabase migration files were found")
    return MigrationValidationSummary(
        results=tuple(validate_migration(path) for path in migration_paths)
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Parse every Supabase migration and nested SQL/PL/pgSQL function body."
        )
    )
    parser.add_argument(
        "migration_dir",
        nargs="?",
        type=Path,
        default=DEFAULT_MIGRATION_DIR,
        help="migration directory (default: supabase/migrations)",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    migration_dir = args.migration_dir.resolve()
    try:
        summary = validate_migrations(migration_dir.glob("*.sql"))
    except (OSError, MigrationValidationError) as exc:
        print(f"Supabase migration validation failed: {exc}")
        return 1

    for result in summary.results:
        print(
            f"{result.path.name}: {result.statement_count} statements, "
            f"{result.sql_body_count} SQL bodies, "
            f"{result.plpgsql_unit_count} PL/pgSQL units"
        )
    print(
        f"Validated {len(summary.results)} migrations: "
        f"{summary.statement_count} statements, "
        f"{summary.sql_body_count} SQL bodies, "
        f"{summary.plpgsql_unit_count} PL/pgSQL units"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
