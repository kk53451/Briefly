-- Briefly v3 initial schema
-- Tables: news_cards, frequencies, headlines, profiles, bookmarks
-- See plans/aws-reflective-moth.md for design rationale

-- ──────────────────────────────────────────────
-- news_cards: 홈/투데이 탭 기사 (클러스터 대표)
-- ──────────────────────────────────────────────
create table public.news_cards (
    news_id            text primary key,
    category           text not null,
    date               date not null,
    slot               text not null check (slot in ('AM','PM')),
    rank               int  not null,
    cluster_size       int  not null,
    title              text not null,
    images             text,
    provider_link_page text,
    provider           text,
    byline             text,
    published_at       timestamptz,
    hilight            text,
    content            text,
    collected_at       timestamptz not null default now()
);

create index news_cards_category_date_rank_idx
    on public.news_cards (category, date, rank);

create index news_cards_date_slot_rank_idx
    on public.news_cards (date, slot, rank);

-- ──────────────────────────────────────────────
-- frequencies: 팟캐스트 대본 + 오디오 경로
-- ──────────────────────────────────────────────
create table public.frequencies (
    id          uuid primary key default gen_random_uuid(),
    category    text not null,
    date        date not null,
    slot        text not null check (slot in ('AM','PM')),
    script      text not null,
    audio_path  text,
    created_at  timestamptz not null default now(),
    unique (category, date, slot)
);

create index frequencies_date_slot_idx on public.frequencies (date, slot);

-- ──────────────────────────────────────────────
-- headlines: 오늘의 브리핑 (카테고리별 헤드라인 묶음)
-- ──────────────────────────────────────────────
create table public.headlines (
    id              uuid primary key default gen_random_uuid(),
    category        text not null,
    date            date not null,
    slot            text not null check (slot in ('AM','PM')),
    items           jsonb not null,
    headline_count  int   not null,
    created_at      timestamptz not null default now(),
    unique (category, date, slot)
);

create index headlines_date_slot_idx on public.headlines (date, slot);

-- ──────────────────────────────────────────────
-- profiles: auth.users 1:1 확장
-- ──────────────────────────────────────────────
create table public.profiles (
    id                    uuid primary key references auth.users(id) on delete cascade,
    nickname              text,
    profile_image         text,
    interests             text[] not null default '{}',
    onboarding_completed  boolean not null default false,
    created_at            timestamptz not null default now()
);

-- handle_new_user trigger: auth.users 생성 시 profiles row 자동 생성
-- raw_user_meta_data에서 provider별 nickname/avatar 추출
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
    meta jsonb := coalesce(new.raw_user_meta_data, '{}'::jsonb);
    derived_nickname text;
    derived_avatar text;
begin
    derived_nickname := coalesce(
        meta->>'name',
        meta->>'full_name',
        meta->>'nickname',
        meta->>'user_name',
        split_part(coalesce(new.email, ''), '@', 1),
        '사용자'
    );

    derived_avatar := coalesce(
        meta->>'avatar_url',
        meta->>'picture',
        meta->>'profile_image'
    );

    insert into public.profiles (id, nickname, profile_image)
    values (new.id, derived_nickname, derived_avatar)
    on conflict (id) do nothing;

    return new;
end;
$$;

create trigger on_auth_user_created
    after insert on auth.users
    for each row execute function public.handle_new_user();

-- ──────────────────────────────────────────────
-- bookmarks: 스냅샷 비정규화 (news_cards FK 없음)
-- ──────────────────────────────────────────────
create table public.bookmarks (
    user_id            uuid not null references auth.users(id) on delete cascade,
    news_id            text not null,
    title              text not null,
    provider           text,
    images             text,
    provider_link_page text,
    hilight            text,
    category           text,
    published_at       timestamptz,
    created_at         timestamptz not null default now(),
    primary key (user_id, news_id)
);

create index bookmarks_user_created_idx
    on public.bookmarks (user_id, created_at desc);
