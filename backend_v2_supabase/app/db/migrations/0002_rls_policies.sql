-- Briefly v3 RLS policies
-- Public read for content tables (anon allowed); user-scoped for profiles/bookmarks
-- Pipeline writes via service_role (bypasses RLS by default)

-- ──────────────────────────────────────────────
-- Public-read content tables
-- ──────────────────────────────────────────────
alter table public.news_cards   enable row level security;
alter table public.frequencies  enable row level security;
alter table public.headlines    enable row level security;

create policy "news_cards: anon+auth can read"
    on public.news_cards for select
    to anon, authenticated
    using (true);

create policy "frequencies: anon+auth can read"
    on public.frequencies for select
    to anon, authenticated
    using (true);

create policy "headlines: anon+auth can read"
    on public.headlines for select
    to anon, authenticated
    using (true);

-- write/update/delete는 정책 없음 → service_role만 가능

-- ──────────────────────────────────────────────
-- profiles: 본인만 SELECT/UPDATE
-- ──────────────────────────────────────────────
alter table public.profiles enable row level security;

create policy "profiles: own row select"
    on public.profiles for select
    to authenticated
    using (id = auth.uid());

create policy "profiles: own row update"
    on public.profiles for update
    to authenticated
    using (id = auth.uid())
    with check (id = auth.uid());

-- INSERT는 트리거(handle_new_user, security definer)로만 발생 — 정책 불필요

-- ──────────────────────────────────────────────
-- bookmarks: 본인 row 전체 CRUD
-- ──────────────────────────────────────────────
alter table public.bookmarks enable row level security;

create policy "bookmarks: own select"
    on public.bookmarks for select
    to authenticated
    using (user_id = auth.uid());

create policy "bookmarks: own insert"
    on public.bookmarks for insert
    to authenticated
    with check (user_id = auth.uid());

create policy "bookmarks: own delete"
    on public.bookmarks for delete
    to authenticated
    using (user_id = auth.uid());
