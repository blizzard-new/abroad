-- match_document_chunks() had no fixed search_path, so the schemas it searches depended on whoever called it
-- (Supabase's security advisor flags that). It reads public.document_chunks by its full name and needs only the
-- pgvector operator, which lives in the `extensions` schema (see 202607190001_ai_rag.sql), plus the built-ins in
-- pg_catalog. Pin exactly those.

alter function public.match_document_chunks(extensions.vector, double precision, integer, text)
  set search_path = extensions, pg_catalog;
