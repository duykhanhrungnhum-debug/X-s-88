-- Xoso88 initial Supabase/PostgreSQL schema
-- Data flow: FETCHED -> PARSED -> VALIDATED -> PUBLISHED

create extension if not exists pgcrypto;

create type public.lottery_region as enum ('north', 'central', 'south');
create type public.fetch_status as enum ('fetched', 'parsed', 'validated', 'published', 'failed');
create type public.validation_status as enum ('pending', 'valid', 'invalid');

create table public.lottery_provinces (
  id uuid primary key default gen_random_uuid(),
  code text not null unique,
  name text not null,
  region public.lottery_region not null,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.lottery_draws (
  id uuid primary key default gen_random_uuid(),
  province_id uuid not null references public.lottery_provinces(id),
  draw_date date not null,
  source_url text not null,
  fetched_at timestamptz not null default now(),
  validation_status public.validation_status not null default 'pending',
  published_at timestamptz,
  created_at timestamptz not null default now(),
  unique (province_id, draw_date)
);

create table public.lottery_results (
  id uuid primary key default gen_random_uuid(),
  draw_id uuid not null references public.lottery_draws(id) on delete cascade,
  prize_code text not null,
  prize_name text not null,
  numbers text[] not null,
  display_order smallint not null,
  created_at timestamptz not null default now(),
  unique (draw_id, prize_code)
);

create table public.source_fetches (
  id uuid primary key default gen_random_uuid(),
  source_name text not null,
  source_url text not null,
  fetched_at timestamptz not null default now(),
  http_status integer,
  status public.fetch_status not null,
  content_hash text,
  error_message text,
  created_at timestamptz not null default now()
);

create table public.validation_events (
  id uuid primary key default gen_random_uuid(),
  draw_id uuid references public.lottery_draws(id) on delete cascade,
  source_fetch_id uuid references public.source_fetches(id) on delete set null,
  status public.validation_status not null,
  reason text,
  checked_at timestamptz not null default now()
);

create index lottery_draws_date_idx on public.lottery_draws(draw_date desc);
create index lottery_draws_province_date_idx on public.lottery_draws(province_id, draw_date desc);
create index lottery_results_draw_order_idx on public.lottery_results(draw_id, display_order);
create index source_fetches_source_date_idx on public.source_fetches(source_name, fetched_at desc);
create index validation_events_draw_date_idx on public.validation_events(draw_id, checked_at desc);

-- Public website may read only published draws/results through the API layer.
alter table public.lottery_provinces enable row level security;
alter table public.lottery_draws enable row level security;
alter table public.lottery_results enable row level security;
alter table public.source_fetches enable row level security;
alter table public.validation_events enable row level security;

create policy "public can read active provinces"
on public.lottery_provinces for select
using (active = true);

create policy "public can read published draws"
on public.lottery_draws for select
using (validation_status = 'valid' and published_at is not null);

create policy "public can read results of published draws"
on public.lottery_results for select
using (
  exists (
    select 1 from public.lottery_draws d
    where d.id = lottery_results.draw_id
      and d.validation_status = 'valid'
      and d.published_at is not null
  )
);

-- No public INSERT/UPDATE/DELETE policies are intentionally created.
-- Writes are performed by the trusted backend/collector using a server-side key.

insert into public.lottery_provinces (code, name, region) values
  ('MB', 'Miền Bắc', 'north'),
  ('MT', 'Miền Trung', 'central'),
  ('MN', 'Miền Nam', 'south')
on conflict (code) do nothing;
