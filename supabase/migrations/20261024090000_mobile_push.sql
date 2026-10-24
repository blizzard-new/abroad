create table public.exchange_mobile_devices (
  installation_id text primary key check (installation_id ~ '^[a-f0-9]{64}$'),
  account_id text not null references public.exchange_accounts(id) on delete cascade,
  fid text not null unique,
  registered_at timestamptz not null default now()
);
create index exchange_mobile_devices_account on public.exchange_mobile_devices(account_id);
create table public.exchange_mobile_push_deliveries (
  notification_id text references public.exchange_notifications(id) on delete cascade,
  installation_id text references public.exchange_mobile_devices(installation_id) on delete cascade,
  state text not null check (state in ('sending','retrying','sent','failed')),
  retry_at timestamptz not null,
  attempts integer not null default 1,
  primary key(notification_id, installation_id)
);
alter table public.exchange_mobile_devices enable row level security;
alter table public.exchange_mobile_push_deliveries enable row level security;
revoke all on public.exchange_mobile_devices, public.exchange_mobile_push_deliveries from anon, authenticated;
grant select, insert, update, delete on public.exchange_mobile_devices, public.exchange_mobile_push_deliveries to service_role;

create function public.exchange_register_mobile_device(p_account_id text, p_installation_id text, p_fid text)
returns void language plpgsql set search_path = public as $$
begin
  -- Serializes registration/rotation for this device across API workers.
  perform pg_advisory_xact_lock(hashtextextended(p_installation_id, 0));
  delete from exchange_mobile_devices where fid=p_fid and installation_id<>p_installation_id;
  delete from exchange_mobile_devices where installation_id=p_installation_id and account_id<>p_account_id;
  insert into exchange_mobile_devices(installation_id,account_id,fid)
  values(p_installation_id,p_account_id,p_fid)
  on conflict(installation_id) do update set fid=excluded.fid;
end $$;

create function public.exchange_claim_mobile_push(p_notification_id text, p_installation_id text)
returns boolean language plpgsql set search_path = public as $$
declare claimed text;
begin
  insert into exchange_mobile_push_deliveries(notification_id,installation_id,state,retry_at)
  values(p_notification_id,p_installation_id,'sending',now()+interval '2 minutes')
  on conflict(notification_id,installation_id) do update
  set state='sending', retry_at=excluded.retry_at, attempts=exchange_mobile_push_deliveries.attempts+1
  where exchange_mobile_push_deliveries.state not in ('sent','failed')
    and exchange_mobile_push_deliveries.retry_at<=now()
    and exchange_mobile_push_deliveries.attempts<5
  returning notification_id into claimed;
  return claimed is not null;
end $$;
revoke all on function public.exchange_register_mobile_device(text,text,text), public.exchange_claim_mobile_push(text,text) from public, anon, authenticated;
grant execute on function public.exchange_register_mobile_device(text,text,text), public.exchange_claim_mobile_push(text,text) to service_role;
