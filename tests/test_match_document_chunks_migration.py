"""The vector search function gets a fixed search path that still finds the vector operator."""
from __future__ import annotations

from pathlib import Path

SQL = Path("supabase/migrations/20261008120000_fix_match_document_chunks_search_path.sql").read_text(encoding="utf-8")
ORIGINAL = Path("supabase/migrations/202607190001_ai_rag.sql").read_text(encoding="utf-8")


def test_the_search_path_is_pinned_to_the_vector_schema_and_the_built_ins_only() -> None:
    assert "set search_path = extensions, pg_catalog;" in SQL
    assert "public" not in SQL.split("set search_path", 1)[1], "no user schema is searched, so nothing there can shadow an operator"


def test_it_alters_the_function_the_original_migration_created_with_the_same_signature() -> None:
    assert "create extension if not exists vector with schema extensions;" in ORIGINAL, "the operator lives in `extensions`"
    assert "create or replace function public.match_document_chunks(" in ORIGINAL
    assert "alter function public.match_document_chunks(extensions.vector, double precision, integer, text)" in SQL


def test_the_function_body_needs_nothing_outside_that_path() -> None:
    body = ORIGINAL.split("create or replace function public.match_document_chunks(", 1)[1].split("$$;", 1)[0]
    assert "public.document_chunks" in body, "the table is named in full"
    assert "<=>" in body and "extensions." not in body.split("as $$", 1)[1], "only the operator, found through the path"
