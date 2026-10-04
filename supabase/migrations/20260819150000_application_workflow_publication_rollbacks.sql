alter table public.application_workflow_revisions
  add column if not exists publication_action text not null default 'standard',
  add column if not exists rolled_back_from_revision_id text,
  add column if not exists restored_revision_id text;

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'application_workflow_revisions_publication_action_check'
      and conrelid = 'public.application_workflow_revisions'::regclass
  ) then
    alter table public.application_workflow_revisions
      add constraint application_workflow_revisions_publication_action_check
      check (
        (publication_action = 'standard'
          and rolled_back_from_revision_id is null
          and restored_revision_id is null)
        or
        (publication_action = 'rollback'
          and rolled_back_from_revision_id is not null
          and restored_revision_id is not null
          and rolled_back_from_revision_id <> restored_revision_id)
      );
  end if;
end
$$;

create index if not exists application_workflow_revisions_rollback_chain_idx
  on public.application_workflow_revisions (
    workflow_key,
    rolled_back_from_revision_id,
    restored_revision_id
  )
  where publication_action = 'rollback';

comment on column public.application_workflow_revisions.publication_action is
  'Standard publication or append-only rollback publication created by FastAPI.';

comment on column public.application_workflow_revisions.rolled_back_from_revision_id is
  'For rollback publications, the exact current revision that was withdrawn.';

comment on column public.application_workflow_revisions.restored_revision_id is
  'For rollback publications, the previously dual-reviewed revision restored as a new version.';

-- Existing RLS and backend-only service-role grants remain unchanged. Web and
-- future Flutter clients can only reach this history through protected FastAPI.
