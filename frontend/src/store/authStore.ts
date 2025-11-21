import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';
import { User, AuthResponse } from '../types';
import { authService } from '../lib/api/services';
import { setAuthToken, clearAuthToken } from '../lib/api/client';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (authResponse: AuthResponse) => Promise<void>;
  logout: () => Promise<void>;
  loadAuth: () => Promise<void>;
  updateUser: (user: User) => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,

  login: async (authResponse: AuthResponse) => {
    try {
      set({ isLoading: true, error: null });

      // Store JWT token
      await setAuthToken(authResponse.access_token);

      // Store user data
      await SecureStore.setItemAsync('user_id', authResponse.user_id);
      await SecureStore.setItemAsync('user_data', JSON.stringify({
        user_id: authResponse.user_id,
        nickname: authResponse.nickname,
        profile_image: authResponse.profile_image,
        onboarding_completed: authResponse.onboarding_completed,
      } as Partial<User>));

      // Fetch full user data
      const user = await authService.getCurrentUser();

      set({
        user,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
    } catch (error) {
      console.error('Login error:', error);
      set({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: 'Failed to login. Please try again.',
      });
    }
  },

  logout: async () => {
    try {
      set({ isLoading: true });

      // Call logout API
      await authService.logout();

      // Clear stored data
      await clearAuthToken();
      await SecureStore.deleteItemAsync('user_id');
      await SecureStore.deleteItemAsync('user_data');

      set({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      });
    } catch (error) {
      console.error('Logout error:', error);
      // Even if logout fails, clear local data
      await clearAuthToken();
      await SecureStore.deleteItemAsync('user_id');
      await SecureStore.deleteItemAsync('user_data');

      set({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      });
    }
  },

  loadAuth: async () => {
    try {
      set({ isLoading: true });

      const token = await SecureStore.getItemAsync('jwt_token');
      const userData = await SecureStore.getItemAsync('user_data');

      if (token && userData) {
        // Try to fetch fresh user data
        try {
          const user = await authService.getCurrentUser();
          set({
            user,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error) {
          // If API fails, use cached data
          const cachedUser = JSON.parse(userData) as Partial<User>;
          if (cachedUser.user_id) {
            set({
              user: cachedUser as User,
              isAuthenticated: true,
              isLoading: false,
              error: null,
            });
          } else {
            // Invalid cached data
            set({
              user: null,
              isAuthenticated: false,
              isLoading: false,
              error: null,
            });
          }
        }
      } else {
        // No stored auth
        set({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
        });
      }
    } catch (error) {
      console.error('Load auth error:', error);
      set({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      });
    }
  },

  updateUser: (user: User) => {
    set({ user });
    // Also update cached user data
    SecureStore.setItemAsync('user_data', JSON.stringify(user)).catch(console.error);
  },

  clearError: () => {
    set({ error: null });
  },
}));