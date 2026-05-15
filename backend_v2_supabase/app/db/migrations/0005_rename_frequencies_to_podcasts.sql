-- 2026-04-19 통합 브리핑 리워크 반영.
-- frequencies 테이블을 podcasts 로 rename 하고, 통합 브리핑 이후 dead column 이
-- 된 category 를 제거합니다.
--
-- 배경:
--   이전: frequencies UNIQUE(category, date, slot) — 카테고리별 개별 팟캐스트용
--   이후: podcasts    UNIQUE(date, slot)            — 하루 2회(AM/PM) 통합 브리핑
--
-- 원격 DB 에는 이 파일 내용이 Supabase migration
-- `20260419030244_rename_frequencies_to_podcasts_drop_category` 로 이미 적용되었음.
-- 이 파일은 로컬 재구성·추후 참조용.

-- 1. 기존 UNIQUE 제약 제거 (category 포함)
ALTER TABLE public.frequencies
  DROP CONSTRAINT frequencies_category_date_slot_key;

-- 2. category 컬럼 제거
ALTER TABLE public.frequencies
  DROP COLUMN category;

-- 3. 비UNIQUE 인덱스 제거 (새 UNIQUE 제약이 대체)
DROP INDEX IF EXISTS public.frequencies_date_slot_idx;

-- 4. 테이블 rename
ALTER TABLE public.frequencies RENAME TO podcasts;

-- 5. 제약 이름 통일
ALTER TABLE public.podcasts
  RENAME CONSTRAINT frequencies_pkey TO podcasts_pkey;

ALTER TABLE public.podcasts
  RENAME CONSTRAINT frequencies_slot_check TO podcasts_slot_check;

-- 6. 새 UNIQUE 제약 (date, slot)
ALTER TABLE public.podcasts
  ADD CONSTRAINT podcasts_date_slot_key UNIQUE (date, slot);

-- 7. 정책 이름 rename
ALTER POLICY "frequencies: anon+auth can read"
  ON public.podcasts
  RENAME TO "podcasts: anon+auth can read";
