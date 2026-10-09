-- Match the existing Python registry alias key (NFKC, case folding, punctuation removal).
-- Only server-verified student bylines use this mapping; unknown schools stay unverified.
-- Keep the formatter signature, ownership, ACL/RLS and all mutation functions unchanged.

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
  v_school := case regexp_replace(lower(normalize(coalesce(v_school, ''), NFKC)), '[^0-9a-z一-鿿]+', '', 'g')
    when 'cgu' then '長庚大學'
    when 'changgunguniversity' then '長庚大學'
    when '長庚' then '長庚大學'
    when '長庚大學' then '長庚大學'
    when 'nationaltaipeiuniversity' then '國立臺北大學'
    when 'ntpu' then '國立臺北大學'
    when '北大' then '國立臺北大學'
    when '台北大學' then '國立臺北大學'
    when '國立臺北大學' then '國立臺北大學'
    when '臺北大學' then '國立臺北大學'
    when 'nationaltaiwanuniversity' then '國立臺灣大學'
    when 'ntu' then '國立臺灣大學'
    when '台大' then '國立臺灣大學'
    when '台灣大學' then '國立臺灣大學'
    when '國立台灣大學' then '國立臺灣大學'
    when '國立臺灣大學' then '國立臺灣大學'
    when '臺大' then '國立臺灣大學'
    when '臺灣大學' then '國立臺灣大學'
    when 'tamkanguniversity' then '淡江大學'
    when 'tku' then '淡江大學'
    when '淡大' then '淡江大學'
    when '淡江' then '淡江大學'
    when '淡江大學' then '淡江大學'
    else null
  end;

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
