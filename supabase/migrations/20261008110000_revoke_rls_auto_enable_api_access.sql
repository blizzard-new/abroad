-- rls_auto_enable() is the body of the `ensure_rls` event trigger: it turns row level security on for every new table
-- in public. An event trigger does not need anybody to be allowed to EXECUTE its function, but the default grants let
-- the browser roles (anon, authenticated) call it through /rest/v1/rpc/rls_auto_enable, which Supabase's security
-- advisor flags. Take that away; the trigger itself, owned by postgres, keeps working.
-- Guarded, so a project that does not have the function (it comes with the Supabase "auto RLS" setting) is not an error.

do $$
begin
  if to_regprocedure('public.rls_auto_enable()') is not null then
    revoke execute on function public.rls_auto_enable() from public, anon, authenticated;
  end if;
end
$$;
