create table if not exists public.exchange_accounts (
  id text primary key,
  email text,
  profile jsonb not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint exchange_accounts_profile_object
    check (jsonb_typeof(profile) = 'object')
);

create unique index if not exists exchange_accounts_email_lower_unique
  on public.exchange_accounts (lower(email))
  where email is not null;

create table if not exists public.exchange_account_workspaces (
  account_id text not null
    references public.exchange_accounts(id) on delete cascade,
  home_school_key text not null,
  workspace jsonb not null,
  updated_at timestamptz not null default now(),
  primary key (account_id, home_school_key),
  constraint exchange_account_workspaces_payload_object
    check (jsonb_typeof(workspace) = 'object')
);

create index if not exists exchange_account_workspaces_updated_idx
  on public.exchange_account_workspaces (account_id, updated_at desc);

create table if not exists public.exchange_account_sessions (
  id text primary key,
  account_id text not null
    references public.exchange_accounts(id) on delete cascade,
  token_hash text not null unique,
  expires_at timestamptz not null,
  created_at timestamptz not null default now()
);

create index if not exists exchange_account_sessions_account_idx
  on public.exchange_account_sessions (account_id, expires_at desc);

create index if not exists exchange_account_sessions_expiry_idx
  on public.exchange_account_sessions (expires_at);

alter table public.exchange_accounts enable row level security;
alter table public.exchange_account_workspaces enable row level security;
alter table public.exchange_account_sessions enable row level security;

-- These rows are server-only. Web and Flutter clients must use the FastAPI API.
revoke all on table public.exchange_accounts from anon, authenticated;
revoke all on table public.exchange_account_workspaces from anon, authenticated;
revoke all on table public.exchange_account_sessions from anon, authenticated;

grant select, insert, update, delete on table public.exchange_accounts to service_role;
grant select, insert, update, delete on table public.exchange_account_workspaces to service_role;
grant select, insert, update, delete on table public.exchange_account_sessions to service_role;
