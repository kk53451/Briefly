export interface NewsCard {
  news_id: string;
  category_date: string; // "politics#2025-01-08"
  category: string; // "politics"
  rank: number;
  title: string;
  images: string; // Single URL (not array)
  provider_link_page: string;
  provider: string; // "연합뉴스"
  byline: string; // "홍길동 기자"
  published_at: string;
  hilight: string; // 200-char highlight
  content: string; // Full article text
  collected_at: string;
  bookmarked_at?: string; // Only in bookmark responses
}

export interface NewsGroupByProvider {
  provider: string;
  count: number;
  news_list: NewsCard[];
}

export interface NewsGroupByCategory {
  category: string;
  count: number;
  news_list: NewsCard[];
}

export interface BookmarkRequest {
  news_id: string;
}

export interface BookmarkResponse {
  message: string;
  news_id: string;
  bookmarked_at: string;
}