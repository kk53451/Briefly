-- news_cards 에 토픽 키워드 컬럼 추가.
-- rank_topics() 가 카테고리당 20 토픽 모두에 키워드를 추출하지만 지금은
-- headlines.items jsonb 안의 상위 5개만 살아남는다. 토픽 단위 검색·필터링을
-- 위해 모든 카드(20)에 키워드를 보존한다.

alter table public.news_cards
  add column if not exists keywords text[] not null default '{}'::text[];

comment on column public.news_cards.keywords is
  'extract_topic_keywords() 결과의 평탄 문자열 배열. rank_topics 가 산출한 토픽 키워드(top 5).';

-- 토픽 키워드 검색 가속 (text[] 전용 GIN).
create index if not exists news_cards_keywords_gin_idx
  on public.news_cards using gin (keywords);
