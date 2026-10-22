-- 2026-04-19 에피소드 오디오 길이(초) 컬럼 추가.
--
-- 클라이언트(모바일 에피소드 리스트)가 "12:40" 같은 길이 표시를 하려면 DB 에 재생
-- 길이가 필요. NotebookLM 이 반환한 MP3 를 백엔드에서 mutagen 으로 헤더 probe 해
-- 초 단위 정수로 저장합니다.
--
-- nullable — probe 실패 시 NULL. 모바일은 NULL 이면 just_audio duration 으로 fallback.
--
-- 원격 DB 에는 Supabase migration `20260419??????_add_podcast_duration_sec` 로 이미
-- 적용됨.

ALTER TABLE public.podcasts
  ADD COLUMN duration_sec integer;
