-- School-board policy selected 2026-10-09: all verified-email members may
-- read/write across schools. Existing 20261003100000 already implements the
-- write gate. Patch only the missing TKU mapping in the deployed function.
-- Preserve later thread, school-choice, lock, receipt and rate-limit changes.
-- Verified student bylines require actual server verification, not a home pick.
-- No ownership, grants, RLS, production deployment or existing data changes.

create or replace function public.exchange_community_display_name(
  p_profile jsonb,
  p_identity_mode text,
  p_content_type text
) returns text
language plpgsql
stable
set search_path = public, pg_temp
as $$
declare
  v_school text := nullif(btrim(p_profile ->> 'verified_university'), '');
  v_department text := nullif(btrim(p_profile ->> 'verified_department'), '');
  v_real_name text := nullif(btrim(p_profile ->> 'display_name'), '');
  v_student_verified boolean := coalesce(
    p_profile -> 'student_status_verified' = 'true'::jsonb,
    false
  );
begin
  if p_identity_mode = 'anonymous' then
    return '匿名學生';
  end if;

  if p_identity_mode = 'real_name' then
    return v_real_name;
  end if;

  if p_identity_mode = 'verified_school' and v_student_verified and v_school is not null then
    return v_school || '學生';
  end if;

  if p_identity_mode = 'verified_department'
     and v_student_verified
     and v_school is not null
     and v_department is not null then
    return v_school || ' ' || v_department || '學生';
  end if;

  return null;
end;
$$;

do $migration$
declare
  v_function regprocedure := to_regprocedure(
    'public.exchange_commit_public_community_content(text,text,text,text,text,text,jsonb)'
  );
  v_def text;
  v_new text;
  v_old text := $p$           or (p_payload ->> 'board_id' = 'ntu' and v_required_school_key = '國立臺灣大學')$p$;
  v_tku text := $p$           or (p_payload ->> 'board_id' = 'tku' and v_required_school_key = '淡江大學')$p$;
begin
  if v_function is null then
    raise exception 'exchange_commit_public_community_content is missing';
  end if;
  v_def := pg_get_functiondef(v_function);
  if position(v_tku in v_def) > 0 then
    return;
  end if;
  if position(v_old in v_def) = 0
     or position($p$coalesce(p_payload ->> 'board_id', '') ~ '^university:'$p$ in v_def) = 0 then
    raise exception 'exchange_commit_public_community_content: expected school-board allowlist not found';
  end if;
  v_new := replace(v_def, v_old, v_old || E'\n' || v_tku);
  execute v_new;
end
$migration$;
