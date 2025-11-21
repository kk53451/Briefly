import axios, { AxiosInstance } from 'axios';
import * as SecureStore from 'expo-secure-store';
import { API_CONFIG } from './config';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_CONFIG.BASE_URL,
      timeout: API_CONFIG.TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      async (config) => {
        try {
          const token = await SecureStore.getItemAsync('jwt_token');
          if (token) {
            config.headers.Authorization = `Bearer ${token}`;
          }
        } catch (error) {
          console.error('Error getting token from SecureStore:', error);
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor to handle errors
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          // Unauthorized - clear token and redirect to login
          await this.clearAuthToken();
          // You might want to trigger navigation to login screen here
          // Using a global event emitter or navigation ref
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth token management
  async setAuthToken(token: string): Promise<void> {
    await SecureStore.setItemAsync('jwt_token', token);
  }

  async getAuthToken(): Promise<string | null> {
    return await SecureStore.getItemAsync('jwt_token');
  }

  async clearAuthToken(): Promise<void> {
    await SecureStore.deleteItemAsync('jwt_token');
  }

  // HTTP methods
  get<T>(url: string, params?: any) {
    return this.client.get<T>(url, { params });
  }

  post<T>(url: string, data?: any) {
    return this.client.post<T>(url, data);
  }

  put<T>(url: string, data?: any) {
    return this.client.put<T>(url, data);
  }

  delete<T>(url: string) {
    return this.client.delete<T>(url);
  }

  // Get the axios instance for custom configurations
  getInstance() {
    return this.client;
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Export convenience functions
export const setAuthToken = (token: string) => apiClient.setAuthToken(token);
export const getAuthToken = () => apiClient.getAuthToken();
export const clearAuthToken = () => apiClient.clearAuthToken();