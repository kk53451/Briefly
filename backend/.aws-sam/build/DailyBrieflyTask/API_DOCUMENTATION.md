# Briefly Backend API 문서

## 📋 개요

이 문서는 **Briefly** 프로젝트의 백엔드 API 엔드포인트 사용법을 설명합니다.
프론트엔드 개발자가 Next.js 프로젝트에 백엔드 API를 연동할 때 참고하세요.

## 🌐 기본 정보

- **Base URL**: `http://localhost:8000`
- **API 문서**: `http://localhost:8000/docs` (FastAPI 자동 생성)
- **프레임워크**: FastAPI + uvicorn
- **인증 방식**: JWT Bearer Token

## 🔐 인증 시스템

### Headers 설정
인증이 필요한 API는 헤더에 JWT 토큰을 포함해야 합니다:

```javascript
const headers = {
  'Authorization': `Bearer ${accessToken}`,
  'Content-Type': 'application/json'
}
```

---

## 📚 API 엔드포인트

## 1. 🔑 인증 (Authentication)

### 1.1 카카오 로그인 시작
```http
GET /api/auth/kakao/login
```
카카오 로그인 페이지로 리다이렉트합니다.

**사용 예시:**
```javascript
// 로그인 버튼 클릭 시
window.location.href = 'http://localhost:8000/api/auth/kakao/login';
```

### 1.2 카카오 로그인 콜백
```http
GET /api/auth/kakao/callback?code={authorization_code}
```

**응답 예시:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": "kakao_1234567890",
  "nickname": "홍길동"
}
```

### 1.3 사용자 정보 조회
```http
GET /api/auth/me
```
**인증 필요** ✅

**응답 예시:**
```json
{
  "user_id": "kakao_1234567890",
  "nickname": "홍길동",
  "profile_image": "https://...",
  "interests": ["정치", "경제"],
  "onboarding_completed": true,
  "created_at": "2024-01-01T00:00:00"
}
```

### 1.4 로그아웃
```http
POST /api/auth/logout
```

**응답:**
```json
{
  "message": "로그아웃 완료 (클라이언트 토큰 삭제 권장)"
}
```

---

## 2. 👤 사용자 관리 (User Management)

### 2.1 프로필 조회
```http
GET /api/user/profile
```
**인증 필요** ✅

### 2.2 프로필 수정
```http
PUT /api/user/profile
```
**인증 필요** ✅

**Body 예시:**
```json
{
  "nickname": "새로운닉네임",
  "default_length": 300,
  "profile_image": "https://example.com/image.jpg"
}
```

### 2.3 관심 카테고리 조회
```http
GET /api/user/categories
```
**인증 필요** ✅

**응답 예시:**
```json
{
  "interests": ["정치", "경제", "IT/과학"]
}
```

### 2.4 관심 카테고리 수정
```http
PUT /api/user/categories
```
**인증 필요** ✅

**Body 예시:**
```json
{
  "interests": ["정치", "경제", "IT/과학", "사회"]
}
```

### 2.5 온보딩 완료 처리
```http
POST /api/user/onboarding
```
**인증 필요** ✅

**응답:**
```json
{
  "message": "온보딩 완료"
}
```

### 2.6 온보딩 상태 확인
```http
GET /api/user/onboarding/status
```
**인증 필요** ✅

**응답 예시:**
```json
{
  "onboarded": true
}
```

### 2.7 사용자 북마크 목록
```http
GET /api/user/bookmarks
```
**인증 필요** ✅

---

## 3. 📰 뉴스 (News)

### 3.1 카테고리별 뉴스 조회
```http
GET /api/news?category={category_name}
```

**파라미터:**
- `category`: 카테고리명 (예: "정치", "경제")

**응답 예시:**
```json
[
  {
    "news_id": "news_12345",
    "title": "뉴스 제목",
    "title_ko": "한글 뉴스 제목",
    "summary": "뉴스 요약",
    "summary_ko": "한글 뉴스 요약",
    "image_url": "https://...",
    "publisher": "연합뉴스",
    "published_at": "2024-01-01T09:00:00",
    "category": "정치",
    "rank": 1
  }
]
```

### 3.2 오늘의 뉴스 (카테고리별 6개씩)
```http
GET /api/news/today
```

**응답 예시:**
```json
{
  "정치": [...6개 뉴스],
  "경제": [...6개 뉴스],
  "사회": [...6개 뉴스],
  "IT/과학": [...6개 뉴스]
}
```

### 3.3 뉴스 상세 조회
```http
GET /api/news/{news_id}
```

**응답 예시:**
```json
{
  "news_id": "news_12345",
  "title": "뉴스 제목",
  "content": "전체 뉴스 본문 내용...",
  "summary": "뉴스 요약",
  "image_url": "https://...",
  "publisher": "연합뉴스",
  "author": "기자명",
  "published_at": "2024-01-01T09:00:00",
  "content_url": "https://original-news-url.com"
}
```

### 3.4 뉴스 북마크 추가
```http
POST /api/news/bookmark
```
**인증 필요** ✅

**Body:**
```json
{
  "news_id": "news_12345"
}
```

### 3.5 뉴스 북마크 삭제
```http
DELETE /api/news/bookmark/{news_id}
```
**인증 필요** ✅

---

## 4. 📻 주파수/오디오 (Frequency)

### 4.1 사용자 맞춤 오디오 목록
```http
GET /api/frequencies
```
**인증 필요** ✅

사용자의 관심 카테고리별 오늘자 TTS 오디오를 반환합니다.

**응답 예시:**
```json
[
  {
    "frequency_id": "정치#2024-01-01",
    "category": "정치",
    "script": "오늘의 정치 뉴스 요약 스크립트...",
    "audio_url": "https://s3.amazonaws.com/briefly/audio/politics/2024-01-01.mp3",
    "created_at": "2024-01-01T06:00:00",
    "duration": 180
  }
]
```

### 4.2 특정 카테고리 오디오 상세
```http
GET /api/frequencies/{category}
```
**인증 필요** ✅

**파라미터:**
- `category`: 카테고리명 (예: "정치", "경제")

---

## 5. 🏷️ 카테고리 (Categories)

### 5.1 전체 카테고리 목록
```http
GET /api/categories
```

**응답 예시:**
```json
{
  "categories": [
    "정치", "경제", "사회", "생활/문화", 
    "IT/과학", "세계", "스포츠", "연예"
  ]
}
```

---

## 🚀 프론트엔드 연동 예시

### React/Next.js 연동 코드

#### 1. API 클라이언트 설정
```javascript
// lib/api.js
const API_BASE_URL = 'http://localhost:8000';

export const apiClient = {
  get: async (endpoint, token = null) => {
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers.Authorization = `Bearer ${token}`;
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'GET',
      headers
    });
    return response.json();
  },
  
  post: async (endpoint, data, token = null) => {
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers.Authorization = `Bearer ${token}`;
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data)
    });
    return response.json();
  },
  
  put: async (endpoint, data, token = null) => {
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers.Authorization = `Bearer ${token}`;
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(data)
    });
    return response.json();
  }
};
```

#### 2. 인증 훅 예시
```javascript
// hooks/useAuth.js
import { useState, useEffect } from 'react';
import { apiClient } from '../lib/api';

export const useAuth = () => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);

  useEffect(() => {
    const savedToken = localStorage.getItem('access_token');
    if (savedToken) {
      setToken(savedToken);
      fetchUser(savedToken);
    }
  }, []);

  const fetchUser = async (accessToken) => {
    try {
      const userData = await apiClient.get('/api/auth/me', accessToken);
      setUser(userData);
    } catch (error) {
      console.error('사용자 정보 조회 실패:', error);
      logout();
    }
  };

  const login = (accessToken) => {
    localStorage.setItem('access_token', accessToken);
    setToken(accessToken);
    fetchUser(accessToken);
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setToken(null);
    setUser(null);
  };

  return { user, token, login, logout };
};
```

#### 3. 뉴스 조회 예시
```javascript
// pages/news.js
import { useEffect, useState } from 'react';
import { apiClient } from '../lib/api';
import { useAuth } from '../hooks/useAuth';

export default function NewsPage() {
  const { token } = useAuth();
  const [todayNews, setTodayNews] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTodayNews();
  }, []);

  const fetchTodayNews = async () => {
    try {
      const data = await apiClient.get('/api/news/today');
      setTodayNews(data);
    } catch (error) {
      console.error('뉴스 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleBookmark = async (newsId) => {
    if (!token) return;
    
    try {
      await apiClient.post('/api/news/bookmark', { news_id: newsId }, token);
      alert('북마크 추가됨');
    } catch (error) {
      console.error('북마크 실패:', error);
    }
  };

  if (loading) return <div>로딩 중...</div>;

  return (
    <div>
      <h1>오늘의 뉴스</h1>
      {Object.entries(todayNews).map(([category, articles]) => (
        <div key={category}>
          <h2>{category}</h2>
          {articles.map(article => (
            <div key={article.news_id}>
              <h3>{article.title_ko || article.title}</h3>
              <p>{article.summary_ko || article.summary}</p>
              <button onClick={() => handleBookmark(article.news_id)}>
                북마크
              </button>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
```

#### 4. 온보딩 페이지 연동
```javascript
// pages/onboarding.js
import { useState } from 'react';
import { useRouter } from 'next/router';
import { apiClient } from '../lib/api';
import { useAuth } from '../hooks/useAuth';

export default function OnboardingPage() {
  const router = useRouter();
  const { token } = useAuth();
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [loading, setLoading] = useState(false);

  const categories = ['정치', '경제', 'IT/과학', '사회', '생활/문화', '세계'];

  const handleComplete = async () => {
    if (!token || selectedCategories.length === 0) return;
    
    setLoading(true);
    try {
      // 관심사 저장
      await apiClient.put('/api/user/categories', 
        { interests: selectedCategories }, 
        token
      );
      
      // 온보딩 완료 처리
      await apiClient.post('/api/user/onboarding', {}, token);
      
      router.push('/');
    } catch (error) {
      console.error('온보딩 완료 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1>관심사를 선택하세요</h1>
      {categories.map(category => (
        <button
          key={category}
          onClick={() => {
            setSelectedCategories(prev => 
              prev.includes(category) 
                ? prev.filter(c => c !== category)
                : [...prev, category]
            );
          }}
          className={selectedCategories.includes(category) ? 'selected' : ''}
        >
          {category}
        </button>
      ))}
      <button onClick={handleComplete} disabled={loading}>
        {loading ? '설정 중...' : '완료'}
      </button>
    </div>
  );
}
```

---

## ⚠️ 주의사항

1. **CORS 설정**: 백엔드에서 모든 오리진을 허용하고 있으나, 운영 환경에서는 특정 도메인으로 제한 필요
2. **토큰 관리**: JWT 토큰은 localStorage에 저장하되, XSS 공격에 주의
3. **에러 처리**: API 호출 시 적절한 에러 처리 로직 구현 필요
4. **로딩 상태**: 사용자 경험을 위해 로딩 상태 표시 권장

---

## 🔧 개발 환경 설정

### 백엔드 실행
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 환경변수 설정
백엔드 실행 전 필요한 환경변수들:
- `AWS_REGION`: AWS 리전 (예: us-east-1)
- `KAKAO_CLIENT_ID`: 카카오 로그인 클라이언트 ID
- `KAKAO_REDIRECT_URI`: 카카오 로그인 리다이렉트 URI

---

이 문서를 참고하여 프론트엔드와 백엔드를 연동하시면 됩니다. 
추가 질문이나 문제가 있으시면 언제든 연락주세요! 🚀 