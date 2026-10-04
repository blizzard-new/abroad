create table if not exists public.exchange_email_verifications (
  id text primary key,
  email_fingerprint text not null,
  code_hash text not null,
  confirmation_token_hash text,
  attempt_count integer not null default 0,
  requested_at timestamptz not null,
  resend_available_at timestamptz not null,
  expires_at timestamptz not null,
  confirmed_at timestamptz,
  consumed_at timestamptz,
  constraint exchange_email_verifications_fingerprint_hash
    check (email_fingerprint ~ '^[0-9a-f]{64}$'),
  constraint exchange_email_verifications_code_hash
    check (code_hash ~ '^[0-9a-f]{64}$'),
  constraint exchange_email_verifications_token_hash
    check (
      confirmation_token_hash is null
      or confirmation_token_hash ~ '^[0-9a-f]{64}$'
    ),
  constraint exchange_email_verifications_attempt_count
    check (attempt_count between 0 and 10),
  constraint exchange_email_verifications_time_order
    check (
      requested_at <= resend_available_at
      and requested_at < expires_at
      and (confirmed_at is null or confirmed_at <= expires_at)
      and (consumed_at is null or consumed_at >= requested_at)
    )
);

create index if not exists exchange_email_verifications_fingerprint_requested_idx
  on public.exchange_email_verifications (email_fingerprint, requested_at desc);

create index if not exists exchange_email_verifications_expiry_idx
  on public.exchange_email_verifications (expires_at)
  where consumed_at is null;

alter table public.exchange_email_verifications enable row level security;

-- Verification codes and one-time token hashes are server-only. Web and Flutter
-- clients must use the FastAPI verification endpoints.
revoke all on table public.exchange_email_verifications from anon, authenticated;
grant select, insert, update, delete
  on table public.exchange_email_verifications
  to service_role;
