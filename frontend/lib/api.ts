import type {
  UserProfile,
  NewsItem,
  TodayNewsResponse,
  NewsDetail,
  UserCategoriesResponse,
  FrequencyItem,
  CategoriesResponse,
  OnboardingStatusResponse,
  ApiError,
} from "@/types/api"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

class ApiClient {
  private getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem("access_token")
    return {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
    }
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`
    // API 로깅은 필요시 활성화
    // console.log(`[API] ${options.method || "GET"} ${url}`)

    const response = await fetch(url, {
      ...options,
      headers: {
        ...this.getAuthHeaders(),
        ...options.headers,
      },
    })

    if (!response.ok) {
      const errorData: ApiError = await response.json().catch(() => ({ detail: "Unknown error" }))
      throw new Error(errorData.detail || `API Error: ${response.status}`)
    }

    return response.json()
  }

  // Auth APIs
  async getKakaoLoginUrl(): Promise<void> {
    window.location.href = `${API_BASE_URL}/api/auth/kakao/login`
  }

  async getCurrentUser(): Promise<UserProfile> {
    return this.request<UserProfile>("/api/auth/me")
  }

  async logout(): Promise<void> {
    return this.request("/api/auth/logout", { method: "POST" })
  }

  // News APIs
  async getNewsByCategory(category: string): Promise<NewsItem[]> {
    const endpoint = `/api/news?category=${encodeURIComponent(category)}`
    return this.request<NewsItem[]>(endpoint)
  }

  async getTodayNews(): Promise<TodayNewsResponse> {
    const endpoint = "/api/news/today"
    return this.request<TodayNewsResponse>(endpoint)
  }

  async getNewsDetail(newsId: string): Promise<NewsDetail> {
    const endpoint = `/api/news/${newsId}`
    return this.request<NewsDetail>(endpoint)
  }

  async bookmarkNews(newsId: string): Promise<void> {
    return this.request("/api/news/bookmark", {
      method: "POST",
      body: JSON.stringify({ news_id: newsId }),
    })
  }

  async removeBookmark(newsId: string): Promise<void> {
    return this.request(`/api/news/bookmark/${newsId}`, {
      method: "DELETE",
    })
  }

  // User APIs
  async getUserProfile(): Promise<UserProfile> {
    return this.request<UserProfile>("/api/user/profile")
  }

  async updateUserProfile(data: Partial<UserProfile>): Promise<UserProfile> {
    return this.request("/api/user/profile", {
      method: "PUT",
      body: JSON.stringify(data),
    })
  }

  async getUserBookmarks(): Promise<NewsItem[]> {
    return this.request<NewsItem[]>("/api/user/bookmarks")
  }

  async getUserCategories(): Promise<UserCategoriesResponse> {
    return this.request<UserCategoriesResponse>("/api/user/categories")
  }

  async updateUserCategories(interests: string[]): Promise<void> {
    return this.request("/api/user/categories", {
      method: "PUT",
      body: JSON.stringify({ interests }),
    })
  }

  async getOnboardingStatus(): Promise<OnboardingStatusResponse> {
    return this.request<OnboardingStatusResponse>("/api/user/onboarding/status")
  }

  async completeOnboarding(): Promise<void> {
    return this.request("/api/user/onboarding", {
      method: "POST",
    })
  }

  // Frequency APIs
  async getUserFrequencies(): Promise<FrequencyItem[]> {
    return this.request<FrequencyItem[]>("/api/frequencies")
  }

  async getFrequencyHistory(limit: number = 30): Promise<FrequencyItem[]> {
    return this.request<FrequencyItem[]>(`/api/frequencies/history?limit=${limit}`)
  }

  async getFrequencyByCategory(category: string): Promise<FrequencyItem> {
    return this.request<FrequencyItem>(`/api/frequencies/${encodeURIComponent(category)}`)
  }

  // Category APIs
  async getCategories(): Promise<CategoriesResponse> {
    return this.request<CategoriesResponse>("/api/categories")
  }
}

export const apiClient = new ApiClient()
