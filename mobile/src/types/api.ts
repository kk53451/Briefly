/**
 * TypeScript type definitions for Briefly API
 * Based on backend FastAPI models
 */

// User types
export interface UserProfile {
  user_id: string;
  nickname: string;
  profile_image?: string;
  interests: string[]; // Korean category names
  onboarding_completed: boolean;
  default_length?: number;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  user_id: string;
  nickname: string;
}

export interface OnboardingStatusResponse {
  onboarded: boolean;
}

// News types
export interface NewsItem {
  news_id: string;
  title: string;
  category: string; // English name (e.g., "politics")
  category_date: string; // Format: "{category}#{date}"
  provider: string; // News provider/publisher
  byline?: string; // Author/byline
  published_at: string;
  collected_at: string;
  images?: string; // Backend stores single image URL as "images" field
  provider_link_page?: string; // Original news URL
  content?: string; // Full article content
  hilight?: string; // Highlighted text from BigKinds
  rank?: number;
}

export interface NewsDetail extends NewsItem {
  content: string;
}

export interface TodayNewsResponse {
  [category: string]: NewsItem[];
}

export interface HomeNewsResponse {
  [provider: string]: NewsItem[];
}

// Podcast/Frequency types
export interface FrequencyItem {
  frequency_id: string;
  category: string;
  script: string;
  audio_url: string;
  date: string;
  created_at: string;
  duration?: number;
}

// Bookmark types
export interface BookmarkItem {
  news_id: string;
  bookmarked_at: string;
}

// Category types
export interface CategoriesResponse {
  categories: string[];
}

export interface UserCategoriesResponse {
  interests: string[];
}

// API error types
export interface ApiError {
  detail: string;
}

// Request types
export interface LoginRequest {
  code: string;
}

export interface UpdateProfileRequest {
  nickname?: string;
  default_length?: number;
  profile_image?: string;
}

export interface UpdateCategoriesRequest {
  interests: string[];
}

export interface BookmarkRequest {
  news_id: string;
}

// Extended news item with category name for UI display
export interface RankedNewsItem extends NewsItem {
  categoryName: string; // Korean category name for display
}

// Headlines types (오늘의 브리핑)
export interface HeadlineNewsInfo {
  news_id: string;
  title: string;
  images?: string;
  provider: string;
  provider_link_page?: string;
  published_at: string;
}

export interface HeadlineItem {
  headline_id: string;
  title: string;           // GPT 생성 헤드라인
  summary: string;         // GPT 생성 요약 (~요, ~해요 체)
  cluster_size: number;    // 클러스터 크기 (관련 기사 수)
  representative_news_id: string;
  news_ids?: string[];     // 클러스터 내 기사 ID 목록
  category?: string;       // 영문 카테고리
  category_ko?: string;    // 한글 카테고리
  news?: HeadlineNewsInfo; // 대표 기사 상세 정보
}

export interface HeadlinesResponse {
  date: string;
  category: string;        // "all" | "politics" | ...
  headlines: HeadlineItem[];
}
