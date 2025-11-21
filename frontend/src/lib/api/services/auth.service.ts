import { apiClient } from '../client';
import { API_ENDPOINTS } from '../config';
import { AuthResponse, User } from '../../../types';

export const authService = {
  // Get current user
  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>(API_ENDPOINTS.AUTH.ME);
    return response.data;
  },

  // Exchange Kakao code for JWT token
  async kakaoCallback(code: string): Promise<AuthResponse> {
    const response = await apiClient.get<AuthResponse>(
      API_ENDPOINTS.AUTH.KAKAO_CALLBACK,
      { code }
    );
    return response.data;
  },

  // Logout
  async logout(): Promise<void> {
    await apiClient.post(API_ENDPOINTS.AUTH.LOGOUT);
    await apiClient.clearAuthToken();
  },
};