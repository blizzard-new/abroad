alter table public.exchange_notifications
  add column if not exists deleted_at timestamptz;

alter table public.exchange_notifications
  drop constraint if exists exchange_notifications_kind_check;

alter table public.exchange_notifications
  add constraint exchange_notifications_kind_check
    check (kind in ('deadline', 'content_update', 'catalogue_update'));

create index if not exists exchange_notifications_active_account_created_idx
  on public.exchange_notifications (account_id, created_at desc)
  where deleted_at is null;
