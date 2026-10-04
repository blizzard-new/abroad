create unique index if not exists application_workflow_revisions_workflow_id_uidx
  on public.application_workflow_revisions (workflow_key, id);

create unique index if not exists application_workflow_revisions_rollback_event_uidx
  on public.application_workflow_revisions (
    workflow_key,
    rolled_back_from_revision_id,
    restored_revision_id
  )
  where publication_action = 'rollback';

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'application_workflow_revisions_rolled_back_from_fk'
      and conrelid = 'public.application_workflow_revisions'::regclass
  ) then
    alter table public.application_workflow_revisions
      add constraint application_workflow_revisions_rolled_back_from_fk
      foreign key (workflow_key, rolled_back_from_revision_id)
      references public.application_workflow_revisions (workflow_key, id)
      on delete restrict;
  end if;

  if not exists (
    select 1
    from pg_constraint
    where conname = 'application_workflow_revisions_restored_revision_fk'
      and conrelid = 'public.application_workflow_revisions'::regclass
  ) then
    alter table public.application_workflow_revisions
      add constraint application_workflow_revisions_restored_revision_fk
      foreign key (workflow_key, restored_revision_id)
      references public.application_workflow_revisions (workflow_key, id)
      on delete restrict;
  end if;
end
$$;

-- The existing RLS/service-role boundary remains unchanged. These constraints
-- only strengthen the private, backend-managed publication ledger.
