-- Cleanup synthetic demo change-sets and inbound TEEP rows from exchange_maint_* tables.
-- Safe, idempotent, target-scoped migration for self-hosted PostgreSQL.
-- Rollback: Re-run generate_shadow_sync_sql(store) or restore from pre-migration snapshot if demo fixtures are needed in staging.

delete from public.exchange_maint_change_items
where change_set_id in ('cs_ntu_116_quota_and_deadline', 'cs_ntu_year_conflict_blocked');

delete from public.exchange_maint_change_sets
where id in ('cs_ntu_116_quota_and_deadline', 'cs_ntu_year_conflict_blocked');

delete from public.exchange_maint_offerings
where home_id = 'cgu'
  and host_id in (
    select id
    from public.exchange_maint_institutions
    where country_code = '來臺蹲點實習計畫 TEEP'
  );

delete from public.exchange_maint_institutions
where country_code = '來臺蹲點實習計畫 TEEP'
  and not exists (
    select 1
    from public.exchange_maint_offerings o
    where o.host_id = public.exchange_maint_institutions.id
  );
