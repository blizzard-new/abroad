-- Permit the NTU board emitted by the application, paired with its canonical school.
-- Patch only this allowlist; keep deployed authentication, identity, school-choice,
-- moderation, rate-limit and transaction checks, function ownership and grants.
-- Stop on an unexpected deployed definition. Reapplying this migration is a no-op.

do $migration$
declare
  v_function regprocedure := to_regprocedure(
    'public.exchange_commit_public_community_content(text,text,text,text,text,text,jsonb)'
  );
  v_def text;
  v_new text;
  v_old text := $p$           or (p_payload ->> 'board_id' = 'ntpu' and v_required_school_key = '國立臺北大學')$p$;
  v_ntu text := $p$           or (p_payload ->> 'board_id' = 'ntu' and v_required_school_key = '國立臺灣大學')$p$;
begin
  if v_function is null then
    raise exception 'exchange_commit_public_community_content is missing';
  end if;
  v_def := pg_get_functiondef(v_function);
  if position(v_ntu in v_def) > 0 then
    return;
  end if;
  if position(v_old in v_def) = 0
     or position($p$coalesce(p_payload ->> 'board_id', '') ~ '^university:'$p$ in v_def) = 0 then
    raise exception 'exchange_commit_public_community_content: expected school-board allowlist not found';
  end if;
  v_new := replace(v_def, v_old, v_old || E'\n' || v_ntu);
  execute v_new;
end
$migration$;
