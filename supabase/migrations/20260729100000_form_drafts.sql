-- Server-only encrypted application form drafts.
-- Plain form values are encrypted by FastAPI before they reach Postgres.

create table if not exists public.exchange_application_form_drafts (
  account_id text not null
    references public.exchange_accounts(id) on delete cascade,
  home_school_key text not null,
  home_school text not null,
  template_id text not null,
  template_version text not null,
  revision integer not null default 1,
  ciphertext text not null,
  nonce text not null,
  plaintext_sha256 text not null,
  updated_at timestamptz not null default now(),
  primary key (account_id, home_school_key, template_id),
  constraint exchange_application_form_drafts_revision_check
    check (revision >= 1),
  constraint exchange_application_form_drafts_hash_check
    check (plaintext_sha256 ~ '^[0-9a-f]{64}$'),
  constraint exchange_application_form_drafts_ciphertext_check
    check (length(ciphertext) > 0 and length(nonce) > 0)
);

create index if not exists exchange_application_form_drafts_account_updated_idx
  on public.exchange_application_form_drafts (account_id, updated_at desc);

alter table public.exchange_application_form_drafts enable row level security;

-- Browser and Flutter clients never access draft ciphertext directly. They use
-- authenticated FastAPI routes so field allowlists and revision checks cannot
-- be bypassed.
revoke all on table public.exchange_application_form_drafts from anon, authenticated;
grant select, insert, update, delete
  on table public.exchange_application_form_drafts to service_role;
