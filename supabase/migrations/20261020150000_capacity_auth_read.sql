-- A private request previously made three HTTP round trips through PostgREST
-- before doing useful work: session, account, then workspaces.  Authenticate
-- and take one consistent account snapshot in a single indexed database read.

create or replace function public.exchange_authenticate_account(
  p_token_hash text
) returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
  v_result jsonb;
begin
  if p_token_hash is null or p_token_hash !~ '^[0-9a-f]{64}$' then
    return jsonb_build_object('status', 'invalid');
  end if;

  select jsonb_build_object(
    'status', 'valid',
    'session', jsonb_build_object(
      'id', session.id,
      'account_id', session.account_id,
      'token_hash', session.token_hash,
      'expires_at', session.expires_at,
      'created_at', session.created_at
    ),
    'account', jsonb_build_object(
      'id', account.id,
      'email', account.email,
      'profile', account.profile,
      'community_suspended_until', account.community_suspended_until,
      'created_at', account.created_at,
      'updated_at', account.updated_at,
      'workspaces', coalesce(
        (
          select jsonb_agg(
            jsonb_build_object(
              'workspace', workspace.workspace,
              'revision', workspace.revision
            )
            order by workspace.updated_at asc
          )
          from public.exchange_account_workspaces workspace
          where workspace.account_id = account.id
        ),
        '[]'::jsonb
      )
    )
  )
  into v_result
  from public.exchange_account_sessions session
  join public.exchange_accounts account on account.id = session.account_id
  where session.token_hash = p_token_hash
    and session.expires_at > statement_timestamp()
  limit 1;

  return coalesce(v_result, jsonb_build_object('status', 'invalid'));
end;
$$;

revoke all on function public.exchange_authenticate_account(text)
  from public, anon, authenticated;
grant execute on function public.exchange_authenticate_account(text)
  to service_role;
