-- The student-card check is gone: an account now posts under the school it picked (or the one its school mail domain names),
-- and cannot change that school again for three days. The application layer only lets a school it supports reach these
-- functions, so the database only has to stop treating "no verified student" as "no school".
--
-- The functions are patched in place by replacing the exact lines that tested the verified-student fields, so the rest of
-- each (long) function stays as deployed. Every step refuses to continue when the text it expects is not there, and is
-- skipped when it has already been applied, so the migration can be run again safely.

do $migration$
declare
  v_def text;
  v_new text;
  v_old text;
  v_replacement text;
begin
  -- 1. The account may record when its school was picked.
  select pg_get_functiondef(p.oid) into v_def
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public' and p.proname = 'exchange_patch_account_profile';
  if v_def is null then
    raise exception 'exchange_patch_account_profile is missing';
  end if;
  if position('''home_university_changed_at''' in v_def) = 0 then
    v_old := $p$'home_university',
    'target_countries',$p$;
    v_replacement := $p$'home_university',
    'home_university_changed_at',
    'target_countries',$p$;
    v_new := replace(v_def, v_old, v_replacement);
    if v_new = v_def then
      raise exception 'exchange_patch_account_profile: allowed field list not found';
    end if;
    execute v_new;
  end if;

  -- 2. The school shown on a post is the verified one, else the picked one.
  select pg_get_functiondef(p.oid) into v_def
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public' and p.proname = 'exchange_community_display_name';
  if v_def is null then
    raise exception 'exchange_community_display_name is missing';
  end if;
  if position('''home_university''' in v_def) = 0 then
    v_old := $p$  v_school text := nullif(btrim(p_profile ->> 'verified_university'), '');$p$;
    v_replacement := $p$  v_school text := coalesce(
    nullif(btrim(p_profile ->> 'verified_university'), ''),
    nullif(nullif(btrim(p_profile ->> 'home_university'), ''), '尚未選擇')
  );$p$;
    v_new := replace(v_def, v_old, v_replacement);
    if v_new = v_def then
      raise exception 'exchange_community_display_name: school declaration not found';
    end if;
    v_def := v_new;
    v_old := $p$  if p_identity_mode = 'verified_school' and v_student_verified and v_school is not null then$p$;
    v_replacement := $p$  if p_identity_mode = 'verified_school' and v_school is not null then$p$;
    v_new := replace(v_def, v_old, v_replacement);
    if v_new = v_def then
      raise exception 'exchange_community_display_name: school branch not found';
    end if;
    execute v_new;
  end if;

  -- 3. Questions, answers, experiences and chat need a school, not a verified student.
  select pg_get_functiondef(p.oid) into v_def
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public' and p.proname = 'exchange_commit_public_community_content';
  if v_def is null then
    raise exception 'exchange_commit_public_community_content is missing';
  end if;
  if position('v_account.profile ->> ''home_university''' in v_def) = 0 then
    v_old := $p$  v_student_verified := coalesce(
    v_account.profile -> 'student_status_verified' = 'true'::jsonb,
    false
  );
  v_verified_school_key := public.exchange_normalize_community_school(
    coalesce(v_account.profile ->> 'verified_university', '')
  );$p$;
    v_replacement := $p$  v_verified_school_key := public.exchange_normalize_community_school(
    coalesce(
      nullif(btrim(v_account.profile ->> 'verified_university'), ''),
      nullif(nullif(btrim(v_account.profile ->> 'home_university'), ''), '尚未選擇'),
      ''
    )
  );
  v_student_verified := coalesce(
    v_account.profile -> 'student_status_verified' = 'true'::jsonb,
    false
  ) or coalesce(v_verified_school_key, '') <> '';$p$;
    v_new := replace(v_def, v_old, v_replacement);
    if v_new = v_def then
      raise exception 'exchange_commit_public_community_content: verified-student assignments not found';
    end if;
    execute v_new;
  end if;

  -- 4. Reporting a wrong application rule needs a school too.
  select pg_get_functiondef(p.oid) into v_def
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public' and p.proname = 'exchange_submit_application_workflow_issue_report';
  if v_def is null then
    raise exception 'exchange_submit_application_workflow_issue_report is missing';
  end if;
  if position('''home_university''' in v_def) = 0 then
    v_old := $p$  if v_account.profile -> 'student_status_verified' is distinct from 'true'::jsonb
     or nullif(btrim(v_account.profile ->> 'verified_university'), '') is null then$p$;
    v_replacement := $p$  if coalesce(
       nullif(btrim(v_account.profile ->> 'verified_university'), ''),
       nullif(nullif(btrim(v_account.profile ->> 'home_university'), ''), '尚未選擇')
     ) is null then$p$;
    v_new := replace(v_def, v_old, v_replacement);
    if v_new = v_def then
      raise exception 'exchange_submit_application_workflow_issue_report: verification check not found';
    end if;
    execute v_new;
  end if;
end
$migration$;
