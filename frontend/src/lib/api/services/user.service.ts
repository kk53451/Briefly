import { apiClient } from '../client';
import { API_ENDPOINTS } from '../config';
import { User, UpdateProfileRequest, OnboardingRequest, NewsCard } from '../../../types';

export const userService = {
  // Get user profile
  async getProfile(): Promise<User> {
    const response = await apiClient.get<User>(API_ENDPOINTS.USER.PROFILE);
    return response.data;
  },

  // Update user profile
  async updateProfile(data: UpdateProfileRequest): Promise<User> {
    const response = await apiClient.put<User>(API_ENDPOINTS.USER.PROFILE, data);
    return response.data;
  },

  // Get user bookmarks
  async getBookmarks(): Promise<NewsCard[]> {
    const response = await apiClient.get<NewsCard[]>(API_ENDPOINTS.USER.BOOKMARKS);
    return response.data;
  },

  // Get user categories
  async getCategories(): Promise<string[]> {
    const response = await apiClient.get<string[]>(API_ENDPOINTS.USER.CATEGORIES);
    return response.data;
  },

  // Update user categories
  async updateCategories(categories: string[]): Promise<{ message: string; interests: string[] }> {
    const response = await apiClient.put<{ message: string; interests: string[] }>(
      API_ENDPOINTS.USER.CATEGORIES,
      { interests: categories }
    );
    return response.data;
  },

  // Complete onboarding
  async completeOnboarding(data: OnboardingRequest): Promise<{ message: string; user: User }> {
    const response = await apiClient.post<{ message: string; user: User }>(
      API_ENDPOINTS.USER.ONBOARDING,
      data
    );
    return response.data;
  },

  // Get onboarding status
  async getOnboardingStatus(): Promise<{ onboarding_completed: boolean }> {
    const response = await apiClient.get<{ onboarding_completed: boolean }>(
      API_ENDPOINTS.USER.ONBOARDING_STATUS
    );
    return response.data;
  },
};