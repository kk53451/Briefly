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
