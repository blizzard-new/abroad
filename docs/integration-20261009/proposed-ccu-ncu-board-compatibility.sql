-- PROPOSAL ONLY. NOT a committed application migration; NOT run on production.
-- Requires explicit coordination of DB-before-code release for PR #3/#4.
-- Extend only the existing short-ID allowlist; preserve function signature,
-- owner, ACL, security mode, search_path, verified-email and mutation gates.
do $migration$
declare
  v_function regprocedure := to_regprocedure('public.exchange_commit_public_community_content(text,text,text,text,text,text,jsonb)');
  v_def text;
  v_anchor text := $p$           or (p_payload ->> 'board_id' = 'ntu' and v_required_school_key = '國立臺灣大學')$p$;
  v_ccu text := $p$           or (p_payload ->> 'board_id' = 'ccu' and v_required_school_key = '國立中正大學')$p$;
  v_ncu text := $p$           or (p_payload ->> 'board_id' = 'ncu' and v_required_school_key = '國立中央大學')$p$;
begin
  if v_function is null then raise exception 'school-board function missing'; end if;
  v_def := pg_get_functiondef(v_function);
  if position(v_anchor in v_def) = 0 or position($p$coalesce(p_payload ->> 'board_id', '') ~ '^university:'$p$ in v_def) = 0 then
    raise exception 'expected current school-board allowlist missing';
  end if;
  if position(v_ccu in v_def) = 0 then v_def := replace(v_def, v_anchor, v_anchor || E'\n' || v_ccu); end if;
  if position(v_ncu in v_def) = 0 then v_def := replace(v_def, v_anchor, v_anchor || E'\n' || v_ncu); end if;
  execute v_def;
end
$migration$;
