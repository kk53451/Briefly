// API Configuration
// In production, use environment variables or config files
export const API_CONFIG = {
  BASE_URL: process.env.API_BASE_URL || 'http://localhost:8000',
  TIMEOUT: 10000,
  KAKAO_CLIENT_ID: process.env.KAKAO_CLIENT_ID || '',
};

export const API_ENDPOINTS = {
  // Auth
  AUTH: {
    KAKAO_LOGIN: '/api/auth/kakao/login',
    KAKAO_CALLBACK: '/api/auth/kakao/callback',
    ME: '/api/auth/me',
    LOGOUT: '/api/auth/logout',
  },

  // User
  USER: {
    PROFILE: '/api/user/profile',
    BOOKMARKS: '/api/user/bookmarks',
    FREQUENCIES: '/api/user/frequencies',
    CATEGORIES: '/api/user/categories',
    ONBOARDING: '/api/user/onboarding',
    ONBOARDING_STATUS: '/api/user/onboarding/status',
  },

  // News
  NEWS: {
    LIST: '/api/news',
    TODAY: '/api/news/today',
    HOME: '/api/news/home',
    DETAIL: (id: string) => `/api/news/${id}`,
    BOOKMARK: '/api/news/bookmark',
    UNBOOKMARK: (id: string) => `/api/news/bookmark/${id}`,
  },

  // Frequencies
  FREQUENCIES: {
    LIST: '/api/frequencies',
    HISTORY: '/api/frequencies/history',
    BY_CATEGORY: (category: string) => `/api/frequencies/${category}`,
  },

  // Categories
  CATEGORIES: '/api/categories',
};