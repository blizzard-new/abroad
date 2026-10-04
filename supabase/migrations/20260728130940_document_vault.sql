-- Server-only metadata for the encrypted private document vault.
-- The ciphertext objects live in a separate private Storage bucket and are
-- managed through the Storage API; this migration intentionally does not write
-- to Supabase's internal storage schema.

create table if not exists public.exchange_vault_documents (
  id text primary key,
  account_id text not null
    references public.exchange_accounts(id) on delete cascade,
  label_ciphertext text not null,
  label_nonce text not null,
  category text not null,
  latest_version integer not null default 1,
  version_count integer not null default 1,
  created_at timestamptz not null,
  updated_at timestamptz not null,
  constraint exchange_vault_documents_id_account_unique unique (id, account_id),
  constraint exchange_vault_documents_category_check check (
    category in (
      'application_form', 'generated_packet', 'passport', 'transcript',
      'student_id', 'financial_proof', 'recommendation', 'study_plan', 'other'
    )
  ),
  constraint exchange_vault_documents_version_check check (
    latest_version >= 1 and version_count >= 1
  )
);

create table if not exists public.exchange_vault_versions (
  id text primary key,
  document_id text not null,
  account_id text not null
    references public.exchange_accounts(id) on delete cascade,
  version_number integer not null,
  file_name_ciphertext text not null,
  file_name_nonce text not null,
  media_type text not null,
  plaintext_size integer not null,
  plaintext_sha256 text not null,
  ciphertext_size integer not null,
  ciphertext_sha256 text not null,
  object_key text not null unique,
  encryption_algorithm text not null default 'AES-256-GCM',
  wrapped_data_key text not null,
  wrap_nonce text not null,
  content_nonce text not null,
  consent_id text not null unique,
  retention_expires_at timestamptz not null,
  created_at timestamptz not null,
  constraint exchange_vault_versions_number_unique
    unique (document_id, version_number),
  constraint exchange_vault_versions_document_owner_fk
    foreign key (document_id, account_id)
    references public.exchange_vault_documents(id, account_id) on delete cascade,
  constraint exchange_vault_versions_number_check check (version_number >= 1),
  constraint exchange_vault_versions_size_check check (
    plaintext_size between 1 and 20971520 and ciphertext_size > 0
  ),
  constraint exchange_vault_versions_plain_hash_check check (
    plaintext_sha256 ~ '^[0-9a-f]{64}$'
  ),
  constraint exchange_vault_versions_cipher_hash_check check (
    ciphertext_sha256 ~ '^[0-9a-f]{64}$'
  ),
  constraint exchange_vault_versions_algorithm_check check (
    encryption_algorithm = 'AES-256-GCM'
  )
);

create table if not exists public.exchange_vault_consents (
  id text primary key,
  account_id text not null
    references public.exchange_accounts(id) on delete cascade,
  document_id text not null
    references public.exchange_vault_documents(id) on delete cascade,
  version_id text not null unique
    references public.exchange_vault_versions(id) on delete cascade,
  purpose text not null,
  retention_days integer not null,
  terms_version text not null,
  granted_at timestamptz not null,
  expires_at timestamptz not null,
  revoked_at timestamptz,
  constraint exchange_vault_consents_purpose_check check (
    purpose in (
      'application_preparation', 'cross_device_access',
      'generated_packet_backup'
    )
  ),
  constraint exchange_vault_consents_retention_check check (
    retention_days between 1 and 365
  ),
  constraint exchange_vault_consents_expiry_check check (expires_at > granted_at)
);

create or replace function public.enforce_exchange_vault_consent_link()
returns trigger
language plpgsql
set search_path = public
as $$
begin
  if not exists (
    select 1
    from public.exchange_vault_versions as version
    where version.id = new.version_id
      and version.consent_id = new.id
      and version.document_id = new.document_id
      and version.account_id = new.account_id
  ) then
    raise exception 'vault consent does not match its encrypted document version';
  end if;
  return new;
end;
$$;

drop trigger if exists exchange_vault_consent_link_trigger
  on public.exchange_vault_consents;
create trigger exchange_vault_consent_link_trigger
before insert or update on public.exchange_vault_consents
for each row execute function public.enforce_exchange_vault_consent_link();

revoke all on function public.enforce_exchange_vault_consent_link() from public;

create table if not exists public.exchange_vault_audit_log (
  id text primary key,
  subject_fingerprint text not null,
  document_id text,
  version_id text,
  action text not null,
  created_at timestamptz not null,
  constraint exchange_vault_audit_fingerprint_check check (
    subject_fingerprint ~ '^[0-9a-f]{32}$'
  ),
  constraint exchange_vault_audit_action_check check (
    action in (
      'version_stored', 'download_granted', 'downloaded',
      'version_deleted', 'document_deleted', 'retention_expired',
      'orphan_removed'
    )
  )
);

create index if not exists exchange_vault_documents_account_updated_idx
  on public.exchange_vault_documents (account_id, updated_at desc);
create index if not exists exchange_vault_versions_account_document_idx
  on public.exchange_vault_versions (account_id, document_id, version_number desc);
create index if not exists exchange_vault_versions_retention_idx
  on public.exchange_vault_versions (retention_expires_at);
create index if not exists exchange_vault_consents_account_document_idx
  on public.exchange_vault_consents (account_id, document_id);
create index if not exists exchange_vault_audit_created_idx
  on public.exchange_vault_audit_log (created_at desc);

alter table public.exchange_vault_documents enable row level security;
alter table public.exchange_vault_versions enable row level security;
alter table public.exchange_vault_consents enable row level security;
alter table public.exchange_vault_audit_log enable row level security;

-- Browser clients never read or mutate vault metadata directly. FastAPI uses
-- the server-only service role and applies account ownership checks first.
revoke all on table public.exchange_vault_documents from anon, authenticated;
revoke all on table public.exchange_vault_versions from anon, authenticated;
revoke all on table public.exchange_vault_consents from anon, authenticated;
revoke all on table public.exchange_vault_audit_log from anon, authenticated;

grant select, insert, update, delete
  on table public.exchange_vault_documents to service_role;
grant select, insert, update, delete
  on table public.exchange_vault_versions to service_role;
grant select, insert, update, delete
  on table public.exchange_vault_consents to service_role;
grant select, insert
  on table public.exchange_vault_audit_log to service_role;
