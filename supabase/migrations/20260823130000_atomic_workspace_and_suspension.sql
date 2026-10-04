-- Workspace revisions and community suspensions are concurrency-owned state.
-- Keep their mutations inside short database transactions so multiple FastAPI
-- workers cannot lose updates or commit an account change without its audit.

alter table public.exchange_account_workspaces
  add column revision bigint;

-- Backfill the typed workspace revision from the legacy JSON payload.  A
-- missing revision is the documented initial revision (zero); an explicit but
-- malformed, fractional, negative, or out-of-range value aborts the migration
-- instead of silently resetting concurrency history.
do $migration$
declare
  v_row record;
  v_revision numeric;
begin
  for v_row in
    select workspace.account_id, workspace.home_school_key, workspace.workspace
    from public.exchange_account_workspaces workspace
    order by workspace.account_id, workspace.home_school_key
  loop
    if not (v_row.workspace ? 'revision') then
      continue;
    end if;

    if jsonb_typeof(v_row.workspace -> 'revision') <> 'number' then
      raise exception
        'workspace revision must be a non-negative bigint for account %, school %',
        v_row.account_id,
        v_row.home_school_key
        using errcode = '23514';
    end if;

    begin
      v_revision := (v_row.workspace ->> 'revision')::numeric;
    exception
      when data_exception then
        raise exception
          'workspace revision is not numeric for account %, school %',
          v_row.account_id,
          v_row.home_school_key
          using errcode = '23514';
    end;

    if v_revision < 0
       or trunc(v_revision) <> v_revision
       or v_revision > 9223372036854775807::numeric then
      raise exception
        'workspace revision is outside bigint range for account %, school %',
        v_row.account_id,
        v_row.home_school_key
        using errcode = '23514';
    end if;
  end loop;
end;
$migration$;

update public.exchange_account_workspaces workspace
set revision = case
  when workspace.workspace ? 'revision'
    then ((workspace.workspace ->> 'revision')::numeric)::bigint
  else 0
end;

alter table public.exchange_account_workspaces
  alter column revision set default 0,
  alter column revision set not null,
  add constraint exchange_account_workspaces_revision_nonnegative
    check (revision >= 0);

update public.exchange_account_workspaces workspace
set workspace = jsonb_set(
  workspace.workspace,
  '{revision}',
  to_jsonb(workspace.revision),
  true
);

alter table public.exchange_account_workspaces
  add constraint exchange_account_workspaces_revision_matches_payload
    check (
      coalesce(
        jsonb_typeof(workspace -> 'revision') = 'number'
        and (workspace ->> 'revision')::numeric = revision::numeric,
        false
      )
    );

create or replace function public.exchange_sync_workspace_revision()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  if new.workspace is null or jsonb_typeof(new.workspace) <> 'object' then
    raise exception 'workspace payload must be a JSON object'
      using errcode = '23514';
  end if;

  if new.revision is null or new.revision < 0 then
    raise exception 'workspace revision must be a non-negative bigint'
      using errcode = '23514';
  end if;

  new.workspace := jsonb_set(
    new.workspace,
    '{revision}',
    to_jsonb(new.revision),
    true
  );
  return new;
end;
$$;

create trigger exchange_sync_workspace_revision_trigger
before insert or update on public.exchange_account_workspaces
for each row execute function public.exchange_sync_workspace_revision();

alter table public.exchange_accounts
  add column community_suspended_until timestamptz;

-- The legacy profile value must be an explicit ISO-8601 timestamp with a time
-- zone. PostgreSQL accepts convenient strings such as "tomorrow" as a
-- timestamptz, so validate the wire shape before casting and fail closed.
do $migration$
declare
  v_row record;
  v_deadline timestamptz;
begin
  for v_row in
    select account.id, account.profile -> 'community_suspended_until' as raw_value
    from public.exchange_accounts account
    where account.profile ? 'community_suspended_until'
      and account.profile -> 'community_suspended_until' <> 'null'::jsonb
    order by account.id
  loop
    if jsonb_typeof(v_row.raw_value) <> 'string'
       or (v_row.raw_value #>> '{}') !~
         '^[0-9]{4}-[0-9]{2}-[0-9]{2}[T ][0-9]{2}:[0-9]{2}:[0-9]{2}([.][0-9]+)?(Z|[+-][0-9]{2}(:[0-9]{2})?)$' then
      raise exception
        'community suspension must be an ISO-8601 timestamp for account %',
        v_row.id
        using errcode = '23514';
    end if;

    begin
      v_deadline := (v_row.raw_value #>> '{}')::timestamptz;
    exception
      when data_exception then
        raise exception
          'community suspension timestamp is invalid for account %',
          v_row.id
          using errcode = '23514';
    end;
  end loop;
end;
$migration$;

update public.exchange_accounts account
set community_suspended_until = case
  when not (account.profile ? 'community_suspended_until')
    or account.profile -> 'community_suspended_until' = 'null'::jsonb
    then null
  else (account.profile ->> 'community_suspended_until')::timestamptz
end;

-- Canonicalize the compatibility profile field once.  From this point onward
-- the typed column is authoritative and a trigger mirrors it into profile JSON
-- for existing application readers.
update public.exchange_accounts account
set profile = account.profile || jsonb_build_object(
      'community_suspended_until', account.community_suspended_until
    );

create or replace function public.exchange_sync_account_community_suspension()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  if new.profile is null or jsonb_typeof(new.profile) <> 'object' then
    raise exception 'account profile must be a JSON object'
      using errcode = '23514';
  end if;

  if tg_op = 'INSERT' then
    if new.community_suspended_until is not null then
      raise exception
        'new accounts cannot start with an unaudited community suspension'
        using errcode = '42501';
    end if;
  elsif tg_op = 'UPDATE' then
    if new.community_suspended_until
         is distinct from old.community_suspended_until
       and coalesce(
         current_setting('exchange.community_suspension_write', true),
         'off'
       ) <> 'on' then
      raise exception
        'community suspension may only change through its audited mutation'
        using errcode = '42501';
    end if;
  end if;

  new.profile := new.profile || jsonb_build_object(
    'community_suspended_until', new.community_suspended_until
  );
  return new;
end;
$$;

create trigger exchange_sync_account_community_suspension_trigger
before insert or update on public.exchange_accounts
for each row execute function public.exchange_sync_account_community_suspension();

-- Replace the previous field patch function with the same signature, but make
-- community_suspended_until unavailable to general profile writers.  The
-- dedicated audited suspension RPC below is its only application write path.
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

create or replace function public.exchange_commit_account_workspace(
  p_account_id text,
  p_home_school_key text,
  p_expected_revision bigint,
  p_candidate_workspace jsonb,
  p_mutation_kind text,
  p_progress_key text,
  p_progress jsonb
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_account_id text := nullif(btrim(p_account_id), '');
  v_home_school_key text := nullif(
    lower(
      regexp_replace(
        btrim(p_home_school_key),
        '[[:space:]]+',
        ' ',
        'g'
      )
    ),
    ''
  );
  v_progress_key text := nullif(btrim(p_progress_key), '');
  v_candidate_home_school_key text;
  v_context_home_school_key text;
  v_account public.exchange_accounts%rowtype;
  v_workspace public.exchange_account_workspaces%rowtype;
  v_workspace_exists boolean := false;
  v_allowed_workspace_fields text[] := array[
    'home_school',
    'revision',
    'favorite_schools',
    'application_schools',
    'application_progress',
    'document_readiness',
    'application_context',
    'application_selections',
    'submission_progress',
    'budget_plans',
    'deadline_events',
    'updated_at'
  ];
  v_allowed_event_fields text[] := array[
    'id',
    'title',
    'date',
    'category',
    'reminder_days',
    'note',
    'source_url',
    'origin',
    'school_name',
    'preparation_days',
    'status',
    'generated_from_event_id'
  ];
  v_allowed_progress_fields text[] := array[
    'title',
    'method',
    'status',
    'responsible_unit',
    'send_by_at',
    'arrival_deadline_at',
    'proof_metadata',
    'recorded_by',
    'platform_submitted',
    'note',
    'started_at',
    'submitted_at',
    'receipt_confirmed_at',
    'completed_at',
    'updated_at'
  ];
  v_allowed_proof_fields text[] := array[
    'kind',
    'reference',
    'file_name',
    'content_type',
    'source',
    'original_file_stored',
    'recorded_at'
  ];
  v_invalid_fields text[] := array[]::text[];
  v_key text;
  v_current_revision bigint;
  v_next_revision bigint;
  v_commit_at timestamptz;
  v_preserved_progress jsonb;
  v_next_workspace jsonb;
  v_next_progress jsonb;
  v_calendar_events jsonb;
begin
  if v_account_id is null
     or char_length(v_account_id) > 128
     or v_home_school_key is null
     or char_length(v_home_school_key) > 200
     or p_expected_revision is null
     or p_expected_revision < 0
     or p_candidate_workspace is null
     or jsonb_typeof(p_candidate_workspace) <> 'object'
     or p_mutation_kind is null
     or p_mutation_kind not in (
       'workspace_replace',
       'submission_progress_transition'
     ) then
    return jsonb_build_object('status', 'invalid_request', 'source', 'request');
  end if;

  if p_mutation_kind = 'workspace_replace'
     and (p_progress_key is not null or p_progress is not null) then
    return jsonb_build_object('status', 'invalid_request', 'source', 'progress');
  end if;

  if p_mutation_kind = 'submission_progress_transition'
     and (
       v_progress_key is null
       or char_length(v_progress_key) > 240
       or p_progress is null
       or jsonb_typeof(p_progress) <> 'object'
     ) then
    return jsonb_build_object('status', 'invalid_request', 'source', 'progress');
  end if;

  for v_key in
    select key_name
    from jsonb_object_keys(p_candidate_workspace) as candidate_key(key_name)
    order by key_name
  loop
    if not (v_key = any(v_allowed_workspace_fields)) then
      v_invalid_fields := array_append(v_invalid_fields, v_key);
    end if;
  end loop;

  if cardinality(v_invalid_fields) > 0 then
    return jsonb_build_object(
      'status', 'invalid_request',
      'source', 'candidate_workspace',
      'fields', to_jsonb(v_invalid_fields)
    );
  end if;

  if not (p_candidate_workspace ? 'home_school')
     or jsonb_typeof(p_candidate_workspace -> 'home_school') <> 'string'
     or btrim(p_candidate_workspace ->> 'home_school') = ''
     or char_length(p_candidate_workspace ->> 'home_school') > 80
     or not (p_candidate_workspace ? 'application_context')
     or jsonb_typeof(p_candidate_workspace -> 'application_context') <> 'object'
     or jsonb_typeof(
       p_candidate_workspace -> 'application_context' -> 'school_name'
     ) <> 'string'
     or (
       p_candidate_workspace ? 'favorite_schools'
       and jsonb_typeof(p_candidate_workspace -> 'favorite_schools') <> 'array'
     )
     or (
       p_candidate_workspace ? 'application_schools'
       and jsonb_typeof(p_candidate_workspace -> 'application_schools') <> 'array'
     )
     or (
       p_candidate_workspace ? 'application_progress'
       and jsonb_typeof(p_candidate_workspace -> 'application_progress') <> 'object'
     )
     or (
       p_candidate_workspace ? 'document_readiness'
       and jsonb_typeof(p_candidate_workspace -> 'document_readiness') <> 'object'
     )
     or (
       p_candidate_workspace ? 'application_selections'
       and jsonb_typeof(p_candidate_workspace -> 'application_selections') <> 'object'
     )
     or (
       p_candidate_workspace ? 'submission_progress'
       and jsonb_typeof(p_candidate_workspace -> 'submission_progress') <> 'object'
     )
     or (
       p_candidate_workspace ? 'budget_plans'
       and jsonb_typeof(p_candidate_workspace -> 'budget_plans') <> 'object'
     )
     or (
       p_candidate_workspace ? 'deadline_events'
       and jsonb_typeof(p_candidate_workspace -> 'deadline_events') <> 'array'
     ) then
    return jsonb_build_object(
      'status', 'invalid_request',
      'source', 'candidate_workspace_shape'
    );
  end if;

  v_candidate_home_school_key := lower(
    regexp_replace(
      btrim(p_candidate_workspace ->> 'home_school'),
      '[[:space:]]+',
      ' ',
      'g'
    )
  );
  v_context_home_school_key := lower(
    regexp_replace(
      btrim(
        p_candidate_workspace -> 'application_context' ->> 'school_name'
      ),
      '[[:space:]]+',
      ' ',
      'g'
    )
  );

  if v_candidate_home_school_key <> v_home_school_key
     or v_context_home_school_key <> v_home_school_key then
    return jsonb_build_object(
      'status', 'invalid_request',
      'source', 'home_school_identity'
    );
  end if;

  if exists (
    select 1
    from jsonb_array_elements(
      coalesce(p_candidate_workspace -> 'deadline_events', '[]'::jsonb)
    ) as event(value)
    where jsonb_typeof(event.value) <> 'object'
      or jsonb_typeof(event.value -> 'id') <> 'string'
      or btrim(coalesce(event.value ->> 'id', '')) = ''
      or char_length(coalesce(event.value ->> 'id', '')) > 180
  ) then
    return jsonb_build_object(
      'status', 'invalid_request',
      'source', 'deadline_events'
    );
  end if;

  if exists (
    select 1
    from jsonb_array_elements(
      coalesce(p_candidate_workspace -> 'deadline_events', '[]'::jsonb)
    ) as event(value)
    cross join lateral jsonb_object_keys(event.value) as event_key(key_name)
    where not (event_key.key_name = any(v_allowed_event_fields))
  ) then
    return jsonb_build_object(
      'status', 'invalid_request',
      'source', 'deadline_event_fields'
    );
  end if;

  if p_mutation_kind = 'submission_progress_transition' then
    v_invalid_fields := array[]::text[];
    for v_key in
      select key_name
      from jsonb_object_keys(p_progress) as progress_field(key_name)
      order by key_name
    loop
      if not (v_key = any(v_allowed_progress_fields)) then
        v_invalid_fields := array_append(v_invalid_fields, v_key);
      end if;
    end loop;

    if cardinality(v_invalid_fields) > 0 then
      return jsonb_build_object(
        'status', 'invalid_request',
        'source', 'progress_fields',
        'fields', to_jsonb(v_invalid_fields)
      );
    end if;

    if jsonb_typeof(p_progress -> 'title') <> 'string'
       or btrim(coalesce(p_progress ->> 'title', '')) = ''
       or char_length(coalesce(p_progress ->> 'title', '')) > 240
       or coalesce(p_progress ->> 'method', '') not in (
         'paper', 'online', 'email', 'in_person', 'mixed'
       )
       or coalesce(p_progress ->> 'status', '') not in (
         'not_started',
         'preparing',
         'submitted',
         'receipt_confirmed',
         'completed'
       )
       or (
         p_progress ? 'recorded_by'
         and p_progress ->> 'recorded_by' <> 'student'
       )
       or (
         p_progress ? 'platform_submitted'
         and p_progress -> 'platform_submitted' <> 'false'::jsonb
       ) then
      return jsonb_build_object(
        'status', 'invalid_request',
        'source', 'progress_shape'
      );
    end if;

    if p_progress ? 'proof_metadata'
       and p_progress -> 'proof_metadata' <> 'null'::jsonb then
      if jsonb_typeof(p_progress -> 'proof_metadata') <> 'object' then
        return jsonb_build_object(
          'status', 'invalid_request',
          'source', 'proof_metadata'
        );
      end if;

      v_invalid_fields := array[]::text[];
      for v_key in
        select key_name
        from jsonb_object_keys(
          p_progress -> 'proof_metadata'
        ) as proof_field(key_name)
        order by key_name
      loop
        if not (v_key = any(v_allowed_proof_fields)) then
          v_invalid_fields := array_append(v_invalid_fields, v_key);
        end if;
      end loop;

      if cardinality(v_invalid_fields) > 0
         or (
           p_progress -> 'proof_metadata' ? 'source'
           and p_progress -> 'proof_metadata' ->> 'source' <> 'student_reported'
         )
         or (
           p_progress -> 'proof_metadata' ? 'original_file_stored'
           and p_progress -> 'proof_metadata' -> 'original_file_stored'
             <> 'false'::jsonb
         ) then
        return jsonb_build_object(
          'status', 'invalid_request',
          'source', 'proof_metadata_fields',
          'fields', to_jsonb(v_invalid_fields)
        );
      end if;
    end if;
  end if;

  -- Every workspace mutation locks the account first, then exactly one school
  -- workspace. The account lock also makes an absent workspace row lockable and
  -- serializes account deletion and the account-level calendar projection.
  select account.* into v_account
  from public.exchange_accounts account
  where account.id = v_account_id
  for update;

  if not found then
    return jsonb_build_object('status', 'account_missing');
  end if;

  select workspace.* into v_workspace
  from public.exchange_account_workspaces workspace
  where workspace.account_id = v_account_id
    and workspace.home_school_key = v_home_school_key
  for update;
  v_workspace_exists := found;

  v_current_revision := case
    when v_workspace_exists then v_workspace.revision
    else 0
  end;

  if v_current_revision <> p_expected_revision then
    return jsonb_build_object(
      'status', 'conflict',
      'exists', v_workspace_exists,
      'current_revision', v_current_revision,
      'current_workspace', case
        when v_workspace_exists then v_workspace.workspace
        else null
      end
    );
  end if;

  if v_current_revision = 9223372036854775807::bigint then
    return jsonb_build_object('status', 'integrity_conflict');
  end if;

  if v_workspace_exists then
    if jsonb_typeof(v_workspace.workspace) <> 'object'
       or jsonb_typeof(v_workspace.workspace -> 'revision') <> 'number'
       or (v_workspace.workspace ->> 'revision')::numeric
         <> v_workspace.revision::numeric then
      return jsonb_build_object('status', 'integrity_conflict');
    end if;

    if v_workspace.workspace ? 'submission_progress'
       and jsonb_typeof(v_workspace.workspace -> 'submission_progress')
         <> 'object' then
      return jsonb_build_object('status', 'integrity_conflict');
    end if;

    v_preserved_progress := coalesce(
      v_workspace.workspace -> 'submission_progress',
      '{}'::jsonb
    );
  else
    v_preserved_progress := '{}'::jsonb;
  end if;

  v_next_revision := v_current_revision + 1;
  v_commit_at := clock_timestamp();

  if p_mutation_kind = 'workspace_replace' then
    v_next_workspace :=
      (
        p_candidate_workspace
        - 'revision'
        - 'updated_at'
        - 'submission_progress'
      )
      || jsonb_build_object(
        'submission_progress', v_preserved_progress,
        'revision', v_next_revision,
        'updated_at', v_commit_at
      );
  else
    if v_workspace_exists then
      v_next_workspace := v_workspace.workspace;
    else
      -- A first progress transition may create the school workspace, but no
      -- client-supplied progress siblings are imported with it.
      v_next_workspace :=
        (
          p_candidate_workspace
          - 'revision'
          - 'updated_at'
          - 'submission_progress'
        )
        || jsonb_build_object('submission_progress', '{}'::jsonb);
    end if;

    v_next_progress :=
      (p_progress - 'updated_at')
      || jsonb_build_object(
        'recorded_by', 'student',
        'platform_submitted', false,
        'updated_at', v_commit_at
      );

    v_next_workspace := jsonb_set(
      v_next_workspace || jsonb_build_object(
        'submission_progress', v_preserved_progress
      ),
      array['submission_progress', v_progress_key],
      v_next_progress,
      true
    ) || jsonb_build_object(
      'revision', v_next_revision,
      'updated_at', v_commit_at
    );
  end if;

  begin
    if v_workspace_exists then
      update public.exchange_account_workspaces workspace
      set workspace = v_next_workspace,
          revision = v_next_revision,
          updated_at = v_commit_at
      where workspace.account_id = v_account_id
        and workspace.home_school_key = v_home_school_key
      returning * into v_workspace;
    else
      insert into public.exchange_account_workspaces (
        account_id,
        home_school_key,
        workspace,
        revision,
        updated_at
      ) values (
        v_account_id,
        v_home_school_key,
        v_next_workspace,
        v_next_revision,
        v_commit_at
      )
      returning * into v_workspace;
    end if;

    -- Fail the whole subtransaction if any stored workspace cannot safely
    -- participate in the account-level deadline projection.
    if exists (
      select 1
      from public.exchange_account_workspaces workspace
      where workspace.account_id = v_account_id
        and workspace.workspace ? 'deadline_events'
        and jsonb_typeof(workspace.workspace -> 'deadline_events') <> 'array'
    ) then
      raise exception 'stored workspace deadline_events is not an array'
        using errcode = '23514';
    end if;

    if exists (
      select 1
      from public.exchange_account_workspaces workspace
      cross join lateral jsonb_array_elements(
        coalesce(workspace.workspace -> 'deadline_events', '[]'::jsonb)
      ) as event(value)
      where workspace.account_id = v_account_id
        and (
          jsonb_typeof(event.value) <> 'object'
          or jsonb_typeof(event.value -> 'id') <> 'string'
          or btrim(coalesce(event.value ->> 'id', '')) = ''
          or char_length(coalesce(event.value ->> 'id', '')) > 180
        )
    ) then
      raise exception 'stored workspace contains an invalid deadline event'
        using errcode = '23514';
    end if;

    if exists (
      select 1
      from public.exchange_account_workspaces workspace
      cross join lateral jsonb_array_elements(
        coalesce(workspace.workspace -> 'deadline_events', '[]'::jsonb)
      ) as event(value)
      cross join lateral jsonb_object_keys(event.value) as event_key(key_name)
      where workspace.account_id = v_account_id
        and not (event_key.key_name = any(v_allowed_event_fields))
    ) then
      raise exception 'stored workspace contains unknown deadline event fields'
        using errcode = '23514';
    end if;

    -- The most recently updated workspace wins when two schools accidentally
    -- reuse an event id.  The final array order is stable for clients and feed
    -- hashing, while all input rows are read after the account lock was taken.
    select coalesce(
      jsonb_agg(
        chosen.event_value
        order by
          chosen.event_value ->> 'date',
          chosen.event_value ->> 'id'
      ),
      '[]'::jsonb
    ) into v_calendar_events
    from (
      select distinct on (event.value ->> 'id')
        event.value as event_value,
        workspace.updated_at as source_updated_at,
        workspace.home_school_key as source_home_school_key,
        event.position as source_position
      from public.exchange_account_workspaces workspace
      cross join lateral jsonb_array_elements(
        coalesce(workspace.workspace -> 'deadline_events', '[]'::jsonb)
      ) with ordinality as event(value, position)
      where workspace.account_id = v_account_id
      order by
        event.value ->> 'id',
        workspace.updated_at desc,
        workspace.home_school_key desc,
        event.position desc
    ) as chosen;

    update public.exchange_accounts account
    set profile = account.profile || jsonb_build_object(
          'calendar_events', v_calendar_events,
          'calendar_last_synced_at', v_commit_at,
          'updated_at', v_commit_at
        ),
        updated_at = v_commit_at
    where account.id = v_account_id
    returning * into v_account;
  exception
    when integrity_constraint_violation or data_exception then
      return jsonb_build_object('status', 'integrity_conflict');
  end;

  return jsonb_build_object(
    'status', 'committed',
    'home_school_key', v_home_school_key,
    'revision', v_workspace.revision,
    'committed_at', v_commit_at,
    'workspace', v_workspace.workspace,
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

create table public.exchange_community_suspension_audits (
  id text primary key,
  identity_id text not null,
  target_account_id text
    references public.exchange_accounts(id) on delete set null,
  moderator_id text
    references public.exchange_accounts(id) on delete set null,
  previous_suspended_until timestamptz,
  new_suspended_until timestamptz not null,
  reason text not null,
  request_fingerprint text not null,
  created_at timestamptz not null default now(),
  retained_until timestamptz not null,
  constraint exchange_community_suspension_audits_id_nonempty
    check (btrim(id) <> '' and char_length(id) <= 128),
  constraint exchange_community_suspension_audits_identity_nonempty
    check (
      btrim(identity_id) <> ''
      and char_length(identity_id) <= 128
    ),
  constraint exchange_community_suspension_audits_reason_length
    check (char_length(btrim(reason)) between 2 and 500),
  constraint exchange_community_suspension_audits_future_deadline
    check (new_suspended_until > created_at),
  constraint exchange_community_suspension_audits_fingerprint_shape
    check (request_fingerprint ~ '^[0-9a-f]{64}$'),
  constraint exchange_community_suspension_audits_retention
    check (retained_until = created_at + interval '2160 hours')
);

create index exchange_community_suspension_audits_identity_idx
  on public.exchange_community_suspension_audits (identity_id, created_at desc);

create index exchange_community_suspension_audits_target_idx
  on public.exchange_community_suspension_audits (
    target_account_id,
    created_at desc
  );

create index exchange_community_suspension_audits_moderator_idx
  on public.exchange_community_suspension_audits (
    moderator_id,
    created_at desc
  );

create index exchange_community_suspension_audits_retention_idx
  on public.exchange_community_suspension_audits (retained_until);

alter table public.exchange_community_suspension_audits enable row level security;
alter table public.exchange_community_suspension_audits force row level security;

-- Application roles cannot update audit content.  The only tolerated row
-- update is an FK ON DELETE SET NULL transition, which preserves the event
-- after an account invokes deletion.  Expired deletion requires the guarded
-- purge RPC below.
create or replace function public.exchange_enforce_suspension_audit_append_only()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  if tg_op = 'UPDATE' then
    if (to_jsonb(new) - array['target_account_id', 'moderator_id'])
         = (to_jsonb(old) - array['target_account_id', 'moderator_id'])
       and (
         new.target_account_id is not distinct from old.target_account_id
         or (old.target_account_id is not null and new.target_account_id is null)
       )
       and (
         new.moderator_id is not distinct from old.moderator_id
         or (old.moderator_id is not null and new.moderator_id is null)
       ) then
      return new;
    end if;

    raise exception 'community suspension audits are append-only'
      using errcode = '42501';
  end if;

  if tg_op = 'DELETE'
     and coalesce(
       current_setting('exchange.community_suspension_audit_purge', true),
       'off'
     ) <> 'on' then
    raise exception 'community suspension audits may only be deleted after retention'
      using errcode = '42501';
  end if;

  return old;
end;
$$;

create trigger exchange_enforce_suspension_audit_append_only_trigger
before update or delete on public.exchange_community_suspension_audits
for each row execute function public.exchange_enforce_suspension_audit_append_only();

create or replace function public.exchange_commit_community_suspension(
  p_event_id text,
  p_identity_id text,
  p_account_id text,
  p_moderator_id text,
  p_expected_suspended_until timestamptz,
  p_suspended_until timestamptz,
  p_reason text
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_event_id text := nullif(btrim(p_event_id), '');
  v_identity_id text := nullif(btrim(p_identity_id), '');
  v_account_id text := nullif(btrim(p_account_id), '');
  v_moderator_id text := nullif(btrim(p_moderator_id), '');
  v_reason text := nullif(btrim(p_reason), '');
  v_locked_account record;
  v_target_found boolean := false;
  v_moderator_found boolean := false;
  v_current_suspended_until timestamptz;
  v_commit_at timestamptz;
  v_request_fingerprint text;
  v_target_account public.exchange_accounts%rowtype;
  v_existing_audit public.exchange_community_suspension_audits%rowtype;
  v_audit public.exchange_community_suspension_audits%rowtype;
  v_audit_json jsonb;
begin
  if v_event_id is null
     or char_length(v_event_id) > 128
     or v_identity_id is null
     or char_length(v_identity_id) > 128
     or v_account_id is null
     or char_length(v_account_id) > 128
     or v_moderator_id is null
     or char_length(v_moderator_id) > 128
     or v_reason is null
     or char_length(v_reason) > 500 then
    return jsonb_build_object('status', 'integrity_conflict');
  end if;

  v_request_fingerprint := encode(
    sha256(
      convert_to(
        jsonb_build_array(
          v_identity_id,
          v_account_id,
          v_moderator_id,
          case
            when p_expected_suspended_until is null then null
            else extract(epoch from p_expected_suspended_until)
          end,
          case
            when p_suspended_until is null then null
            else extract(epoch from p_suspended_until)
          end,
          v_reason
        )::text,
        'UTF8'
      )
    ),
    'hex'
  );

  -- Return an already committed event before revalidating a deadline against
  -- the current clock. A response-lost retry must stay idempotent even after the
  -- original future deadline has elapsed.
  select audit.* into v_existing_audit
  from public.exchange_community_suspension_audits audit
  where audit.id = v_event_id;

  if found then
    if v_existing_audit.request_fingerprint = v_request_fingerprint then
      select account.* into v_target_account
      from public.exchange_accounts account
      where account.id = v_account_id;
      v_target_found := found;

      v_audit_json :=
        (to_jsonb(v_existing_audit) - 'request_fingerprint' - 'identity_id')
        || jsonb_build_object(
        'resource_type', 'identity',
        'resource_id', v_existing_audit.identity_id,
        'previous_status', case
          when v_existing_audit.previous_suspended_until is null
            or v_existing_audit.previous_suspended_until
              <= v_existing_audit.created_at then 'active'
          else 'suspended'
        end,
        'new_status', 'suspended',
        'moderator_id', coalesce(
          v_existing_audit.moderator_id,
          'deleted-moderator'
        ),
        'note', v_existing_audit.reason
      );
      if v_target_found then
        return jsonb_build_object(
          'status', 'committed',
          'idempotent', true,
          'audit', v_audit_json,
          'account', jsonb_build_object(
            'id', v_target_account.id,
            'email', v_target_account.email,
            'profile', v_target_account.profile,
            'community_suspended_until',
              v_target_account.community_suspended_until,
            'created_at', v_target_account.created_at,
            'updated_at', v_target_account.updated_at
          )
        );
      end if;

      return jsonb_build_object(
        'status', 'committed',
        'idempotent', true,
        'audit', v_audit_json
      );
    end if;

    return jsonb_build_object('status', 'idempotency_conflict');
  end if;

  -- Lock both target and moderator accounts in lexical id order. This remains
  -- deadlock-safe when two moderators target each other or share a target.
  for v_locked_account in
    select account.id, account.community_suspended_until
    from public.exchange_accounts account
    where account.id in (v_account_id, v_moderator_id)
    order by account.id
    for update
  loop
    if v_locked_account.id = v_account_id then
      v_target_found := true;
      v_current_suspended_until := v_locked_account.community_suspended_until;
    end if;
    if v_locked_account.id = v_moderator_id then
      v_moderator_found := true;
    end if;
  end loop;

  if not v_target_found then
    return jsonb_build_object('status', 'account_missing');
  end if;

  if not v_moderator_found then
    return jsonb_build_object('status', 'moderator_missing');
  end if;

  select account.* into v_target_account
  from public.exchange_accounts account
  where account.id = v_account_id;

  -- A concurrent call with the same event id may have committed while this
  -- call waited for its account locks, so repeat the idempotency decision.
  select audit.* into v_existing_audit
  from public.exchange_community_suspension_audits audit
  where audit.id = v_event_id;

  if found then
    if v_existing_audit.request_fingerprint = v_request_fingerprint then
      v_audit_json :=
        (to_jsonb(v_existing_audit) - 'request_fingerprint' - 'identity_id')
        || jsonb_build_object(
        'resource_type', 'identity',
        'resource_id', v_existing_audit.identity_id,
        'previous_status', case
          when v_existing_audit.previous_suspended_until is null
            or v_existing_audit.previous_suspended_until
              <= v_existing_audit.created_at then 'active'
          else 'suspended'
        end,
        'new_status', 'suspended',
        'moderator_id', coalesce(
          v_existing_audit.moderator_id,
          'deleted-moderator'
        ),
        'note', v_existing_audit.reason
      );
      return jsonb_build_object(
        'status', 'committed',
        'idempotent', true,
        'audit', v_audit_json,
        'account', jsonb_build_object(
          'id', v_target_account.id,
          'email', v_target_account.email,
          'profile', v_target_account.profile,
          'community_suspended_until',
            v_target_account.community_suspended_until,
          'created_at', v_target_account.created_at,
          'updated_at', v_target_account.updated_at
        )
      );
    end if;

    return jsonb_build_object('status', 'idempotency_conflict');
  end if;

  v_commit_at := clock_timestamp();
  if p_suspended_until is null or p_suspended_until <= v_commit_at then
    return jsonb_build_object('status', 'invalid_deadline');
  end if;

  if v_current_suspended_until is distinct from p_expected_suspended_until then
    return jsonb_build_object(
      'status', 'conflict',
      'current_suspended_until', v_current_suspended_until,
      'account', jsonb_build_object(
        'id', v_target_account.id,
        'email', v_target_account.email,
        'profile', v_target_account.profile,
        'community_suspended_until',
          v_target_account.community_suspended_until,
        'created_at', v_target_account.created_at,
        'updated_at', v_target_account.updated_at
      )
    );
  end if;

  if v_current_suspended_until is not distinct from p_suspended_until then
    return jsonb_build_object(
      'status', 'no_change',
      'current_suspended_until', v_current_suspended_until,
      'account', jsonb_build_object(
        'id', v_target_account.id,
        'email', v_target_account.email,
        'profile', v_target_account.profile,
        'community_suspended_until',
          v_target_account.community_suspended_until,
        'created_at', v_target_account.created_at,
        'updated_at', v_target_account.updated_at
      )
    );
  end if;

  begin
    perform set_config('exchange.community_suspension_write', 'on', true);

    update public.exchange_accounts account
    set community_suspended_until = p_suspended_until,
        profile = account.profile || jsonb_build_object(
          'community_suspended_until', p_suspended_until,
          'updated_at', v_commit_at
        ),
        updated_at = v_commit_at
    where account.id = v_account_id
    returning * into v_target_account;

    perform set_config('exchange.community_suspension_write', 'off', true);

    insert into public.exchange_community_suspension_audits (
      id,
      identity_id,
      target_account_id,
      moderator_id,
      previous_suspended_until,
      new_suspended_until,
      reason,
      request_fingerprint,
      created_at,
      retained_until
    ) values (
      v_event_id,
      v_identity_id,
      v_account_id,
      v_moderator_id,
      v_current_suspended_until,
      p_suspended_until,
      v_reason,
      v_request_fingerprint,
      v_commit_at,
      v_commit_at + interval '2160 hours'
    )
    returning * into v_audit;
  exception
    when unique_violation then
      -- A reused event id against another target may race without sharing an
      -- account lock. The subtransaction has rolled back the account update;
      -- classify the now-visible winner instead of leaking a duplicate error.
      select audit.* into v_existing_audit
      from public.exchange_community_suspension_audits audit
      where audit.id = v_event_id;

      if found
         and v_existing_audit.request_fingerprint = v_request_fingerprint then
        v_audit_json :=
          (to_jsonb(v_existing_audit) - 'request_fingerprint' - 'identity_id')
          || jsonb_build_object(
          'resource_type', 'identity',
          'resource_id', v_existing_audit.identity_id,
          'previous_status', case
            when v_existing_audit.previous_suspended_until is null
              or v_existing_audit.previous_suspended_until
                <= v_existing_audit.created_at then 'active'
            else 'suspended'
          end,
          'new_status', 'suspended',
          'moderator_id', coalesce(
            v_existing_audit.moderator_id,
            'deleted-moderator'
          ),
          'note', v_existing_audit.reason
        );
        return jsonb_build_object(
          'status', 'committed',
          'idempotent', true,
          'audit', v_audit_json
        );
      end if;

      return jsonb_build_object('status', 'idempotency_conflict');
    when foreign_key_violation
      or check_violation
      or not_null_violation
      or data_exception then
      return jsonb_build_object('status', 'integrity_conflict');
  end;

  v_audit_json :=
    (to_jsonb(v_audit) - 'request_fingerprint' - 'identity_id')
    || jsonb_build_object(
    'resource_type', 'identity',
    'resource_id', v_audit.identity_id,
    'previous_status', case
      when v_audit.previous_suspended_until is null
        or v_audit.previous_suspended_until <= v_audit.created_at then 'active'
      else 'suspended'
    end,
    'new_status', 'suspended',
    'moderator_id', coalesce(v_audit.moderator_id, 'deleted-moderator'),
    'note', v_audit.reason
  );

  return jsonb_build_object(
    'status', 'committed',
    'idempotent', false,
    'audit', v_audit_json,
    'account', jsonb_build_object(
      'id', v_target_account.id,
      'email', v_target_account.email,
      'profile', v_target_account.profile,
      'community_suspended_until',
        v_target_account.community_suspended_until,
      'created_at', v_target_account.created_at,
      'updated_at', v_target_account.updated_at
    )
  );
end;
$$;

create or replace function public.exchange_purge_expired_community_suspension_audits()
returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_purged_at timestamptz := clock_timestamp();
  v_deleted_count bigint;
begin
  perform set_config(
    'exchange.community_suspension_audit_purge',
    'on',
    true
  );

  delete from public.exchange_community_suspension_audits audit
  where audit.retained_until <= v_purged_at;
  get diagnostics v_deleted_count = row_count;

  perform set_config(
    'exchange.community_suspension_audit_purge',
    'off',
    true
  );

  return jsonb_build_object(
    'status', 'committed',
    'deleted_count', v_deleted_count,
    'purged_at', v_purged_at
  );
end;
$$;

-- Tables remain private. Workspace writes and audit inserts/deletes are only
-- available through the SECURITY DEFINER functions above.
revoke update on table public.exchange_accounts from service_role;

revoke all on table public.exchange_account_workspaces
  from public, anon, authenticated;
revoke insert, update, delete on table public.exchange_account_workspaces
  from service_role;
grant select on table public.exchange_account_workspaces to service_role;

revoke all on table public.exchange_community_suspension_audits
  from public, anon, authenticated, service_role;
grant select on table public.exchange_community_suspension_audits
  to service_role;

revoke all on function public.exchange_sync_workspace_revision()
  from public, anon, authenticated, service_role;
revoke all on function public.exchange_sync_account_community_suspension()
  from public, anon, authenticated, service_role;
revoke all on function public.exchange_enforce_suspension_audit_append_only()
  from public, anon, authenticated, service_role;
revoke all on function public.exchange_patch_account_profile(text, jsonb, jsonb)
  from public, anon, authenticated, service_role;
revoke all on function public.exchange_commit_account_workspace(
  text, text, bigint, jsonb, text, text, jsonb
) from public, anon, authenticated, service_role;
revoke all on function public.exchange_commit_community_suspension(
  text, text, text, text, timestamptz, timestamptz, text
) from public, anon, authenticated, service_role;
revoke all on function public.exchange_purge_expired_community_suspension_audits()
  from public, anon, authenticated, service_role;

grant execute on function public.exchange_patch_account_profile(
  text, jsonb, jsonb
) to service_role;
grant execute on function public.exchange_commit_account_workspace(
  text, text, bigint, jsonb, text, text, jsonb
) to service_role;
grant execute on function public.exchange_commit_community_suspension(
  text, text, text, text, timestamptz, timestamptz, text
) to service_role;
grant execute on function public.exchange_purge_expired_community_suspension_audits()
  to service_role;
