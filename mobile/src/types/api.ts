export interface UserProfile {
  user_id: string;
  nickname: string;
  email?: string;
  profile_image?: string;
  interests: string[];
  created_at: string;
  onboarding_completed: boolean;
}

export interface NewsItem {
  news_id: string;
  title: string;
  summary: string;
  category: string;
  published_date: string;
  source: string;
  url: string;
  image_url?: string;
  is_bookmarked: boolean;
  view_count: number;
}

export interface NewsDetail extends NewsItem {
  content: string;
  tags?: string[];
}

export interface FrequencyItem {
  frequency_id: string;
  category: string;
  date: string;
  script: string;
  audio_url: string;
  duration: number;
  created_at: string;
}

export interface TodayNewsResponse {
  categories: {
    [key: string]: NewsItem[];
  };
  total_count: number;
}

export interface UserCategoriesResponse {
  interests: string[];
}

export interface CategoriesResponse {
  categories: Array<{
    id: string;
    name: string;
    name_en: string;
    description: string;
  }>;
}

export interface OnboardingStatusResponse {
  onboarding_completed: boolean;
}

export interface ApiError {
  detail: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
}
