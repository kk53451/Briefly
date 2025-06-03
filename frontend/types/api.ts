export interface NewsItem {
  news_id: string
  title: string
  title_ko?: string // 새로 추가
  summary: string
  summary_ko?: string // 새로 추가
  category: string
  publisher: string
  author?: string // 새로 추가
  published_at: string
  collected_at?: string
  image_url?: string
  thumbnail_url?: string
  content_url?: string // 새로 추가
  rank?: number
}

export interface NewsDetail extends NewsItem {
  content: string
}

export interface TodayNewsResponse {
  [category: string]: NewsItem[]
}

export interface UserProfile {
  user_id: string
  nickname: string
  profile_image?: string
  interests: string[]
  onboarding_completed: boolean
  default_length?: number
  created_at: string
}

export interface BookmarkItem {
  news_id: string
  bookmarked_at: string
}

export interface FrequencyItem {
  frequency_id: string
  category: string
  script: string
  audio_url: string
  date: string
  created_at: string
  duration?: number // 새로 추가
}

export interface UserCategoriesResponse {
  interests: string[]
}

export interface CategoriesResponse {
  categories: string[]
}

export interface OnboardingStatusResponse {
  onboarded: boolean
}

export interface AuthResponse {
  access_token: string
  user_id: string
  nickname: string
}

export interface ApiError {
  detail: string
}
