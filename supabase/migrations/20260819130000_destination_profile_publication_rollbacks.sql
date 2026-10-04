alter table public.destination_profile_promotion_events
    drop constraint if exists destination_profile_promotion_events_profile_key_source_profile_content_hash_key;

create index if not exists destination_profile_promotion_events_source_idx
    on public.destination_profile_promotion_events (
        profile_key,
        source_profile_content_hash,
        promoted_at desc
    );

create table if not exists public.destination_profile_rollback_events (
    id text primary key,
    profile_key text not null,
    rolled_back_from_event_id text not null unique,
    rolled_back_promotion_event_id text not null,
    restored_promotion_event_id text,
    rolled_back_by_id text not null,
    rolled_back_at timestamptz not null,
    event_payload jsonb not null
);

create index if not exists destination_profile_rollback_events_profile_idx
    on public.destination_profile_rollback_events (
        profile_key,
        rolled_back_at desc
    );

alter table public.destination_profile_rollback_events enable row level security;

revoke all on table public.destination_profile_rollback_events from anon, authenticated;
grant select, insert on table public.destination_profile_rollback_events to service_role;

comment on table public.destination_profile_rollback_events is
    'Append-only, backend-only restoration events for destination profile public snapshots.';
