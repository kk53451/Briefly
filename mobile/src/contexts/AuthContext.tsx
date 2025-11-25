/**
 * Authentication Context for managing user state
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import * as SecureStore from 'expo-secure-store';
import { apiClient } from '../services/api';
import { UserProfile } from '../types/api';

interface AuthContextType {
  user: UserProfile | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (code: string) => Promise<void>;
  loginWithKakao: (accessToken: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  updateUser: (user: UserProfile) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const token = await SecureStore.getItemAsync('access_token');
      if (token) {
        const userData = await apiClient.getCurrentUser();
        setUser(userData);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      await SecureStore.deleteItemAsync('access_token');
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (code: string) => {
    try {
      const authResponse = await apiClient.handleKakaoCallback(code);
      const userData = await apiClient.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const loginWithKakao = async (accessToken: string) => {
    try {
      console.log('📡 백엔드에 카카오 토큰 전송 중...');

      // Send Kakao access token to backend
      const authResponse = await apiClient.loginWithKakaoToken(accessToken);

      console.log('✅ JWT 토큰 받음:', authResponse.access_token ? 'success' : 'failed');
      console.log('👤 사용자 정보:', authResponse.nickname);

      // Get full user data
      const userData = await apiClient.getCurrentUser();
      setUser(userData);

      console.log('✅ 로그인 완료!');
    } catch (error: any) {
      console.error('❌ Kakao token login failed:', error);

      // 에러 정보를 더 명확하게 전달
      if (error.response) {
        console.error('Response error:', error.response.data);
        console.error('Response status:', error.response.status);
      }

      throw error;
    }
  };

  const logout = async () => {
    try {
      await apiClient.logout();
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      setUser(null);
      await SecureStore.deleteItemAsync('access_token');
    }
  };

  const refreshUser = async () => {
    try {
      const userData = await apiClient.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error('Failed to refresh user:', error);
      throw error;
    }
  };

  const updateUser = (updatedUser: UserProfile) => {
    setUser(updatedUser);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        loginWithKakao,
        logout,
        refreshUser,
        updateUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
