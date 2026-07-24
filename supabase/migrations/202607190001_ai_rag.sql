create schema if not exists extensions;
create extension if not exists vector with schema extensions;

create table if not exists public.universities (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  country text,
  official_url text,
  last_checked timestamptz
);

create table if not exists public.partner_universities (
  id uuid primary key default gen_random_uuid(),
  home_university_id uuid not null references public.universities(id) on delete cascade,
  partner_university_id uuid not null references public.universities(id) on delete cascade,
  program_type text,
  degree_levels text,
  colleges text,
  source_url text not null,
  last_checked timestamptz,
  unique (home_university_id, partner_university_id, program_type)
);

create table if not exists public.programs (
  id uuid primary key default gen_random_uuid(),
  university_id uuid not null references public.universities(id) on delete cascade,
  program_type text not null,
  academic_year text,
  semester text,
  source_url text not null,
  last_checked timestamptz
);

create table if not exists public.eligibility_rules (
  id uuid primary key default gen_random_uuid(),
  program_id uuid not null references public.programs(id) on delete cascade,
  rule_type text not null,
  rule_value jsonb not null default '{}'::jsonb,
  source_url text not null,
  last_checked timestamptz
);

create table if not exists public.deadlines (
  id uuid primary key default gen_random_uuid(),
  program_id uuid not null references public.programs(id) on delete cascade,
  label text not null,
  starts_at date,
  ends_at date,
  source_url text not null,
  last_checked timestamptz
);

create table if not exists public.required_documents (
  id uuid primary key default gen_random_uuid(),
  program_id uuid not null references public.programs(id) on delete cascade,
  name text not null,
  details text,
  source_url text not null,
  last_checked timestamptz
);

create table if not exists public.scholarships (
  id uuid primary key default gen_random_uuid(),
  university_id uuid not null references public.universities(id) on delete cascade,
  name text not null,
  details jsonb not null default '{}'::jsonb,
  source_url text not null,
  last_checked timestamptz
);

create table if not exists public.source_pages (
  id uuid primary key default gen_random_uuid(),
  school_name text not null,
  source_url text not null unique,
  title text not null,
  category text not null,
  published_at text,
  crawled_at timestamptz not null,
  content_hash text not null,
  summary text,
  body text not null
);

create table if not exists public.structured_announcements (
  id uuid primary key default gen_random_uuid(),
  source_url text not null unique,
  school_name text not null,
  category text not null,
  extracted_data jsonb not null,
  extraction_method text not null check (extraction_method in ('rules', 'ai')),
  needs_review boolean not null default true,
  content_hash text not null,
  last_checked timestamptz not null
);

create table if not exists public.document_chunks (
  id text primary key,
  school_name text not null,
  source_url text not null,
  source_title text not null,
  section text not null,
  text text not null,
  published_at text,
  last_checked timestamptz not null,
  category text not null,
  content_hash text not null,
  embedding extensions.vector(1536),
  embedding_model text
);

create index if not exists document_chunks_source_url_idx
  on public.document_chunks (source_url);

create index if not exists document_chunks_embedding_hnsw_idx
  on public.document_chunks
  using hnsw (embedding extensions.vector_cosine_ops);

create or replace function public.match_document_chunks(
  query_embedding extensions.vector(1536),
  match_threshold float,
  match_count int,
  filter_school text default null
)
returns table (
  id text,
  school_name text,
  source_url text,
  source_title text,
  section text,
  text text,
  published_at text,
  last_checked timestamptz,
  category text,
  content_hash text,
  embedding_model text,
  similarity float
)
language sql
stable
as $$
  select
    chunks.id,
    chunks.school_name,
    chunks.source_url,
    chunks.source_title,
    chunks.section,
    chunks.text,
    chunks.published_at,
    chunks.last_checked,
    chunks.category,
    chunks.content_hash,
    chunks.embedding_model,
    1 - (chunks.embedding <=> query_embedding) as similarity
  from public.document_chunks as chunks
  where chunks.embedding is not null
    and (filter_school is null or chunks.school_name = filter_school)
    and 1 - (chunks.embedding <=> query_embedding) >= match_threshold
  order by chunks.embedding <=> query_embedding
  limit greatest(match_count, 1);
$$;

alter table public.universities enable row level security;
alter table public.partner_universities enable row level security;
alter table public.programs enable row level security;
alter table public.eligibility_rules enable row level security;
alter table public.deadlines enable row level security;
alter table public.required_documents enable row level security;
alter table public.scholarships enable row level security;
alter table public.source_pages enable row level security;
alter table public.structured_announcements enable row level security;
alter table public.document_chunks enable row level security;

-- The app accesses these tables through FastAPI with the service-role key.
-- Do not expose SUPABASE_SERVICE_ROLE_KEY to the web or Flutter clients.
