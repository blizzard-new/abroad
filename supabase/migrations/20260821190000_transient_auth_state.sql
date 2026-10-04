create table if not exists public.exchange_transient_auth_states (
  state_hash text primary key,
  kind text not null,
  provider_id text,
  account_id text references public.exchange_accounts(id) on delete cascade,
  session_id text,
  payload jsonb not null default '{}'::jsonb,
  expires_at timestamptz not null,
  created_at timestamptz not null default now(),
  constraint exchange_transient_auth_state_hash_format
    check (state_hash ~ '^[0-9a-f]{64}$'),
  constraint exchange_transient_auth_state_kind
    check (kind in ('oauth_login', 'student_verification_oauth', 'student_verification_session')),
  constraint exchange_transient_auth_state_payload_object
    check (jsonb_typeof(payload) = 'object')
);

create index if not exists exchange_transient_auth_states_expiry_idx
  on public.exchange_transient_auth_states (expires_at);

create index if not exists exchange_transient_auth_states_session_idx
  on public.exchange_transient_auth_states (kind, provider_id, session_id)
  where session_id is not null;

create index if not exists exchange_transient_auth_states_account_idx
  on public.exchange_transient_auth_states (account_id, expires_at)
  where account_id is not null;

create table if not exists public.exchange_transient_auth_rate_events (
  id bigint generated always as identity primary key,
  kind text not null,
  client_fingerprint text not null,
  occurred_at timestamptz not null default now(),
  constraint exchange_transient_auth_rate_kind
    check (kind in ('oauth_login', 'student_verification_oauth')),
  constraint exchange_transient_auth_rate_fingerprint
    check (client_fingerprint ~ '^[0-9a-f]{64}$')
);

create index if not exists exchange_transient_auth_rate_window_idx
  on public.exchange_transient_auth_rate_events (kind, client_fingerprint, occurred_at desc);

alter table public.exchange_transient_auth_states enable row level security;
alter table public.exchange_transient_auth_rate_events enable row level security;

revoke all on table public.exchange_transient_auth_states from anon, authenticated;
revoke all on table public.exchange_transient_auth_rate_events from anon, authenticated;
revoke all on sequence public.exchange_transient_auth_rate_events_id_seq from anon, authenticated;

grant select, insert, update, delete on table public.exchange_transient_auth_states to service_role;
grant select, insert, update, delete on table public.exchange_transient_auth_rate_events to service_role;
grant usage, select on sequence public.exchange_transient_auth_rate_events_id_seq to service_role;

create or replace function public.exchange_save_transient_auth_state(
  p_state_hash text,
  p_kind text,
  p_provider_id text,
  p_account_id text,
  p_session_id text,
  p_payload jsonb,
  p_expires_at timestamptz
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_saved public.exchange_transient_auth_states;
begin
  perform pg_advisory_xact_lock(hashtext('exchange_transient_auth_state'));
  delete from public.exchange_transient_auth_states where expires_at <= now();

  insert into public.exchange_transient_auth_states (
    state_hash,
    kind,
    provider_id,
    account_id,
    session_id,
    payload,
    expires_at
  ) values (
    p_state_hash,
    p_kind,
    p_provider_id,
    p_account_id,
    p_session_id,
    coalesce(p_payload, '{}'::jsonb),
    p_expires_at
  )
  returning * into v_saved;

  return to_jsonb(v_saved);
end;
$$;

create or replace function public.exchange_start_transient_auth_state(
  p_state_hash text,
  p_kind text,
  p_provider_id text,
  p_account_id text,
  p_session_id text,
  p_payload jsonb,
  p_expires_at timestamptz,
  p_client_fingerprint text,
  p_window_start timestamptz,
  p_start_limit integer,
  p_max_active integer,
  p_replace_session boolean
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_rate_count integer;
  v_active_count integer;
begin
  if p_kind not in ('oauth_login', 'student_verification_oauth') then
    raise exception 'unsupported transient auth oauth kind';
  end if;
  if p_start_limit < 1 or p_max_active < 1 then
    raise exception 'transient auth limits must be positive';
  end if;
  if p_replace_session and (p_provider_id is null or p_session_id is null) then
    raise exception 'replacement scope requires provider and session';
  end if;

  perform pg_advisory_xact_lock(hashtext('exchange_transient_auth_state'));
  delete from public.exchange_transient_auth_states where expires_at <= now();
  delete from public.exchange_transient_auth_rate_events where occurred_at <= p_window_start;

  select count(*) into v_rate_count
  from public.exchange_transient_auth_rate_events
  where kind = p_kind
    and client_fingerprint = p_client_fingerprint
    and occurred_at > p_window_start;

  if v_rate_count >= p_start_limit then
    return jsonb_build_object('status', 'rate_limited');
  end if;

  select count(*) into v_active_count
  from public.exchange_transient_auth_states state
  where state.kind = p_kind
    and state.expires_at > now()
    and not (
      p_replace_session
      and state.provider_id = p_provider_id
      and state.session_id = p_session_id
    );

  if v_active_count >= p_max_active then
    return jsonb_build_object('status', 'capacity_reached');
  end if;

  if p_replace_session then
    delete from public.exchange_transient_auth_states
    where kind = p_kind
      and provider_id = p_provider_id
      and session_id = p_session_id;
  end if;

  insert into public.exchange_transient_auth_rate_events (
    kind,
    client_fingerprint,
    occurred_at
  ) values (
    p_kind,
    p_client_fingerprint,
    now()
  );

  insert into public.exchange_transient_auth_states (
    state_hash,
    kind,
    provider_id,
    account_id,
    session_id,
    payload,
    expires_at
  ) values (
    p_state_hash,
    p_kind,
    p_provider_id,
    p_account_id,
    p_session_id,
    coalesce(p_payload, '{}'::jsonb),
    p_expires_at
  );

  return jsonb_build_object('status', 'created');
end;
$$;

create or replace function public.exchange_consume_transient_auth_state(
  p_state_hash text,
  p_kind text,
  p_expected_account_id text,
  p_expected_session_id text,
  p_expected_provider_id text
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_consumed public.exchange_transient_auth_states;
begin
  perform pg_advisory_xact_lock(hashtext('exchange_transient_auth_state'));
  delete from public.exchange_transient_auth_states where expires_at <= now();

  delete from public.exchange_transient_auth_states
  where state_hash = p_state_hash
    and kind = p_kind
    and (p_expected_account_id is null or account_id = p_expected_account_id)
    and (p_expected_session_id is null or session_id = p_expected_session_id)
    and (p_expected_provider_id is null or provider_id = p_expected_provider_id)
  returning * into v_consumed;

  if v_consumed.state_hash is null then
    return null;
  end if;
  return to_jsonb(v_consumed);
end;
$$;

revoke all on function public.exchange_save_transient_auth_state(
  text, text, text, text, text, jsonb, timestamptz
) from public, anon, authenticated;
revoke all on function public.exchange_start_transient_auth_state(
  text, text, text, text, text, jsonb, timestamptz, text, timestamptz, integer, integer, boolean
) from public, anon, authenticated;
revoke all on function public.exchange_consume_transient_auth_state(
  text, text, text, text, text
) from public, anon, authenticated;

grant execute on function public.exchange_save_transient_auth_state(
  text, text, text, text, text, jsonb, timestamptz
) to service_role;
grant execute on function public.exchange_start_transient_auth_state(
  text, text, text, text, text, jsonb, timestamptz, text, timestamptz, integer, integer, boolean
) to service_role;
grant execute on function public.exchange_consume_transient_auth_state(
  text, text, text, text, text
) to service_role;
