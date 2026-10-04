-- Production auth mutations must not depend on a process-local lock.  Provider
-- identity, account identity fields, and the resulting session are committed by
-- the database in one short transaction after all external OAuth HTTP has ended.

create table public.exchange_account_provider_links (
  account_id text not null
    references public.exchange_accounts(id) on delete cascade,
  provider text not null,
  subject text not null,
  created_at timestamptz not null default now(),
  primary key (provider, subject),
  unique (account_id, provider),
  constraint exchange_account_provider_links_provider_allowed
    check (provider in ('email', 'google', 'facebook', 'apple')),
  constraint exchange_account_provider_links_subject_nonempty
    check (btrim(subject) <> '' and char_length(subject) <= 512)
);

-- The UNIQUE (account_id, provider) index also covers the foreign-key prefix and
-- keeps account deletion/cascade and account-centric hydration index-backed.

do $$
begin
  if exists (
    select 1
    from public.exchange_accounts account
    where account.profile ? 'provider_links'
      and jsonb_typeof(account.profile -> 'provider_links') <> 'array'
  ) then
    raise exception
      'exchange_accounts.profile.provider_links must be an array before auth migration';
  end if;

  if exists (
    select 1
    from public.exchange_accounts account
    cross join lateral jsonb_array_elements(
      case
        when jsonb_typeof(account.profile -> 'provider_links') = 'array'
          then account.profile -> 'provider_links'
        else '[]'::jsonb
      end
    ) as link(value)
    where jsonb_typeof(link.value) <> 'object'
      or coalesce(link.value ->> 'provider', '') not in (
        'email', 'google', 'facebook', 'apple'
      )
      or btrim(coalesce(link.value ->> 'subject', '')) = ''
      or char_length(coalesce(link.value ->> 'subject', '')) > 512
  ) then
    raise exception
      'exchange_accounts.profile.provider_links contains an invalid provider identity';
  end if;
end;
$$;

-- The constraints intentionally make this a fail-closed backfill.  Duplicate
-- provider subjects or two identities for the same account/provider abort the
-- migration instead of silently choosing an owner.
insert into public.exchange_account_provider_links (
  account_id,
  provider,
  subject,
  created_at
)
select
  account.id,
  link.value ->> 'provider',
  link.value ->> 'subject',
  account.created_at + ((link.position - 1) * interval '1 microsecond')
from public.exchange_accounts account
cross join lateral jsonb_array_elements(
  case
    when jsonb_typeof(account.profile -> 'provider_links') = 'array'
      then account.profile -> 'provider_links'
    else '[]'::jsonb
  end
) with ordinality as link(value, position);

-- Capture provider links for newly inserted accounts such as email registration.
-- Existing-account link changes remain possible only through the dedicated auth
-- RPC, so a stale whole-profile update cannot manufacture a provider identity.
create or replace function public.exchange_capture_initial_provider_links()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_link record;
begin
  if new.profile ? 'provider_links'
     and jsonb_typeof(new.profile -> 'provider_links') <> 'array' then
    raise exception 'account provider_links must be an array';
  end if;

  for v_link in
    select
      item.value as raw_value,
      item.value ->> 'provider' as provider,
      item.value ->> 'subject' as subject,
      item.position
    from jsonb_array_elements(
      case
        when jsonb_typeof(new.profile -> 'provider_links') = 'array'
          then new.profile -> 'provider_links'
        else '[]'::jsonb
      end
    ) with ordinality as item(value, position)
  loop
    if jsonb_typeof(v_link.raw_value) <> 'object'
       or coalesce(v_link.provider, '') not in (
         'email', 'google', 'facebook', 'apple'
       )
       or btrim(coalesce(v_link.subject, '')) = ''
       or char_length(coalesce(v_link.subject, '')) > 512 then
      raise exception 'account contains an invalid provider identity';
    end if;

    insert into public.exchange_account_provider_links (
      account_id,
      provider,
      subject,
      created_at
    ) values (
      new.id,
      v_link.provider,
      v_link.subject,
      new.created_at + ((v_link.position - 1) * interval '1 microsecond')
    );
  end loop;

  return new;
end;
$$;

drop trigger if exists exchange_capture_initial_provider_links_trigger
  on public.exchange_accounts;
create trigger exchange_capture_initial_provider_links_trigger
after insert on public.exchange_accounts
for each row execute function public.exchange_capture_initial_provider_links();

-- Ordinary profile upserts are allowed to change product/profile fields, but
-- auth-owned state is monotonic and provider links are rebuilt from their
-- normalized authority.  This prevents a stale full JSON profile from removing
-- a newly committed OAuth link or reverting a completed student verification.
create or replace function public.exchange_protect_auth_owned_account_fields()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_provider_links jsonb;
  v_old_email_verified boolean;
  v_new_email_verified boolean;
  v_old_school_email_verified boolean;
  v_new_school_email_verified boolean;
  v_old_student_verified boolean;
  v_new_student_verified boolean;
begin
  new.id := old.id;
  new.created_at := old.created_at;

  if old.email is not null then
    new.email := old.email;
  elsif new.email is not null then
    new.email := nullif(lower(btrim(new.email)), '');
  end if;

  new.updated_at := greatest(old.updated_at, coalesce(new.updated_at, old.updated_at));

  v_old_email_verified := coalesce(
    (old.profile ->> 'email_verified')::boolean,
    false
  );
  v_new_email_verified := coalesce(
    (new.profile ->> 'email_verified')::boolean,
    false
  );
  v_old_school_email_verified := coalesce(
    (old.profile ->> 'school_email_verified')::boolean,
    false
  );
  v_new_school_email_verified := coalesce(
    (new.profile ->> 'school_email_verified')::boolean,
    false
  );
  v_old_student_verified := coalesce(
    (old.profile ->> 'student_status_verified')::boolean,
    false
  );
  v_new_student_verified := coalesce(
    (new.profile ->> 'student_status_verified')::boolean,
    false
  );

  select coalesce(
    jsonb_agg(
      jsonb_build_object(
        'provider', link.provider,
        'subject', link.subject
      )
      order by
        case link.provider
          when 'email' then 0
          when 'google' then 1
          when 'facebook' then 2
          when 'apple' then 3
          else 4
        end,
        link.created_at,
        link.subject
    ),
    '[]'::jsonb
  ) into v_provider_links
  from public.exchange_account_provider_links link
  where link.account_id = old.id;

  new.profile := coalesce(new.profile, '{}'::jsonb) || jsonb_build_object(
    'id', old.id,
    'email', new.email,
    'email_verified', v_old_email_verified or v_new_email_verified,
    'school_email_verified',
      v_old_school_email_verified or v_new_school_email_verified,
    'student_status_verified', v_old_student_verified or v_new_student_verified,
    'provider_links', v_provider_links,
    'created_at', old.created_at,
    'updated_at', new.updated_at
  );

  if v_old_student_verified then
    new.profile := new.profile || jsonb_build_object(
      'home_university', old.profile -> 'home_university',
      'student_status_verified', true,
      'verified_university', old.profile -> 'verified_university',
      'verified_department', old.profile -> 'verified_department',
      'student_verification_method', old.profile -> 'student_verification_method',
      'student_verified_at', old.profile -> 'student_verified_at'
    );
  end if;

  return new;
end;
$$;

drop trigger if exists exchange_protect_auth_owned_account_fields_trigger
  on public.exchange_accounts;
create trigger exchange_protect_auth_owned_account_fields_trigger
before update on public.exchange_accounts
for each row execute function public.exchange_protect_auth_owned_account_fields();

create or replace function public.exchange_commit_oauth_login(
  p_provider text,
  p_subject text,
  p_trusted_email text,
  p_display_name text,
  p_avatar_url text,
  p_home_university text,
  p_new_account_id text,
  p_session_id text,
  p_session_token_hash text,
  p_session_expires_at timestamptz,
  p_occurred_at timestamptz
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_trusted_email text;
  v_provider_account public.exchange_accounts%rowtype;
  v_email_account public.exchange_accounts%rowtype;
  v_account public.exchange_accounts%rowtype;
  v_session public.exchange_account_sessions%rowtype;
  v_provider_found boolean := false;
  v_email_found boolean := false;
  v_email_verified boolean := false;
  v_next_email text;
  v_next_avatar text;
  v_existing_same_provider boolean := false;
  v_commit_at timestamptz;
begin
  v_trusted_email := nullif(lower(btrim(p_trusted_email)), '');

  if p_provider is null
     or p_provider not in ('google', 'facebook')
     or p_subject is null
     or btrim(p_subject) = ''
     or char_length(p_subject) > 512
     or p_new_account_id is null
     or btrim(p_new_account_id) = ''
     or char_length(p_new_account_id) > 128
     or p_session_id is null
     or btrim(p_session_id) = ''
     or char_length(p_session_id) > 128
     or p_session_token_hash is null
     or char_length(p_session_token_hash) < 32
     or char_length(p_session_token_hash) > 128
     or p_session_expires_at is null
     or btrim(coalesce(p_home_university, '')) = ''
     or (v_trusted_email is not null and char_length(v_trusted_email) > 254)
     or (p_provider = 'facebook' and v_trusted_email is not null) then
    return jsonb_build_object('status', 'integrity_conflict');
  end if;

  -- One global transaction lock makes an absent provider/email row lockable as a
  -- business identity and gives every worker the same conflict decision.  All
  -- provider HTTP calls have already completed before this short function starts.
  perform pg_advisory_xact_lock(
    hashtext('exchange_atomic_auth_account_mutations')
  );

  select session.* into v_session
  from public.exchange_account_sessions session
  where session.id = p_session_id
     or session.token_hash = p_session_token_hash
  order by session.id
  limit 1
  for update;

  if found then
    return jsonb_build_object('status', 'integrity_conflict');
  end if;

  select account.* into v_provider_account
  from public.exchange_account_provider_links link
  join public.exchange_accounts account on account.id = link.account_id
  where link.provider = p_provider
    and link.subject = p_subject
  for update of account;
  v_provider_found := found;

  if v_trusted_email is not null then
    select account.* into v_email_account
    from public.exchange_accounts account
    where lower(account.email) = v_trusted_email
    limit 1
    for update;
    v_email_found := found;
  end if;

  if v_email_found
     and not coalesce(
       (v_email_account.profile ->> 'email_verified')::boolean,
       false
     )
     and (
       not v_provider_found
       or v_provider_account.id <> v_email_account.id
     ) then
    return jsonb_build_object('status', 'unverified_email_conflict');
  end if;

  if v_provider_found
     and v_email_found
     and v_provider_account.id <> v_email_account.id then
    return jsonb_build_object('status', 'verified_email_conflict');
  end if;

  if v_provider_found
     and v_trusted_email is not null
     and v_provider_account.email is not null
     and lower(v_provider_account.email) <> v_trusted_email then
    return jsonb_build_object('status', 'verified_email_conflict');
  end if;

  if not v_provider_found and v_email_found then
    select exists (
      select 1
      from public.exchange_account_provider_links link
      where link.account_id = v_email_account.id
        and link.provider = p_provider
    ) into v_existing_same_provider;

    if v_existing_same_provider then
      return jsonb_build_object('status', 'same_provider_conflict');
    end if;
  end if;

  -- Capture the linearization time only after every existing account row needed
  -- by this decision is locked. Direct profile/delete operations do not take the
  -- advisory lock and may have made this RPC wait on a row lock.
  v_commit_at := clock_timestamp();
  if p_session_expires_at <= v_commit_at then
    return jsonb_build_object('status', 'integrity_conflict');
  end if;

  begin
    if v_provider_found then
      v_account := v_provider_account;
    elsif v_email_found then
      v_account := v_email_account;
    else
      if exists (
        select 1
        from public.exchange_accounts account
        where account.id = p_new_account_id
      ) then
        return jsonb_build_object('status', 'integrity_conflict');
      end if;

      insert into public.exchange_accounts (
        id,
        email,
        profile,
        created_at,
        updated_at
      ) values (
        p_new_account_id,
        v_trusted_email,
        jsonb_build_object(
          'id', p_new_account_id,
          'email', v_trusted_email,
          'display_name', left(
            coalesce(nullif(btrim(p_display_name), ''), '留學同學'),
            30
          ),
          'avatar_url', p_avatar_url,
          'home_university', p_home_university,
          'email_verified', v_trusted_email is not null,
          'provider_links', jsonb_build_array(
            jsonb_build_object(
              'provider', p_provider,
              'subject', p_subject
            )
          ),
          'created_at', v_commit_at,
          'updated_at', v_commit_at
        ),
        v_commit_at,
        v_commit_at
      )
      returning * into v_account;
    end if;

    if v_provider_found or not v_email_found then
      -- Existing provider links need no insert.  A newly created account was
      -- captured by the AFTER INSERT trigger above.
      null;
    else
      insert into public.exchange_account_provider_links (
        account_id,
        provider,
        subject,
        created_at
      ) values (
        v_account.id,
        p_provider,
        p_subject,
        v_commit_at
      );
    end if;

    if v_provider_found or v_email_found then
      v_next_email := coalesce(v_account.email, v_trusted_email);
      v_email_verified := coalesce(
        (v_account.profile ->> 'email_verified')::boolean,
        false
      ) or v_trusted_email is not null;
      v_next_avatar := coalesce(
        nullif(v_account.profile ->> 'avatar_url', ''),
        p_avatar_url
      );

      update public.exchange_accounts account
      set email = v_next_email,
          profile = account.profile || jsonb_build_object(
            'email', v_next_email,
            'email_verified', v_email_verified,
            'avatar_url', v_next_avatar,
            'updated_at', v_commit_at
          ),
          updated_at = v_commit_at
      where account.id = v_account.id
      returning * into v_account;
    end if;

    if p_session_expires_at <= clock_timestamp() then
      raise exception 'oauth session expired while committing'
        using errcode = '23514';
    end if;

    insert into public.exchange_account_sessions (
      id,
      account_id,
      token_hash,
      expires_at,
      created_at
    ) values (
      p_session_id,
      v_account.id,
      p_session_token_hash,
      p_session_expires_at,
      v_commit_at
    )
    returning * into v_session;
  exception
    when unique_violation
      or foreign_key_violation
      or check_violation
      or not_null_violation then
      return jsonb_build_object('status', 'integrity_conflict');
  end;

  return jsonb_build_object(
    'status', 'committed',
    'account', jsonb_build_object(
      'id', v_account.id,
      'email', v_account.email,
      'profile', v_account.profile,
      'created_at', v_account.created_at,
      'updated_at', v_account.updated_at
    ),
    'session', to_jsonb(v_session)
  );
end;
$$;

create or replace function public.exchange_commit_student_verification(
  p_account_id text,
  p_expected_session_id text,
  p_expected_session_token_hash text,
  p_school_name text,
  p_department_name text,
  p_verification_method text,
  p_school_email_verified boolean,
  p_verified_at timestamptz
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_account public.exchange_accounts%rowtype;
  v_session public.exchange_account_sessions%rowtype;
  v_school_email_verified boolean;
  v_commit_at timestamptz;
begin
  if p_account_id is null
     or btrim(p_account_id) = ''
     or p_expected_session_id is null
     or btrim(p_expected_session_id) = ''
     or p_expected_session_token_hash is null
     or char_length(p_expected_session_token_hash) < 32
     or btrim(coalesce(p_school_name, '')) = ''
     or p_verification_method is null
     or p_verification_method not in (
       'student_card',
       'school_email',
       'google_workspace',
       'microsoft_entra',
       'school_sso'
     ) then
    return jsonb_build_object('status', 'integrity_conflict');
  end if;

  perform pg_advisory_xact_lock(
    hashtext('exchange_atomic_auth_account_mutations')
  );

  -- Lock order is deliberately account then exact session for every student
  -- verification mutation.  Missing accounts are never created by this RPC.
  select account.* into v_account
  from public.exchange_accounts account
  where account.id = p_account_id
  for update;

  if not found then
    return jsonb_build_object('status', 'account_missing');
  end if;

  select session.* into v_session
  from public.exchange_account_sessions session
  where session.id = p_expected_session_id
    and session.account_id = p_account_id
    and session.token_hash = p_expected_session_token_hash
  for update;

  -- The datastore clock is sampled after both rows are locked so time spent
  -- waiting behind logout/delete is included in the expiry decision.
  v_commit_at := clock_timestamp();
  if not found or v_session.expires_at <= v_commit_at then
    return jsonb_build_object('status', 'session_invalid');
  end if;

  if coalesce(
    (v_account.profile ->> 'student_status_verified')::boolean,
    false
  ) then
    return jsonb_build_object(
      'status', 'already_verified',
      'account', jsonb_build_object(
        'id', v_account.id,
        'email', v_account.email,
        'profile', v_account.profile,
        'created_at', v_account.created_at,
        'updated_at', v_account.updated_at
      )
    );
  end if;

  v_school_email_verified := coalesce(
    (v_account.profile ->> 'school_email_verified')::boolean,
    false
  ) or coalesce(p_school_email_verified, false);

  update public.exchange_accounts account
  set profile = account.profile || jsonb_build_object(
        'home_university', p_school_name,
        'school_email_verified', v_school_email_verified,
        'student_status_verified', true,
        'verified_university', p_school_name,
        'verified_department', p_department_name,
        'student_verification_method', p_verification_method,
        'student_verified_at', v_commit_at,
        'updated_at', v_commit_at
      ),
      updated_at = v_commit_at
  where account.id = p_account_id
  returning * into v_account;

  return jsonb_build_object(
    'status', 'committed',
    'account', jsonb_build_object(
      'id', v_account.id,
      'email', v_account.email,
      'profile', v_account.profile,
      'created_at', v_account.created_at,
      'updated_at', v_account.updated_at
    )
  );
end;
$$;

-- Patch only explicitly approved profile fields under a row lock.  The
-- optional expected object provides field-level compare-and-set semantics, so
-- independent profile writers do not have to replace the entire profile or
-- overwrite a concurrent change.  JSON null and a missing current key compare
-- as the same value for expected checks.
create or replace function public.exchange_patch_account_profile(
  p_account_id text,
  p_updates jsonb,
  p_expected jsonb default '{}'::jsonb
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_account public.exchange_accounts%rowtype;
  v_allowed_fields text[] := array[
    'display_name',
    'avatar_url',
    'home_university',
    'target_countries',
    'application_stage',
    'followed_boards',
    'notification_preferences',
    'content_updates_seen_at',
    'email_verified',
    'community_suspended_until',
    'calendar_feed_token',
    'calendar_events',
    'calendar_last_synced_at',
    'product_tier'
  ];
  v_invalid_fields text[] := array[]::text[];
  v_conflicting_fields text[] := array[]::text[];
  v_key text;
  v_commit_at timestamptz;
begin
  if p_updates is null or jsonb_typeof(p_updates) <> 'object' then
    return jsonb_build_object(
      'status', 'invalid_fields',
      'source', 'updates',
      'fields', '[]'::jsonb
    );
  end if;

  if p_expected is null or jsonb_typeof(p_expected) <> 'object' then
    return jsonb_build_object(
      'status', 'invalid_fields',
      'source', 'expected',
      'fields', '[]'::jsonb
    );
  end if;

  for v_key in
    select key_name
    from jsonb_object_keys(p_updates) as update_key(key_name)
    order by key_name
  loop
    if not (v_key = any(v_allowed_fields)) then
      v_invalid_fields := array_append(v_invalid_fields, v_key);
    end if;
  end loop;

  if cardinality(v_invalid_fields) > 0 then
    return jsonb_build_object(
      'status', 'invalid_fields',
      'source', 'updates',
      'fields', to_jsonb(v_invalid_fields)
    );
  end if;

  v_invalid_fields := array[]::text[];
  for v_key in
    select key_name
    from jsonb_object_keys(p_expected) as expected_key(key_name)
    order by key_name
  loop
    if not (v_key = any(v_allowed_fields)) then
      v_invalid_fields := array_append(v_invalid_fields, v_key);
    end if;
  end loop;

  if cardinality(v_invalid_fields) > 0 then
    return jsonb_build_object(
      'status', 'invalid_fields',
      'source', 'expected',
      'fields', to_jsonb(v_invalid_fields)
    );
  end if;

  select account.* into v_account
  from public.exchange_accounts account
  where account.id = p_account_id
  for update;

  if not found then
    return jsonb_build_object('status', 'account_missing');
  end if;

  for v_key in
    select key_name
    from jsonb_object_keys(p_expected) as expected_key(key_name)
    order by key_name
  loop
    if coalesce(v_account.profile -> v_key, 'null'::jsonb)
       is distinct from coalesce(p_expected -> v_key, 'null'::jsonb) then
      v_conflicting_fields := array_append(v_conflicting_fields, v_key);
    end if;
  end loop;

  if cardinality(v_conflicting_fields) > 0 then
    return jsonb_build_object(
      'status', 'conflict',
      'fields', to_jsonb(v_conflicting_fields)
    );
  end if;

  v_commit_at := clock_timestamp();
  update public.exchange_accounts account
  set profile = account.profile || p_updates || jsonb_build_object(
        'updated_at', v_commit_at
      ),
      updated_at = v_commit_at
  where account.id = p_account_id
  returning * into v_account;

  return jsonb_build_object(
    'status', 'committed',
    'id', v_account.id,
    'email', v_account.email,
    'profile', v_account.profile,
    'created_at', v_account.created_at,
    'updated_at', v_account.updated_at
  );
end;
$$;

alter table public.exchange_account_provider_links enable row level security;

-- Runtime account changes must go through the field-level or auth-specific RPCs.
-- Keep direct read/insert/delete for repository bootstrap and account deletion,
-- while the production repository rejects its compatibility upsert entirely.
revoke update on table public.exchange_accounts from service_role;

revoke all on table public.exchange_account_provider_links
  from public, anon, authenticated;
revoke all on table public.exchange_account_provider_links from service_role;
grant select on table public.exchange_account_provider_links to service_role;

revoke all on function public.exchange_capture_initial_provider_links()
  from public, anon, authenticated;
revoke all on function public.exchange_protect_auth_owned_account_fields()
  from public, anon, authenticated;
revoke all on function public.exchange_commit_oauth_login(
  text, text, text, text, text, text, text, text, text, timestamptz, timestamptz
) from public, anon, authenticated;
revoke all on function public.exchange_commit_student_verification(
  text, text, text, text, text, text, boolean, timestamptz
) from public, anon, authenticated;
revoke all on function public.exchange_patch_account_profile(text, jsonb, jsonb)
  from public, anon, authenticated;

grant execute on function public.exchange_commit_oauth_login(
  text, text, text, text, text, text, text, text, text, timestamptz, timestamptz
) to service_role;
grant execute on function public.exchange_commit_student_verification(
  text, text, text, text, text, text, boolean, timestamptz
) to service_role;
grant execute on function public.exchange_patch_account_profile(text, jsonb, jsonb)
  to service_role;
