-- Extend the existing atomic workspace RPC; retain lock order, revision checks and progress ownership.
begin;

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
    'discovery',
    'planning_availability',
    'preparation_tasks',
    'selection_conditions',
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
    'generated_from_event_id',
    'effort_hours',
    'remaining_hours',
    'depends_on',
    'available_from',
    'waiting_reason',
    'document_id'
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

  -- Validate extension shapes before acquiring the existing account/workspace locks.
  if (p_candidate_workspace ? 'discovery'
      and jsonb_typeof(p_candidate_workspace -> 'discovery') <> 'object')
     or (p_candidate_workspace ? 'planning_availability'
         and jsonb_typeof(p_candidate_workspace -> 'planning_availability') not in ('object', 'null'))
     or (p_candidate_workspace ? 'preparation_tasks'
         and jsonb_typeof(p_candidate_workspace -> 'preparation_tasks') <> 'object')
     or (p_candidate_workspace ? 'selection_conditions'
         and jsonb_typeof(p_candidate_workspace -> 'selection_conditions') not in ('object', 'null')) then
    return jsonb_build_object('status', 'invalid_request', 'source', 'workspace_extensions');
  end if;
  if jsonb_typeof(p_candidate_workspace -> 'selection_conditions') = 'object' then
    if not (p_candidate_workspace -> 'selection_conditions' ? 'profile')
       or jsonb_typeof(p_candidate_workspace -> 'selection_conditions' -> 'profile') not in ('object', 'null')
       or exists (select 1 from jsonb_object_keys(p_candidate_workspace -> 'selection_conditions') as field(name)
                  where name <> 'profile') then
      return jsonb_build_object('status', 'invalid_request', 'source', 'selection_conditions');
    end if;
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

revoke all on function public.exchange_commit_account_workspace(
  text, text, bigint, jsonb, text, text, jsonb
) from public, anon, authenticated, service_role;
grant execute on function public.exchange_commit_account_workspace(
  text, text, bigint, jsonb, text, text, jsonb
) to service_role;

commit;
