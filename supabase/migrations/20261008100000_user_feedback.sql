-- User feedback ("用戶評價"): suggestions, problem reports and kind words typed into the site.
-- FastAPI is the only writer and reader (service role); the browser roles get nothing.
--
-- Nothing that identifies the sender is stored: no IP address, no account id, no e-mail address.
-- `contact` is only what the person chose to type; `route` and `home_school` are the page and school they were looking at.
-- The administrator reads the rows on /admin/feedback, or directly in the Supabase Table Editor.
-- Safe to run twice: the project's Supabase may already have it from a direct apply.

create table if not exists public.exchange_user_feedback (
  id text primary key check (char_length(id) between 8 and 64),
  created_at timestamptz not null default now(),
  kind text not null default 'suggestion' check (kind in ('suggestion', 'bug', 'praise', 'other')),
  rating smallint check (rating between 1 and 5),
  message text not null check (char_length(message) between 5 and 2000),
  contact text not null default '' check (char_length(contact) <= 120),
  route text not null default '' check (char_length(route) <= 120),
  home_school text not null default '' check (char_length(home_school) <= 60),
  signed_in boolean not null default false,
  status text not null default 'new' check (status in ('new', 'read', 'done')),
  admin_note text not null default '' check (char_length(admin_note) <= 1000),
  handled_at timestamptz
);

create index if not exists exchange_user_feedback_time_idx on public.exchange_user_feedback (created_at desc);
create index if not exists exchange_user_feedback_status_idx on public.exchange_user_feedback (status, created_at desc);

alter table public.exchange_user_feedback enable row level security;
alter table public.exchange_user_feedback force row level security;
revoke all on public.exchange_user_feedback from public, anon, authenticated;
grant select, insert, update, delete on public.exchange_user_feedback to service_role;
