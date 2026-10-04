-- First-party, anonymous product analytics. FastAPI is the only writer and reader (service role).
--
-- exchange_analytics_events     one row per browser or server event; no IP address, e-mail, name or
--                               account id is ever stored (visitor_id is a random browser-side id).
-- exchange_analytics_api_hourly request counts and latency buckets per endpoint and hour.
-- exchange_analytics_* views    daily summaries for looking at the data directly in the Supabase
--                               SQL editor; the admin dashboard computes the same numbers in Python.
--
-- RLS is on for both tables and the browser roles get nothing; views run as the caller
-- (security_invoker), so they cannot reach rows their caller cannot.

create table public.exchange_analytics_events (
  id text primary key check (char_length(id) between 8 and 64),
  occurred_at timestamptz not null,
  received_at timestamptz not null default now(),
  visitor_id text not null check (char_length(visitor_id) between 6 and 64),
  session_id text not null check (char_length(session_id) between 6 and 64),
  name text not null check (char_length(name) between 2 and 40),
  route text not null default '' check (char_length(route) <= 120),
  home_school text not null default '' check (char_length(home_school) <= 60),
  props jsonb not null default '{}'::jsonb check (jsonb_typeof(props) = 'object' and pg_column_size(props) <= 4096),
  device_class text not null default '',
  browser text not null default '',
  os text not null default '',
  country text not null default '' check (char_length(country) <= 2),
  language text not null default '',
  timezone text not null default '',
  viewport text not null default '',
  display_mode text not null default '',
  connection text not null default '',
  referrer_host text not null default '',
  utm_source text not null default '',
  utm_medium text not null default '',
  utm_campaign text not null default '',
  utm_term text not null default '',
  utm_content text not null default '',
  new_visitor boolean not null default false,
  signed_in boolean not null default false,
  school_basis text not null default '',
  is_bot boolean not null default false
);

create index exchange_analytics_events_time_idx on public.exchange_analytics_events (occurred_at desc);
create index exchange_analytics_events_name_idx on public.exchange_analytics_events (name, occurred_at desc);
create index exchange_analytics_events_visitor_idx on public.exchange_analytics_events (visitor_id, occurred_at);
create index exchange_analytics_events_session_idx on public.exchange_analytics_events (session_id, occurred_at);
create index exchange_analytics_events_human_idx on public.exchange_analytics_events (occurred_at desc) where not is_bot;

alter table public.exchange_analytics_events enable row level security;
alter table public.exchange_analytics_events force row level security;
revoke all on public.exchange_analytics_events from public, anon, authenticated;
grant select, insert on public.exchange_analytics_events to service_role;

create table public.exchange_analytics_api_hourly (
  bucket_hour timestamptz not null,
  route text not null check (char_length(route) between 1 and 120),
  method text not null check (char_length(method) between 1 and 10),
  status_class text not null check (status_class in ('1xx', '2xx', '3xx', '4xx', '5xx', 'other')),
  request_count bigint not null default 0 check (request_count >= 0),
  total_ms bigint not null default 0 check (total_ms >= 0),
  max_ms integer not null default 0 check (max_ms >= 0),
  le_100 bigint not null default 0,
  le_300 bigint not null default 0,
  le_1000 bigint not null default 0,
  le_3000 bigint not null default 0,
  gt_3000 bigint not null default 0,
  primary key (bucket_hour, route, method, status_class)
);

alter table public.exchange_analytics_api_hourly enable row level security;
alter table public.exchange_analytics_api_hourly force row level security;
revoke all on public.exchange_analytics_api_hourly from public, anon, authenticated;
grant select on public.exchange_analytics_api_hourly to service_role;

-- One round trip adds a whole batch of hourly counters; concurrent workers add rather than overwrite.
create function public.exchange_analytics_add_api_hourly(p_rows jsonb) returns void
language plpgsql security definer set search_path = '' as $$
begin
  if p_rows is null or jsonb_typeof(p_rows) <> 'array' then
    raise exception 'p_rows must be a json array' using errcode = '22023';
  end if;
  insert into public.exchange_analytics_api_hourly as target (
    bucket_hour, route, method, status_class, request_count, total_ms, max_ms,
    le_100, le_300, le_1000, le_3000, gt_3000
  )
  select
    (item ->> 'bucket_hour')::timestamptz, item ->> 'route', item ->> 'method', item ->> 'status_class',
    coalesce((item ->> 'request_count')::bigint, 0), coalesce((item ->> 'total_ms')::bigint, 0),
    coalesce((item ->> 'max_ms')::integer, 0), coalesce((item ->> 'le_100')::bigint, 0),
    coalesce((item ->> 'le_300')::bigint, 0), coalesce((item ->> 'le_1000')::bigint, 0),
    coalesce((item ->> 'le_3000')::bigint, 0), coalesce((item ->> 'gt_3000')::bigint, 0)
  from jsonb_array_elements(p_rows) as incoming(item)
  on conflict (bucket_hour, route, method, status_class) do update set
    request_count = target.request_count + excluded.request_count,
    total_ms = target.total_ms + excluded.total_ms,
    max_ms = greatest(target.max_ms, excluded.max_ms),
    le_100 = target.le_100 + excluded.le_100,
    le_300 = target.le_300 + excluded.le_300,
    le_1000 = target.le_1000 + excluded.le_1000,
    le_3000 = target.le_3000 + excluded.le_3000,
    gt_3000 = target.gt_3000 + excluded.gt_3000;
end;
$$;
revoke all on function public.exchange_analytics_add_api_hourly(jsonb) from public, anon, authenticated;
grant execute on function public.exchange_analytics_add_api_hourly(jsonb) to service_role;

-- Retention: the API calls this once a day with now() minus EXCHANGE_ANALYTICS_RETENTION_DAYS.
create function public.exchange_analytics_purge(p_before timestamptz) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  v_events bigint;
  v_hourly bigint;
begin
  if p_before is null or p_before > now() - interval '30 days' then
    raise exception 'refusing to purge data newer than 30 days' using errcode = '22023';
  end if;
  with removed as (
    delete from public.exchange_analytics_events where occurred_at < p_before returning 1
  ) select count(*) into v_events from removed;
  with removed as (
    delete from public.exchange_analytics_api_hourly where bucket_hour < p_before returning 1
  ) select count(*) into v_hourly from removed;
  return jsonb_build_object('events', v_events, 'api_hourly', v_hourly);
end;
$$;
revoke all on function public.exchange_analytics_purge(timestamptz) from public, anon, authenticated;
grant execute on function public.exchange_analytics_purge(timestamptz) to service_role;

-- Daily views (Asia/Taipei days, bots excluded, server-written rows excluded from visitor counts).
create view public.exchange_analytics_daily with (security_invoker = true) as
select
  (occurred_at at time zone 'Asia/Taipei')::date as day,
  count(distinct visitor_id) filter (where visitor_id <> 'server') as visitors,
  count(distinct session_id) filter (where session_id <> 'server') as sessions,
  count(*) filter (where name = 'page_view') as pageviews,
  count(*) filter (where name = 'school_open') as school_opens,
  count(*) filter (where name = 'favorite_toggle' and props ->> 'saved' = 'true') as favorites_added,
  count(*) filter (where name = 'account_created') as new_accounts,
  count(*) as events
from public.exchange_analytics_events
where not is_bot
group by 1;

create view public.exchange_analytics_routes_daily with (security_invoker = true) as
select
  (occurred_at at time zone 'Asia/Taipei')::date as day,
  route,
  count(*) as views,
  count(distinct visitor_id) as visitors
from public.exchange_analytics_events
where not is_bot and name = 'page_view'
group by 1, 2;

create view public.exchange_analytics_schools_daily with (security_invoker = true) as
select
  (occurred_at at time zone 'Asia/Taipei')::date as day,
  props ->> 'school' as school,
  home_school as viewed_from,
  count(*) filter (where name = 'school_open') as opens,
  count(*) filter (where name = 'favorite_toggle' and props ->> 'saved' = 'true') as favorites_added,
  count(*) filter (where name = 'outbound_click') as outbound_clicks,
  count(distinct visitor_id) as visitors
from public.exchange_analytics_events
where not is_bot
  and name in ('school_open', 'favorite_toggle', 'outbound_click')
  and coalesce(props ->> 'school', '') <> ''
group by 1, 2, 3;

create view public.exchange_analytics_search_terms_daily with (security_invoker = true) as
select
  (occurred_at at time zone 'Asia/Taipei')::date as day,
  props ->> 'q' as term,
  count(*) as searches,
  count(distinct visitor_id) as visitors,
  count(*) filter (where (props ->> 'results') = '0') as zero_results
from public.exchange_analytics_events
where not is_bot and name = 'search' and coalesce(props ->> 'q', '') <> ''
group by 1, 2;

create view public.exchange_analytics_traffic_daily with (security_invoker = true) as
select day, channel, count(*) as sessions
from (
  select
    (min(occurred_at) at time zone 'Asia/Taipei')::date as day,
    case
      when max(utm_medium) in ('cpc', 'ppc', 'paid', 'paidsocial', 'paid_social', 'display') then 'paid'
      when max(utm_source) <> '' or max(utm_medium) <> '' or max(utm_campaign) <> '' then 'campaign'
      when max(referrer_host) ~ '(google|bing|yahoo|duckduckgo|baidu|naver|ecosia|yandex)\.' then 'search'
      when max(referrer_host) ~ '(facebook|instagram|line\.me|lin\.ee|twitter|threads|dcard|ptt|reddit|youtube|linkedin|tiktok|t\.co)' then 'social'
      when max(referrer_host) <> '' then 'referral'
      when max(browser) like '%(in-app)' then 'social'
      else 'direct'
    end as channel
  from public.exchange_analytics_events
  where not is_bot and session_id <> 'server'
  group by session_id
) sessions
group by 1, 2;

create view public.exchange_analytics_api_daily with (security_invoker = true) as
select
  (bucket_hour at time zone 'Asia/Taipei')::date as day,
  route,
  sum(request_count) as requests,
  sum(request_count) filter (where status_class = '5xx') as errors_5xx,
  sum(request_count) filter (where status_class = '4xx') as errors_4xx,
  round(sum(total_ms)::numeric / nullif(sum(request_count), 0), 1) as avg_ms,
  max(max_ms) as max_ms,
  sum(le_3000 + gt_3000) as slow_requests
from public.exchange_analytics_api_hourly
group by 1, 2;

revoke all on public.exchange_analytics_daily, public.exchange_analytics_routes_daily,
  public.exchange_analytics_schools_daily, public.exchange_analytics_search_terms_daily,
  public.exchange_analytics_traffic_daily, public.exchange_analytics_api_daily
  from public, anon, authenticated;
grant select on public.exchange_analytics_daily, public.exchange_analytics_routes_daily,
  public.exchange_analytics_schools_daily, public.exchange_analytics_search_terms_daily,
  public.exchange_analytics_traffic_daily, public.exchange_analytics_api_daily
  to service_role;
