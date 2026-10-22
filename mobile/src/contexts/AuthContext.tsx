/**
 * Authentication Context (Kakao 제거 후 게스트 모드)
 *
 * 현재는 Kakao SDK 의존성을 제거하기 위해 **게스트 모드**로 동작.
 * 앱 시작 시 자동으로 게스트 사용자로 로그인된 상태를 만듭니다.
 * 추후 다른 인증 수단(이메일, Google, Apple 등)으로 교체할 수 있도록
 * 인터페이스는 유지합니다.
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import * as SecureStore from 'expo-secure-store';
import { apiClient } from '../services/api';
import { UserProfile } from '../types/api';

interface AuthContextType {
  user: UserProfile | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (code?: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  updateUser: (user: UserProfile) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// 게스트 사용자 기본 프로필 (서버 연동 실패 시 fallback)
const GUEST_USER_FALLBACK: UserProfile = {
  user_id: 'guest',
  nickname: '게스트',
  interests: ['정치', '경제', '사회', '문화', '국제', 'IT/과학'],
  onboarding_completed: true,
  created_at: new Date().toISOString(),
};

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    bootstrap();
  }, []);

  const bootstrap = async () => {
    // 저장된 토큰이 있으면 그대로 쓰고, 없거나 만료됐으면 게스트 로그인 발급
    try {
      const token = await SecureStore.getItemAsync('access_token');
      if (token) {
        try {
          const userData = await apiClient.getCurrentUser();
          setUser(userData);
          setIsLoading(false);
          return;
        } catch {
          // 토큰 만료/무효 → 게스트 로그인 재발급
          await SecureStore.deleteItemAsync('access_token');
        }
      }

      await guestLoginFlow();
    } finally {
      setIsLoading(false);
    }
  };

  const guestLoginFlow = async () => {
    try {
      await apiClient.guestLogin(); // 서버에서 JWT 저장
      const userData = await apiClient.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.warn('Guest login failed, using local fallback:', error);
      setUser(GUEST_USER_FALLBACK);
    }
  };

  const login = async (_code?: string) => {
    await guestLoginFlow();
  };

  const logout = async () => {
    try {
      await SecureStore.deleteItemAsync('access_token');
    } catch {
      // ignore
    } finally {
      setUser(null);
    }
  };

  const refreshUser = async () => {
    try {
      const userData = await apiClient.getCurrentUser();
      setUser(userData);
    } catch {
      setUser(GUEST_USER_FALLBACK);
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
