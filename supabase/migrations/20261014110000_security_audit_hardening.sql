-- Security audit remediation hardening for early RAG and document vault objects.
-- Pins pg_temp on trigger functions, revokes direct PostgREST RPC access from
-- anon/authenticated on match_document_chunks, and enforces FORCE ROW LEVEL
-- SECURITY + explicit table privilege grants on early RAG and vault tables.

alter function public.enforce_exchange_vault_consent_link()
  set search_path = public, pg_temp;

revoke all on function public.enforce_exchange_vault_consent_link()
  from public, anon, authenticated;

revoke all on function public.match_document_chunks(extensions.vector, double precision, integer, text)
  from public, anon, authenticated;

grant execute on function public.match_document_chunks(extensions.vector, double precision, integer, text)
  to service_role;

alter table public.universities force row level security;
alter table public.partner_universities force row level security;
alter table public.programs force row level security;
alter table public.eligibility_rules force row level security;
alter table public.deadlines force row level security;
alter table public.required_documents force row level security;
alter table public.scholarships force row level security;
alter table public.source_pages force row level security;
alter table public.structured_announcements force row level security;
alter table public.document_chunks force row level security;

alter table public.exchange_vault_documents force row level security;
alter table public.exchange_vault_versions force row level security;
alter table public.exchange_vault_consents force row level security;
alter table public.exchange_vault_audit_log force row level security;

revoke all on table
  public.universities,
  public.partner_universities,
  public.programs,
  public.eligibility_rules,
  public.deadlines,
  public.required_documents,
  public.scholarships,
  public.source_pages,
  public.structured_announcements,
  public.document_chunks,
  public.exchange_vault_documents,
  public.exchange_vault_versions,
  public.exchange_vault_consents,
  public.exchange_vault_audit_log
from public, anon, authenticated;

grant select, insert, update, delete on table
  public.universities,
  public.partner_universities,
  public.programs,
  public.eligibility_rules,
  public.deadlines,
  public.required_documents,
  public.scholarships,
  public.source_pages,
  public.structured_announcements,
  public.document_chunks
to service_role;
