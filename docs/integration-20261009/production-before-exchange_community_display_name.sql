CREATE OR REPLACE FUNCTION public.exchange_community_display_name(p_profile jsonb, p_identity_mode text, p_content_type text)
 RETURNS text
 LANGUAGE plpgsql
 STABLE
 SET search_path TO 'public', 'pg_temp'
AS $function$
declare
  v_school text := coalesce(
    nullif(btrim(p_profile ->> 'verified_university'), ''),
    nullif(nullif(btrim(p_profile ->> 'home_university'), ''), '尚未選擇')
  );
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

  if p_identity_mode = 'verified_school' and v_school is not null then
    return v_school || '學生';
  end if;

  if p_identity_mode = 'verified_department'
     and v_student_verified
     and v_school is not null
     and v_department is not null then
    return v_school || ' ' || v_department;
  end if;

  return null;
end;
$function$
