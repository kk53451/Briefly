import axios, { AxiosInstance, AxiosError } from "axios";
import { storage } from "./storage";
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
  LoginResponse,
} from "../types/api";

// 백엔드 API URL - 환경변수로 관리
const API_BASE_URL = "http://localhost:8000"; // 실제 배포 시 변경 필요

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        "Content-Type": "application/json",
      },
    });

    // Request 인터셉터 - 토큰 자동 추가
    this.client.interceptors.request.use(
      async (config) => {
        const token = await storage.getAccessToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response 인터셉터 - 에러 핸들링
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError<ApiError>) => {
        if (error.response?.status === 401) {
          // 토큰 만료 시 로그아웃 처리
          await storage.clear();
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth APIs
  async getKakaoLoginUrl(): Promise<string> {
    return `${API_BASE_URL}/api/auth/kakao/login`;
  }

  async handleKakaoCallback(code: string): Promise<LoginResponse> {
    const response = await this.client.get<LoginResponse>(
      `/api/auth/kakao/callback?code=${code}`
    );
    return response.data;
  }

  async getCurrentUser(): Promise<UserProfile> {
    const response = await this.client.get<UserProfile>("/api/auth/me");
    return response.data;
  }

  async logout(): Promise<void> {
    await this.client.post("/api/auth/logout");
    await storage.clear();
  }

  // News APIs
  async getNewsByCategory(category: string): Promise<NewsItem[]> {
    const response = await this.client.get<NewsItem[]>(
      `/api/news?category=${encodeURIComponent(category)}`
    );
    return response.data;
  }

  async getTodayNews(): Promise<TodayNewsResponse> {
    const response = await this.client.get<TodayNewsResponse>("/api/news/today");
    return response.data;
  }

  async getNewsDetail(newsId: string): Promise<NewsDetail> {
    const response = await this.client.get<NewsDetail>(`/api/news/${newsId}`);
    return response.data;
  }

  async bookmarkNews(newsId: string): Promise<void> {
    await this.client.post("/api/news/bookmark", { news_id: newsId });
  }

  async removeBookmark(newsId: string): Promise<void> {
    await this.client.delete(`/api/news/bookmark/${newsId}`);
  }

  // User APIs
  async getUserProfile(): Promise<UserProfile> {
    const response = await this.client.get<UserProfile>("/api/user/profile");
    return response.data;
  }

  async updateUserProfile(data: Partial<UserProfile>): Promise<UserProfile> {
    const response = await this.client.put<UserProfile>("/api/user/profile", data);
    return response.data;
  }

  async getUserBookmarks(): Promise<NewsItem[]> {
    const response = await this.client.get<NewsItem[]>("/api/user/bookmarks");
    return response.data;
  }

  async getUserCategories(): Promise<UserCategoriesResponse> {
    const response = await this.client.get<UserCategoriesResponse>("/api/user/categories");
    return response.data;
  }

  async updateUserCategories(interests: string[]): Promise<void> {
    await this.client.put("/api/user/categories", { interests });
  }

  async getOnboardingStatus(): Promise<OnboardingStatusResponse> {
    const response = await this.client.get<OnboardingStatusResponse>(
      "/api/user/onboarding/status"
    );
    return response.data;
  }

  async completeOnboarding(): Promise<void> {
    await this.client.post("/api/user/onboarding");
  }

  // Frequency APIs
  async getUserFrequencies(): Promise<FrequencyItem[]> {
    const response = await this.client.get<FrequencyItem[]>("/api/frequencies");
    return response.data;
  }

  async getFrequencyHistory(limit: number = 30): Promise<FrequencyItem[]> {
    const response = await this.client.get<FrequencyItem[]>(
      `/api/frequencies/history?limit=${limit}`
    );
    return response.data;
  }

  async getFrequencyByCategory(category: string): Promise<FrequencyItem> {
    const response = await this.client.get<FrequencyItem>(
      `/api/frequencies/${encodeURIComponent(category)}`
    );
    return response.data;
  }

  // Category APIs
  async getCategories(): Promise<CategoriesResponse> {
    const response = await this.client.get<CategoriesResponse>("/api/categories");
    return response.data;
  }
}

export const apiClient = new ApiClient();
