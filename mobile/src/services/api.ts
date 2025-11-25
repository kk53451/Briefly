/**
 * API client for Briefly backend
 * Handles all HTTP requests and token management
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import * as SecureStore from 'expo-secure-store';
import {
  AuthResponse,
  UserProfile,
  NewsItem,
  NewsDetail,
  TodayNewsResponse,
  HomeNewsResponse,
  FrequencyItem,
  CategoriesResponse,
  UserCategoriesResponse,
  OnboardingStatusResponse,
  UpdateProfileRequest,
  UpdateCategoriesRequest,
  BookmarkRequest,
} from '../types/api';

// API Base URL from environment variables
const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';
// For local development, set EXPO_PUBLIC_API_URL to http://10.0.2.2:8000 (Android) or http://localhost:8000 (iOS)

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor: Add auth token
    this.client.interceptors.request.use(
      async (config) => {
        const token = await SecureStore.getItemAsync('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor: Handle errors
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          await SecureStore.deleteItemAsync('access_token');
          // You could emit an event here to trigger logout
        }
        return Promise.reject(error);
      }
    );
  }

  // ========== Auth APIs ==========

  async getKakaoLoginUrl(): Promise<string> {
    const response = await this.client.get<{ url: string }>('/api/auth/kakao/login');
    return response.data.url;
  }

  async handleKakaoCallback(code: string): Promise<AuthResponse> {
    const response = await this.client.get<AuthResponse>('/api/auth/kakao/callback', {
      params: { code },
    });
    await SecureStore.setItemAsync('access_token', response.data.access_token);
    return response.data;
  }

  async loginWithKakaoToken(accessToken: string): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/api/auth/kakao/token', {
      access_token: accessToken,
    });
    await SecureStore.setItemAsync('access_token', response.data.access_token);
    return response.data;
  }

  async getCurrentUser(): Promise<UserProfile> {
    const response = await this.client.get<UserProfile>('/api/auth/me');
    return response.data;
  }

  async logout(): Promise<void> {
    await this.client.post('/api/auth/logout');
    await SecureStore.deleteItemAsync('access_token');
  }

  // ========== News APIs ==========

  async getNewsByCategory(category: string): Promise<NewsItem[]> {
    const response = await this.client.get<NewsItem[]>('/api/news', {
      params: { category },
    });
    return response.data;
  }

  async getTodayNews(): Promise<TodayNewsResponse> {
    const response = await this.client.get<TodayNewsResponse>('/api/news/today');
    return response.data;
  }

  async getHomeNews(date?: string): Promise<HomeNewsResponse> {
    const response = await this.client.get<HomeNewsResponse>('/api/news/home', {
      params: date ? { date } : undefined,
    });
    return response.data;
  }

  async getNewsDetail(newsId: string): Promise<NewsDetail> {
    const response = await this.client.get<NewsDetail>(`/api/news/${newsId}`);
    return response.data;
  }

  async addBookmark(newsId: string): Promise<void> {
    await this.client.post('/api/news/bookmark', { news_id: newsId } as BookmarkRequest);
  }

  async removeBookmark(newsId: string): Promise<void> {
    await this.client.delete(`/api/news/bookmark/${newsId}`);
  }

  // ========== User APIs ==========

  async getUserProfile(): Promise<UserProfile> {
    const response = await this.client.get<UserProfile>('/api/user/profile');
    return response.data;
  }

  async updateProfile(data: UpdateProfileRequest): Promise<void> {
    await this.client.put('/api/user/profile', data);
  }

  async getBookmarks(): Promise<NewsItem[]> {
    const response = await this.client.get<NewsItem[]>('/api/user/bookmarks');
    return response.data;
  }

  async getUserCategories(): Promise<UserCategoriesResponse> {
    const response = await this.client.get<UserCategoriesResponse>('/api/user/categories');
    return response.data;
  }

  async updateUserCategories(interests: string[]): Promise<void> {
    await this.client.put('/api/user/categories', { interests } as UpdateCategoriesRequest);
  }

  async getOnboardingStatus(): Promise<OnboardingStatusResponse> {
    const response = await this.client.get<OnboardingStatusResponse>('/api/user/onboarding/status');
    return response.data;
  }

  async completeOnboarding(): Promise<void> {
    await this.client.post('/api/user/onboarding');
  }

  // ========== Frequency/Podcast APIs ==========

  async getFrequencies(): Promise<FrequencyItem[]> {
    const response = await this.client.get<FrequencyItem[]>('/api/frequencies');
    return response.data;
  }

  async getFrequencyHistory(limit: number = 30): Promise<FrequencyItem[]> {
    const response = await this.client.get<FrequencyItem[]>('/api/frequencies/history', {
      params: { limit },
    });
    return response.data;
  }

  async getFrequencyByCategory(category: string): Promise<FrequencyItem> {
    const response = await this.client.get<FrequencyItem>(`/api/frequencies/${category}`);
    return response.data;
  }

  // ========== Category APIs ==========

  async getAllCategories(): Promise<CategoriesResponse> {
    const response = await this.client.get<CategoriesResponse>('/api/categories');
    return response.data;
  }
}

export const apiClient = new ApiClient();
