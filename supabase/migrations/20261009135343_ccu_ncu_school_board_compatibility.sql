-- Extend only the existing short-ID allowlist; preserve function signature,
-- owner, ACL, security mode, search_path, verified-email and mutation gates.
do $migration$
declare
  v_function regprocedure := to_regprocedure('public.exchange_commit_public_community_content(text,text,text,text,text,text,jsonb)');
  v_def text;
  v_normalized_def text;
  v_tku text := $p$           or (p_payload ->> 'board_id' = 'tku' and v_required_school_key = '淡江大學')$p$;
  v_metadata jsonb;
  v_after_metadata jsonb;
  v_anchor text := $p$           or (p_payload ->> 'board_id' = 'ntu' and v_required_school_key = '國立臺灣大學')$p$;
  v_ccu text := $p$           or (p_payload ->> 'board_id' = 'ccu' and v_required_school_key = '國立中正大學')$p$;
  v_ncu text := $p$           or (p_payload ->> 'board_id' = 'ncu' and v_required_school_key = '國立中央大學')$p$;
begin
  if v_function is null then raise exception 'school-board function missing'; end if;
  v_def := pg_get_functiondef(v_function);
  -- Fresh installs apply TKU's earlier timestamp first; deployed rollout applied this first.
  -- Ignore only that exact reviewed TKU mapping when comparing the guarded definitions.
  v_normalized_def := replace(v_def, E'\n' || v_tku, '');
  if md5(v_normalized_def) = 'b032beac1990513b576f388328720999' then return; end if;
  if md5(v_normalized_def) <> 'b81840819d91b81f3557964da088ea3f' then
    raise exception 'unexpected forum function definition; re-review required';
  end if;
  select jsonb_build_array(proowner, proacl, prosecdef, proconfig)
    into v_metadata from pg_proc where oid = v_function;
  if position(v_anchor in v_def) = 0 or position($p$coalesce(p_payload ->> 'board_id', '') ~ '^university:'$p$ in v_def) = 0 then
    raise exception 'expected current school-board allowlist missing';
  end if;
  if position(v_ccu in v_def) = 0 then v_def := replace(v_def, v_anchor, v_anchor || E'\n' || v_ccu); end if;
  if position(v_ncu in v_def) = 0 then v_def := replace(v_def, v_anchor, v_anchor || E'\n' || v_ncu); end if;
  if md5(replace(v_def, E'\n' || v_tku, '')) <> 'b032beac1990513b576f388328720999' then
    raise exception 'unexpected rewritten forum function definition';
  end if;
  execute v_def;
  select jsonb_build_array(proowner, proacl, prosecdef, proconfig)
    into v_after_metadata from pg_proc where oid = v_function;
  if v_after_metadata is distinct from v_metadata then
    raise exception 'forum function security metadata changed';
  end if;
end
$migration$;
