create table if not exists public.exchange_notifications (
  id text primary key,
  account_id text not null
    references public.exchange_accounts(id) on delete cascade,
  dedupe_key text not null,
  kind text not null,
  channels text[] not null default '{}',
  title text not null,
  body text not null,
  action_url text,
  source_key text not null,
  source_url text,
  deadline_at timestamptz,
  reminder_days integer,
  scheduled_for timestamptz not null,
  read_at timestamptz,
  created_at timestamptz not null default now(),
  unique (account_id, dedupe_key),
  constraint exchange_notifications_kind_check
    check (kind in ('deadline', 'content_update')),
  constraint exchange_notifications_channels_check
    check (channels <@ array['web', 'email']::text[]),
  constraint exchange_notifications_reminder_days_check
    check (reminder_days is null or reminder_days between 0 and 90)
);

create index if not exists exchange_notifications_account_created_idx
  on public.exchange_notifications (account_id, created_at desc);

create index if not exists exchange_notifications_unread_idx
  on public.exchange_notifications (account_id, created_at desc)
  where read_at is null;

create table if not exists public.exchange_notification_deliveries (
  id text primary key,
  notification_id text not null
    references public.exchange_notifications(id) on delete cascade,
  account_id text not null
    references public.exchange_accounts(id) on delete cascade,
  channel text not null,
  status text not null default 'pending',
  attempt_count integer not null default 0,
  next_attempt_at timestamptz not null,
  sent_at timestamptz,
  last_error_code text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (notification_id, channel),
  constraint exchange_notification_deliveries_channel_check
    check (channel = 'email'),
  constraint exchange_notification_deliveries_status_check
    check (status in ('pending', 'retrying', 'sent', 'failed', 'cancelled')),
  constraint exchange_notification_deliveries_attempt_count_check
    check (attempt_count between 0 and 20)
);

create index if not exists exchange_notification_deliveries_due_idx
  on public.exchange_notification_deliveries (next_attempt_at)
  where status in ('pending', 'retrying');

alter table public.exchange_notifications enable row level security;
alter table public.exchange_notification_deliveries enable row level security;

revoke all on table public.exchange_notifications from anon, authenticated;
revoke all on table public.exchange_notification_deliveries from anon, authenticated;

grant select, insert, update, delete on table public.exchange_notifications to service_role;
grant select, insert, update, delete on table public.exchange_notification_deliveries to service_role;
