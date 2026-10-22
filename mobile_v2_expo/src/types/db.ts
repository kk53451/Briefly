/**
 * Supabase row types — mirrors backend_v2_supabase/app/db/migrations/0001_init_schema.sql.
 */

export type Slot = 'AM' | 'PM';

export interface NewsCard {
  news_id: string;
  category: string;
  date: string;               // YYYY-MM-DD
  slot: Slot;
  rank: number;
  cluster_size: number;
  title: string;
  images: string | null;
  provider_link_page: string | null;
  provider: string | null;
  byline: string | null;
  published_at: string | null;
  hilight: string | null;
  content: string | null;
  collected_at: string;
}

export interface HeadlineItem {
  topic_id: number;
  headline: string;
  summary: string;
  cluster_size: number;
  representative_news_id: string;
  representative_title: string;
  representative_image: string | null;
  representative_press: string;
  keywords: string[];
}

export interface HeadlineRow {
  id: string;
  category: string;
  date: string;
  slot: Slot;
  items: HeadlineItem[];
  headline_count: number;
  created_at: string;
}

/**
 * Comprehensive AM/PM integrated briefing podcast.
 * Schema: `podcasts` (UNIQUE date, slot) — post-rename of 2026-04-19.
 *
 * `title` = 에피소드 한 줄 헤드라인 요약. 예:
 *   "추경 35조 합의, 서울 아파트 반등, 美·이란 협상 개시"
 *   (backend 가 Gemma4 카테고리 top1 헤드라인 3개를 쉼표로 연결해서 생성)
 *
 * `duration_sec` = 백엔드가 mutagen 으로 MP3 헤더 probe 한 길이 (실패 시 NULL).
 *                  NULL 이면 모바일이 expo-av 로딩 후 player duration 으로 폴백.
 *
 * `covered_keywords` = backend 가 다음 실행의 previous-topics dedup 에 쓰는
 *                      메타데이터. 모바일에서 직접 쓸 일은 없지만 스키마 일관성 위해 노출.
 */
export interface PodcastRow {
  id: string;
  date: string;
  slot: Slot;
  script: string;
  title: string | null;
  audio_path: string | null;  // path inside briefly-audio bucket
  duration_sec: number | null;
  covered_keywords: string[][];
  created_at: string;
}

export interface Profile {
  id: string;
  nickname: string | null;
  profile_image: string | null;
  interests: string[];
  onboarding_completed: boolean;
  created_at: string;
}

export interface Bookmark {
  user_id: string;
  news_id: string;
  title: string;
  provider: string | null;
  images: string | null;
  provider_link_page: string | null;
  hilight: string | null;
  category: string | null;
  published_at: string | null;
  created_at: string;
}
