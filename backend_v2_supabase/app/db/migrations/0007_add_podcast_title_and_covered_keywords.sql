-- 2026-04-19 통합 브리핑 완성 — 에피소드 title + previous-topics dedup 메타.
--
-- title: Gemma4 헤드라인 top1 × 3분야 를 쉼표로 연결한 한 줄 요약
--        예) "추경 35조 합의, 서울 아파트 반등, 美·이란 협상 개시"
-- covered_keywords: 이 에피소드에 담긴 토픽들의 top 키워드 집합.
--                   다음 실행의 previous-topics dedup 에서 후보 토픽과 비교.
--                   형식: [["추경","35조","합의"], ["아파트","서울","반등"], ...]
--
-- 원격 DB 에는 Supabase migration
-- `20260419??????_add_podcast_title_and_covered_keywords` 로 이미 적용됨.

ALTER TABLE public.podcasts
  ADD COLUMN title text,
  ADD COLUMN covered_keywords jsonb NOT NULL DEFAULT '[]'::jsonb;

-- 최근 24시간 covered_keywords 조회용 index (dedup fetch 경로 가속).
CREATE INDEX podcasts_created_at_idx ON public.podcasts (created_at DESC);
