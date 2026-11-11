-- Follow-up database security hardening:
-- 1. Pin search_path on match_document_chunks (pg_catalog before extensions, plus pg_temp)
--    and mobile push RPCs (empty search_path + deadlock-free dual advisory locks).
-- 2. Verify job_id ownership on effect_key replay in exchange_maint_complete_job.
-- 3. Enforce append-only semantics on audit log tables for service_role.
-- 4. Enforce ENABLE + FORCE ROW LEVEL SECURITY and revoke PUBLIC/anon/authenticated
--    table/sequence grants + default privileges across public schema.
-- 5. Ensure exchange-private-vault bucket remains non-public when storage.buckets exists.

alter function public.match_document_chunks(extensions.vector, double precision, integer, text)
  set search_path = pg_catalog, extensions, pg_temp;

create or replace function public.exchange_register_mobile_device(
  p_account_id text,
  p_installation_id text,
  p_fid text
) returns void
language plpgsql
set search_path = ''
as $$
declare
  v_lock_inst bigint := pg_catalog.hashtextextended('inst:' || coalesce(p_installation_id, ''), 0);
  v_lock_fid bigint := pg_catalog.hashtextextended('fid:' || coalesce(p_fid, ''), 0);
begin
  -- Acquire both installation_id and fid locks in canonical bigint order to prevent deadlocks
  -- and eliminate UNIQUE(fid) race conditions across concurrent API workers.
  perform pg_catalog.pg_advisory_xact_lock(least(v_lock_inst, v_lock_fid));
  if v_lock_inst <> v_lock_fid then
    perform pg_catalog.pg_advisory_xact_lock(greatest(v_lock_inst, v_lock_fid));
  end if;

  delete from public.exchange_mobile_devices
   where fid = p_fid
     and installation_id <> p_installation_id;

  delete from public.exchange_mobile_devices
   where installation_id = p_installation_id
     and account_id <> p_account_id;

  insert into public.exchange_mobile_devices (installation_id, account_id, fid)
  values (p_installation_id, p_account_id, p_fid)
  on conflict (installation_id) do update
     set fid = excluded.fid;
end;
$$;

create or replace function public.exchange_claim_mobile_push(
  p_notification_id text,
  p_installation_id text
) returns boolean
language plpgsql
set search_path = ''
as $$
declare
  v_claimed text;
begin
  insert into public.exchange_mobile_push_deliveries (
    notification_id,
    installation_id,
    state,
    retry_at
  )
  values (
    p_notification_id,
    p_installation_id,
    'sending',
    pg_catalog.now() + interval '2 minutes'
  )
  on conflict (notification_id, installation_id) do update
     set state = 'sending',
         retry_at = excluded.retry_at,
         attempts = public.exchange_mobile_push_deliveries.attempts + 1
   where public.exchange_mobile_push_deliveries.state not in ('sent', 'failed')
     and public.exchange_mobile_push_deliveries.retry_at <= pg_catalog.now()
     and public.exchange_mobile_push_deliveries.attempts < 5
  returning notification_id into v_claimed;

  return v_claimed is not null;
end;
$$;

revoke all on function
  public.exchange_register_mobile_device(text, text, text),
  public.exchange_claim_mobile_push(text, text)
from public, anon, authenticated;

grant execute on function
  public.exchange_register_mobile_device(text, text, text),
  public.exchange_claim_mobile_push(text, text)
to service_role;

create or replace function public.exchange_maint_complete_job(
  p_job_id text,
  p_worker_id text,
  p_lease_token bigint,
  p_effect_key text,
  p_result_id text,
  p_result_payload jsonb default '{}'::jsonb
) returns jsonb
language plpgsql
set search_path = ''
as $$
declare
  v_existing public.exchange_maint_job_effects%rowtype;
  v_job public.exchange_maint_jobs%rowtype;
begin
  select *
    into v_existing
    from public.exchange_maint_job_effects
   where effect_key = p_effect_key;

  if found then
    if v_existing.job_id <> p_job_id then
      raise exception using errcode = 'P0001', message = 'Effect key belongs to a different job';
    end if;
    return jsonb_build_object(
      'idempotent_replay', true,
      'effect_key', v_existing.effect_key,
      'result_id', v_existing.result_id,
      'result_payload', v_existing.result_payload
    );
  end if;

  select *
    into v_job
    from public.exchange_maint_jobs
   where id = p_job_id
   for update;

  if not found
     or v_job.status <> 'leased'
     or v_job.worker_id <> p_worker_id
     or v_job.lease_token <> p_lease_token
     or v_job.lease_until is null
     or v_job.lease_until <= pg_catalog.now() then
    raise exception using errcode = '40001', message = 'Stale lease token or expired lease rejected';
  end if;

  insert into public.exchange_maint_job_effects (
    effect_key, job_id, lease_token, result_id, result_payload, committed_at
  ) values (
    p_effect_key, p_job_id, p_lease_token, p_result_id, coalesce(p_result_payload, '{}'::jsonb), pg_catalog.now()
  );

  update public.exchange_maint_jobs
     set status = 'succeeded',
         lease_until = null,
         updated_at = pg_catalog.now()
   where id = p_job_id;

  return jsonb_build_object(
    'idempotent_replay', false,
    'effect_key', p_effect_key,
    'result_id', p_result_id,
    'result_payload', coalesce(p_result_payload, '{}'::jsonb)
  );
end;
$$;

revoke all on function public.exchange_maint_complete_job(text, text, bigint, text, text, jsonb)
  from public, anon, authenticated;
grant execute on function public.exchange_maint_complete_job(text, text, bigint, text, text, jsonb)
  to service_role;

-- Append-only protection on audit tables
revoke update, delete on table public.application_workflow_audit_log from service_role;
revoke update, delete on table public.exchange_maint_audit_events from service_role;

create or replace function public.exchange_prevent_maint_audit_mutation()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  raise exception using errcode = '42501', message = 'exchange_maint_audit_events is append-only';
end;
$$;

revoke all on function public.exchange_prevent_maint_audit_mutation()
  from public, anon, authenticated;

drop trigger if exists exchange_maint_audit_events_append_only on public.exchange_maint_audit_events;
create trigger exchange_maint_audit_events_append_only
  before update or delete on public.exchange_maint_audit_events
  for each row
  execute function public.exchange_prevent_maint_audit_mutation();

-- Sweep all application tables in public to enforce ENABLE + FORCE ROW LEVEL SECURITY
-- and revoke PUBLIC/anon/authenticated grants uniformly.
do $$
declare
  v_row record;
begin
  for v_row in
    select tablename
      from pg_catalog.pg_tables
     where schemaname = 'public'
       and tablename <> 'uniway_schema_migrations'
     order by tablename
  loop
    execute pg_catalog.format('alter table public.%I enable row level security', v_row.tablename);
    execute pg_catalog.format('alter table public.%I force row level security', v_row.tablename);
    execute pg_catalog.format('revoke all on table public.%I from public, anon, authenticated', v_row.tablename);
  end loop;
end;
$$;

revoke all on all sequences in schema public from public, anon, authenticated;

alter default privileges in schema public
  revoke all on tables from public, anon, authenticated;
alter default privileges in schema public
  revoke all on sequences from public, anon, authenticated;
alter default privileges in schema public
  revoke all on functions from public, anon, authenticated;

do $$
begin
  if pg_catalog.to_regclass('storage.buckets') is not null then
    update storage.buckets
       set public = false
     where id = 'exchange-private-vault'
       and public is distinct from false;
  end if;
end;
$$;
