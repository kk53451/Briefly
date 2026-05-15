-- 본문에서 추출한 고해상도 대표 이미지 컬럼 추가.
--   images       : 목록 페이지 220×150 썸네일 (작은 카드용, 기존 유지)
--   hero_image   : og:image 또는 본문 첫 사진 (리드 스토리/상세 화면용, 신규)

alter table public.news_cards
    add column if not exists hero_image text;

comment on column public.news_cards.hero_image is
    '본문에서 추출한 고해상도 대표 이미지 (og:image 우선, 없으면 본문 첫 사진). 리드 스토리/상세 화면용. images 컬럼은 목록 페이지 220x150 썸네일.';
