# Briefly Backend API 문서 v2.0

## 📋 개요

이 문서는 **Briefly** 프로젝트의 백엔드 API 엔드포인트 사용법을 설명합니다.
프론트엔드 개발자가 Next.js 프로젝트에 백엔드 API를 연동할 때 참고하세요.

**최신 업데이트 (v2.0):**
- 🆕 주파수 히스토리 API 추가
- 🔧 카테고리 매핑 시스템 개선 (한국어 ↔ 영어)
- 🗑️ Mock 데이터 제거 및 실제 DynamoDB 데이터 사용
- ⚡ 성능 및 안정성 개선

## 🌐 기본 정보

- **Base URL**: `http://localhost:8000` (개발) / `https://your-api-domain.com` (운영)
- **API 문서**: `http://localhost:8000/docs` (FastAPI 자동 생성)
- **프레임워크**: FastAPI + uvicorn
- **인증 방식**: JWT Bearer Token
- **데이터베이스**: AWS DynamoDB

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
  "interests": ["정치", "경제", "IT/과학"],
  "onboarding_completed": true,
  "created_at": "2025-05-01T00:00:00"
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

**⚠️ 카테고리 매핑 중요사항:**
- **프론트엔드**: 한국어 카테고리 사용 (`["정치", "경제", "IT/과학"]`)
- **백엔드/DynamoDB**: 영어 카테고리 사용 (`["politics", "economy", "tech"]`)
- **자동 변환**: API에서 한국어 ↔ 영어 자동 변환 처리

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
- `category`: 한국어 또는 영어 카테고리명 (예: "정치" 또는 "politics")

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
    "thumbnail_url": "https://...",
    "publisher": "연합뉴스",
    "published_at": "2025-06-03T09:00:00",
    "category": "politics",
    "rank": 1,
    "companies": ["삼성전자", "LG전자"],
    "esg": ["환경", "사회"]
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

**🔄 실시간 데이터:** Mock 데이터가 제거되어 실제 DynamoDB에서만 데이터를 가져옵니다.

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
  "published_at": "2025-06-03T09:00:00",
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

## 4. 📻 주파수/오디오 (Frequency) - **업데이트됨**

### 4.1 사용자 맞춤 오디오 목록 (오늘)
```http
GET /api/frequencies
```
**인증 필요** ✅

사용자의 관심 카테고리별 **오늘자** TTS 오디오를 반환합니다.

**응답 예시:**
```json
[
  {
    "frequency_id": "politics#2025-06-03",
    "category": "politics",
    "script": "오늘의 정치 뉴스 요약 스크립트입니다. 국회에서는...",
    "audio_url": "https://s3.amazonaws.com/briefly-bucket/audio/politics/2025-06-03.mp3",
    "date": "2025-06-03",
    "created_at": "2025-06-03T06:00:00",
    "duration": 180
  },
  {
    "frequency_id": "economy#2025-06-03",
    "category": "economy",
    "script": "오늘의 경제 뉴스 요약입니다. 코스피는...",
    "audio_url": "https://s3.amazonaws.com/briefly-bucket/audio/economy/2025-06-03.mp3",
    "date": "2025-06-03",
    "created_at": "2025-06-03T06:00:00",
    "duration": 165
  }
]
```

### 4.2 🆕 주파수 히스토리 조회
```http
GET /api/frequencies/history?limit={limit}
```
**인증 필요** ✅

사용자의 관심 카테고리별 **과거** 주파수 데이터를 날짜순으로 반환합니다.

**쿼리 파라미터:**
- `limit`: 조회할 개수 (기본값: 30, 최대: 100)

**응답 예시:**
```json
[
  {
    "frequency_id": "politics#2025-06-02",
    "category": "politics",
    "script": "6월 2일 정치 뉴스 요약...",
    "audio_url": "https://s3.amazonaws.com/briefly-bucket/audio/politics/2025-06-02.mp3",
    "date": "2025-06-02",
    "created_at": "2025-06-02T06:00:00",
    "duration": 175
  },
  {
    "frequency_id": "economy#2025-06-02",
    "category": "economy",
    "script": "6월 2일 경제 뉴스 요약...",
    "audio_url": "https://s3.amazonaws.com/briefly-bucket/audio/economy/2025-06-02.mp3",
    "date": "2025-06-02",
    "created_at": "2025-06-02T06:00:00",
    "duration": 160
  }
]
```

**📝 특징:**
- 오늘 날짜는 제외하고 과거 데이터만 반환
- 최신순으로 정렬
- 사용자 관심 카테고리에 해당하는 데이터만 필터링

### 4.3 특정 카테고리 오디오 상세
```http
GET /api/frequencies/{category}
```
**인증 필요** ✅

**파라미터:**
- `category`: 한국어 또는 영어 카테고리명 (예: "정치" 또는 "politics")

**응답 예시:**
```json
{
  "frequency_id": "politics#2025-06-03",
  "category": "politics",
  "script": "오늘의 정치 뉴스 요약 스크립트...",
  "audio_url": "https://s3.amazonaws.com/briefly-bucket/audio/politics/2025-06-03.mp3",
  "date": "2025-06-03",
  "created_at": "2025-06-03T06:00:00",
  "duration": 180
}
```

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

**카테고리 매핑 테이블:**
| 한국어 | 영어 (API) | 설명 |
|--------|------------|------|
| 정치 | politics | 정치 관련 뉴스 |
| 경제 | economy | 경제, 금융 뉴스 |
| 사회 | society | 사회 일반 뉴스 |
| 생활/문화 | lifestyle | 생활, 문화 뉴스 |
| IT/과학 | tech | IT, 과학기술 뉴스 |
| 세계 | world | 국제, 해외 뉴스 |
| 스포츠 | sports | 스포츠 뉴스 |
| 연예 | entertainment | 연예, 오락 뉴스 |

---

## 🚀 프론트엔드 연동 예시

### TypeScript 타입 정의
```typescript
// types/api.ts
export interface FrequencyItem {
  frequency_id: string;
  category: string;
  script: string;
  audio_url: string;
  date: string;
  created_at: string;
  duration?: number;
}

export interface NewsItem {
  news_id: string;
  title: string;
  title_ko?: string;
  summary: string;
  summary_ko?: string;
  image_url: string;
  thumbnail_url?: string;
  publisher: string;
  published_at: string;
  category: string;
  rank?: number;
  companies?: string[];
  esg?: string[];
}
```

### React/Next.js 연동 코드

#### 1. 주파수 히스토리 컴포넌트 예시
```typescript
// components/FrequencyHistory.tsx
import { useState, useEffect } from 'react';
import { apiClient } from '../lib/api';
import type { FrequencyItem } from '../types/api';

export function FrequencyHistory() {
  const [frequencies, setFrequencies] = useState<FrequencyItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchFrequencyHistory();
  }, []);

  const fetchFrequencyHistory = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getFrequencyHistory(30);
      setFrequencies(data);
    } catch (error) {
      console.error('주파수 히스토리 조회 실패:', error);
      setError('데이터를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>로딩 중...</div>;
  if (error) return <div>오류: {error}</div>;

  return (
    <div>
      <h2>주파수 히스토리</h2>
      {frequencies.map((frequency) => (
        <div key={frequency.frequency_id}>
          <h3>{frequency.date} - {frequency.category}</h3>
          <audio controls src={frequency.audio_url} />
          <p>{frequency.script.slice(0, 100)}...</p>
        </div>
      ))}
    </div>
  );
}
```

#### 2. API 클라이언트 업데이트
```typescript
// lib/api.ts
class ApiClient {
  // 기존 메서드들...

  async getUserFrequencies(): Promise<FrequencyItem[]> {
    return this.request<FrequencyItem[]>("/api/frequencies");
  }

  async getFrequencyHistory(limit: number = 30): Promise<FrequencyItem[]> {
    return this.request<FrequencyItem[]>(`/api/frequencies/history?limit=${limit}`);
  }

  async getFrequencyByCategory(category: string): Promise<FrequencyItem> {
    return this.request<FrequencyItem>(`/api/frequencies/${encodeURIComponent(category)}`);
  }
}
```

#### 3. 카테고리 매핑 유틸리티
```typescript
// lib/constants.ts
export const CATEGORY_MAP: Record<string, string> = {
  "politics": "정치",
  "economy": "경제", 
  "society": "사회",
  "lifestyle": "생활/문화",
  "tech": "IT/과학",
  "world": "세계",
  "sports": "스포츠",
  "entertainment": "연예"
};

export const REVERSE_CATEGORY_MAP: Record<string, string> = {
  "정치": "politics",
  "경제": "economy",
  "사회": "society", 
  "생활/문화": "lifestyle",
  "IT/과학": "tech",
  "세계": "world",
  "스포츠": "sports",
  "연예": "entertainment"
};

export function getKoreanCategory(englishCategory: string): string {
  return CATEGORY_MAP[englishCategory] || englishCategory;
}

export function getEnglishCategory(koreanCategory: string): string {
  return REVERSE_CATEGORY_MAP[koreanCategory] || koreanCategory;
}
```

---

## ⚠️ 중요 변경사항 (v2.0)

### 🗑️ Mock 데이터 제거
- **이전**: API 오류 시 Mock 데이터 자동 반환
- **현재**: 실제 DynamoDB 데이터만 사용, 오류 시 적절한 에러 메시지 반환
- **주의**: 개발 시 실제 데이터가 없으면 빈 배열이 반환됨

### 🔄 카테고리 매핑 개선
- **문제**: 사용자 관심사(한국어)와 DynamoDB 저장 형식(영어) 불일치
- **해결**: API 레벨에서 자동 변환 처리
- **영향**: 프론트엔드는 한국어 카테고리만 사용하면 됨

### 📈 성능 개선
- **주파수 API**: 사용자 관심사에 해당하는 데이터만 조회
- **히스토리 API**: 날짜별 정렬 및 제한 개수 설정
- **캐싱**: DynamoDB 쿼리 최적화

---

## 🔧 개발 환경 설정

### 백엔드 실행
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### AWS SAM 배포
```bash
cd backend
sam build
sam deploy --guided
```

### 환경변수 설정
백엔드 실행 전 필요한 환경변수들:
- `AWS_REGION`: AWS 리전 (예: us-east-1)
- `KAKAO_CLIENT_ID`: 카카오 로그인 클라이언트 ID
- `KAKAO_REDIRECT_URI`: 카카오 로그인 리다이렉트 URI
- `DDB_NEWS_TABLE`: DynamoDB 뉴스 테이블명
- `DDB_FREQ_TABLE`: DynamoDB 주파수 테이블명
- `DDB_USERS_TABLE`: DynamoDB 사용자 테이블명
- `DDB_BOOKMARKS_TABLE`: DynamoDB 북마크 테이블명

---

## 🚀 마이그레이션 가이드 (v1.x → v2.0)

### 프론트엔드 변경사항
1. **주파수 히스토리 API 추가**: `getFrequencyHistory()` 메서드 사용
2. **Mock 데이터 제거**: 에러 처리 로직 강화 필요
3. **카테고리 매핑**: 기존 코드 유지 가능 (자동 변환)

### 백엔드 변경사항
1. **새로운 API 엔드포인트**: `/api/frequencies/history`
2. **DynamoDB 함수 추가**: `get_frequency_history_by_categories()`
3. **카테고리 매핑 로직**: 모든 주파수 API에 적용

---

이 문서를 참고하여 프론트엔드와 백엔드를 연동하시면 됩니다. 
추가 질문이나 문제가 있으시면 언제든 연락주세요! 🚀 