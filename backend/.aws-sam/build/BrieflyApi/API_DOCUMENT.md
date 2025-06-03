# 🎙️ Briefly Backend API 문서

## 📋 프로젝트 개요

**Briefly**는 AI 기반 뉴스 팟캐스트 백엔드 시스템으로, 매일 뉴스를 수집하여 GPT-4o-mini로 요약하고 ElevenLabs TTS로 음성을 생성하는 자동화 서비스입니다.

### ✨ 핵심 기능
- 🤖 **AI 뉴스 요약**: GPT-4o-mini + 이중 클러스터링으로 중복 제거
- 🎵 **TTS 변환**: ElevenLabs 고품질 음성 생성  
- ⏰ **스케줄링**: 매일 오전 6시(KST) 자동 실행
- 🔐 **인증**: 카카오 로그인 + JWT 토큰
- 📊 **데이터**: AWS DynamoDB + S3 스토리지

### 🏗️ 시스템 아키텍처

```
🌐 External APIs          ⚙️ Backend Services         🗄️ Data Storage
┌─────────────────┐     ┌─────────────────────┐     ┌─────────────────┐
│ • OpenAI GPT    │────▶│   FastAPI Lambda    │────▶│   DynamoDB      │
│ • ElevenLabs    │     │                     │     │   - NewsCards   │
│ • DeepSearch    │     │ • API Routes        │     │   - Frequencies │
│ • 카카오 로그인  │     │ • Services          │     │   - Users       │
└─────────────────┘     │ • Tasks             │     │   - Bookmarks   │
                        └─────────────────────┘     └─────────────────┘
                                   │                          │
                        ┌─────────────────────┐     ┌─────────────────┐
                        │ Scheduler Lambda    │     │   S3 Storage    │
                        │ (Daily 6AM KST)     │     │   - Audio Files │
                        └─────────────────────┘     └─────────────────┘
```

### 🚀 배포 정보

- **Base URL**: `https://your-api-gateway-url/`
- **배포 도구**: AWS SAM
- **실행 환경**: AWS Lambda (Python 3.12)
- **스케줄러**: CloudWatch Events (매일 오전 6시 KST)

---

## 🔐 인증 시스템

### JWT 토큰 사용법

모든 보호된 엔드포인트는 다음과 같은 헤더가 필요합니다:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 인증 플로우

1. **카카오 로그인 시작** → `/api/auth/kakao/login`
2. **사용자 카카오 인증** → 카카오 서버
3. **콜백 처리** → `/api/auth/kakao/callback`
4. **JWT 토큰 발급** → 클라이언트에 전달
5. **API 호출 시 토큰 사용** → `Authorization` 헤더

---

## 📚 API 엔드포인트

### 🔑 1. 인증 API (`/api/auth`)

#### 1-1. 카카오 로그인 시작

```http
GET /api/auth/kakao/login
```

**설명**: 카카오 OAuth 로그인 페이지로 리다이렉트

**매개변수**: 없음

**응답**: 카카오 인증 페이지로 리다이렉트

**사용 예시**:
```javascript
// 프론트엔드에서 사용
window.location.href = 'https://api.briefly.com/api/auth/kakao/login';
```

---

#### 1-2. 카카오 로그인 콜백

```http
GET /api/auth/kakao/callback?code={authorization_code}
```

**설명**: 카카오 로그인 완료 후 JWT 토큰 발급

**매개변수**:
- `code` (query, required): 카카오에서 전달하는 인증 코드

**성공 응답** (200):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": "kakao_123456789",
  "nickname": "홍길동"
}
```

**에러 응답**:
- `400`: 인증 코드 만료/재사용
  ```json
  {
    "detail": "이 인증 코드는 이미 사용되었습니다. 다시 로그인해주세요."
  }
  ```
- `500`: 카카오 서버 연결 실패
  ```json
  {
    "detail": "카카오 서버 연결 실패"
  }
  ```

---

#### 1-3. 내 정보 조회

```http
GET /api/auth/me
Authorization: Bearer {token}
```

**설명**: 현재 로그인한 사용자 정보 조회

**응답** (200):
```json
{
  "user_id": "kakao_123456789",
  "nickname": "홍길동",
  "profile_image": "https://k.kakaocdn.net/dn/profile.jpg",
  "interests": ["정치", "경제"],
  "onboarding_completed": true,
  "created_at": "2025-01-01T00:00:00",
  "default_length": 3
}
```

**에러 응답**:
- `401`: 토큰 없음/만료
  ```json
  {
    "detail": "토큰이 필요합니다"
  }
  ```

---

#### 1-4. 로그아웃

```http
POST /api/auth/logout
Authorization: Bearer {token}
```

**설명**: 로그아웃 처리 (클라이언트에서 토큰 삭제 권장)

**응답** (200):
```json
{
  "message": "로그아웃 완료 (클라이언트 토큰 삭제 권장)"
}
```

---

### 👤 2. 사용자 API (`/api/user`)

#### 2-1. 프로필 조회

```http
GET /api/user/profile
Authorization: Bearer {token}
```

**설명**: 로그인한 사용자의 프로필 정보 조회

**응답** (200):
```json
{
  "user_id": "kakao_123456789",
  "nickname": "홍길동",
  "profile_image": "https://k.kakaocdn.net/dn/profile.jpg",
  "interests": ["정치", "경제"],
  "onboarding_completed": true,
  "default_length": 3,
  "created_at": "2025-01-01T00:00:00"
}
```

**사용 예시**:
```javascript
// 마이페이지 진입 시
const response = await fetch('/api/user/profile', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
const profile = await response.json();
```

---

#### 2-2. 프로필 수정

```http
PUT /api/user/profile
Authorization: Bearer {token}
Content-Type: application/x-www-form-urlencoded
```

**설명**: 사용자 프로필 정보 수정

**요청 바디** (form-data):
```
nickname=새닉네임&default_length=5&profile_image=https://...
```

**매개변수** (모두 선택적):
- `nickname` (string): 닉네임 (최대 20자)
- `default_length` (integer): 기본 재생 길이 (1-10분)
- `profile_image` (string): 프로필 이미지 URL

**응답** (200):
```json
{
  "message": "프로필이 업데이트되었습니다."
}
```

**사용 예시**:
```javascript
// 프로필 편집 저장
const formData = new FormData();
formData.append('nickname', '새로운닉네임');
formData.append('default_length', '5');

const response = await fetch('/api/user/profile', {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});
```

---

#### 2-3. 북마크 목록 조회

```http
GET /api/user/bookmarks
Authorization: Bearer {token}
```

**설명**: 사용자가 북마크한 뉴스 목록 조회

**응답** (200):
```json
[
  {
    "news_id": "news_12345",
    "title": "한국 경제 성장률 3% 달성",
    "category": "경제",
    "published_at": "2025-01-01T12:00:00Z",
    "content": "한국의 올해 경제 성장률이...",
    "summary": "한국 경제가 예상보다 높은 성장률을 기록했습니다.",
    "publisher": "연합뉴스",
    "url": "https://...",
    "image_url": "https://...",
    "bookmarked_at": "2025-01-01T15:30:00Z"
  }
]
```

---

#### 2-4. 내 주파수 조회

```http
GET /api/user/frequencies
Authorization: Bearer {token}
```

**설명**: 사용자 관심 카테고리별 오늘의 주파수(TTS 음성) 조회

**응답** (200):
```json
[
  {
    "frequency_id": "politics_2025-01-01",
    "category": "politics",
    "script": "안녕하세요, 오늘의 정치 뉴스를 전해드리겠습니다. 국정감사에서는...",
    "audio_url": "https://s3.amazonaws.com/briefly-news-audio/politics_2025-01-01.mp3",
    "date": "2025-01-01",
    "created_at": "2025-01-01T06:00:00Z",
    "duration": 180
  },
  {
    "frequency_id": "economy_2025-01-01",
    "category": "economy",
    "script": "경제 뉴스입니다. 오늘 증시는...",
    "audio_url": "https://s3.amazonaws.com/briefly-news-audio/economy_2025-01-01.mp3",
    "date": "2025-01-01",
    "created_at": "2025-01-01T06:00:00Z",
    "duration": 210
  }
]
```

---

#### 2-5. 관심 카테고리 조회

```http
GET /api/user/categories
Authorization: Bearer {token}
```

**응답** (200):
```json
{
  "interests": ["정치", "경제", "IT/과학"]
}
```

---

#### 2-6. 관심 카테고리 수정

```http
PUT /api/user/categories
Authorization: Bearer {token}
Content-Type: application/json
```

**요청 바디**:
```json
["정치", "경제", "스포츠"]
```

**응답** (200):
```json
{
  "message": "관심 카테고리가 업데이트되었습니다."
}
```

**에러 응답**:
- `400`: 유효하지 않은 카테고리
  ```json
  {
    "detail": "지원하지 않는 카테고리입니다: ['잘못된카테고리']"
  }
  ```

---

#### 2-7. 온보딩 완료

```http
POST /api/user/onboarding
Authorization: Bearer {token}
```

**설명**: 첫 설정 완료 플래그 설정

**응답** (200):
```json
{
  "message": "온보딩 완료"
}
```

---

#### 2-8. 온보딩 상태 확인

```http
GET /api/user/onboarding/status
Authorization: Bearer {token}
```

**응답** (200):
```json
{
  "onboarded": true
}
```

**사용 예시**:
```javascript
// 앱 진입 시 온보딩 화면 표시 여부 결정
const { onboarded } = await fetch('/api/user/onboarding/status').then(r => r.json());
if (!onboarded) {
  showOnboardingScreen();
}
```

---

### 📰 3. 뉴스 API (`/api/news`)

#### 3-1. 카테고리별 뉴스 조회

```http
GET /api/news?category={category}
```

**설명**: 특정 카테고리의 오늘 뉴스 목록 조회 (최대 10개)

**매개변수**:
- `category` (query, required): 뉴스 카테고리
  - **지원 카테고리**: "정치", "경제", "사회", "생활/문화", "세계", "IT/과학", "스포츠", "전체"

**응답** (200):
```json
[
  {
    "news_id": "news_12345",
    "category": "politics",
    "title": "국정감사 주요 이슈 정리",
    "content": "올해 국정감사에서는 다음과 같은 주요 이슈들이 다뤄졌습니다...",
    "summary": "국정감사에서 경제정책과 부동산 대책이 주요 쟁점으로 부상했습니다.",
    "published_at": "2025-01-01T12:00:00Z",
    "publisher": "연합뉴스",
    "url": "https://www.yna.co.kr/view/AKR20250101000001",
    "image_url": "https://img.yna.co.kr/photo/yna/YH/2025/01/01/thumbnail.jpg"
  }
]
```

**특별 기능 - "전체" 카테고리**:
- 모든 카테고리에서 뉴스를 균등하게 섞어서 최대 30개 반환
- 라운드로빈 방식으로 다양성 확보

**에러 응답**:
- `400`: 지원하지 않는 카테고리
  ```json
  {
    "detail": "지원하지 않는 카테고리입니다: 잘못된카테고리"
  }
  ```

**사용 예시**:
```javascript
// 정치 뉴스 조회
const politicsNews = await fetch('/api/news?category=정치').then(r => r.json());

// 전체 뉴스 조회 (다양한 카테고리 섞임)
const allNews = await fetch('/api/news?category=전체').then(r => r.json());
```

---

#### 3-2. 오늘의 뉴스 (카테고리별 그룹핑)

```http
GET /api/news/today
```

**설명**: 오늘의 뉴스를 카테고리별로 6개씩 그룹핑하여 반환

**응답** (200):
```json
{
  "정치": [
    {
      "news_id": "news_001",
      "title": "정치 뉴스 1",
      "summary": "정치 관련 요약...",
      "published_at": "2025-01-01T10:00:00Z"
    }
  ],
  "경제": [
    {
      "news_id": "news_002", 
      "title": "경제 뉴스 1",
      "summary": "경제 관련 요약...",
      "published_at": "2025-01-01T11:00:00Z"
    }
  ],
  "사회": [...],
  "생활/문화": [...],
  "세계": [...],
  "IT/과학": [...],
  "스포츠": [...]
}
```

**사용 예시**:
```javascript
// 오늘의 뉴스 탭 구현
const todayNews = await fetch('/api/news/today').then(r => r.json());
Object.entries(todayNews).forEach(([category, newsList]) => {
  renderCategorySection(category, newsList);
});
```

---

#### 3-3. 뉴스 상세 조회

```http
GET /api/news/{news_id}
```

**설명**: 개별 뉴스 상세 내용 조회

**매개변수**:
- `news_id` (path, required): 뉴스 ID

**응답** (200):
```json
{
  "news_id": "news_12345",
  "category": "politics",
  "title": "국정감사 주요 이슈 정리",
  "content": "올해 국정감사에서는 다음과 같은 주요 이슈들이 다뤄졌습니다. 첫째, 경제정책에 대한 논의가 활발했으며...",
  "summary": "AI가 생성한 뉴스 요약: 국정감사에서 경제정책과 부동산 대책이 주요 쟁점으로 부상했습니다.",
  "published_at": "2025-01-01T12:00:00Z",
  "publisher": "연합뉴스",
  "url": "https://www.yna.co.kr/view/AKR20250101000001",
  "image_url": "https://img.yna.co.kr/photo/yna/YH/2025/01/01/image.jpg",
  "category_date": "politics#2025-01-01"
}
```

**에러 응답**:
- `404`: 뉴스 없음
  ```json
  {
    "detail": "뉴스를 찾을 수 없습니다."
  }
  ```

---

#### 3-4. 북마크 추가

```http
POST /api/news/bookmark
Authorization: Bearer {token}
Content-Type: application/json
```

**요청 바디**:
```json
{
  "news_id": "news_12345"
}
```

**응답** (200):
```json
{
  "message": "북마크 완료"
}
```

**사용 예시**:
```javascript
// 뉴스 카드의 북마크 버튼 클릭
const bookmarkNews = async (newsId) => {
  await fetch('/api/news/bookmark', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ news_id: newsId })
  });
};
```

---

#### 3-5. 북마크 삭제

```http
DELETE /api/news/bookmark/{news_id}
Authorization: Bearer {token}
```

**매개변수**:
- `news_id` (path, required): 삭제할 뉴스 ID

**응답** (200):
```json
{
  "message": "북마크 삭제됨"
}
```

---

### 🎙️ 4. 주파수 API (`/api/frequencies`)

#### 4-1. 내 주파수 목록 조회

```http
GET /api/frequencies
Authorization: Bearer {token}
```

**설명**: 사용자 관심 카테고리별 오늘의 주파수(TTS 음성) 조회

**응답** (200):
```json
[
  {
    "frequency_id": "politics_2025-01-01",
    "category": "politics",
    "script": "안녕하세요, 브리플리 정치 주파수입니다. 오늘의 주요 정치 뉴스를 전해드리겠습니다. 국정감사에서는 경제정책과 부동산 대책이 주요 쟁점으로 부상했습니다...",
    "audio_url": "https://s3.amazonaws.com/briefly-news-audio/politics_2025-01-01.mp3",
    "date": "2025-01-01",
    "created_at": "2025-01-01T06:00:00Z",
    "duration": 180
  },
  {
    "frequency_id": "economy_2025-01-01",
    "category": "economy", 
    "script": "브리플리 경제 주파수입니다. 오늘 증시는 상승세를 보이며...",
    "audio_url": "https://s3.amazonaws.com/briefly-news-audio/economy_2025-01-01.mp3",
    "date": "2025-01-01",
    "created_at": "2025-01-01T06:00:00Z",
    "duration": 210
  }
]
```

**특별 기능**:
- **URL 자동 갱신**: 만료된 S3 presigned URL을 자동으로 새로 생성
- **유효성 검증**: 각 오디오 URL의 접근 가능성을 실시간 확인

**사용 예시**:
```javascript
// 내 주파수 탭 구현
const myFrequencies = await fetch('/api/frequencies', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

myFrequencies.forEach(freq => {
  createAudioPlayer(freq.audio_url, freq.script);
});
```

---

#### 4-2. 주파수 히스토리 조회

```http
GET /api/frequencies/history?limit={limit}
Authorization: Bearer {token}
```

**설명**: 사용자 관심 카테고리별 과거 주파수 히스토리 조회

**매개변수**:
- `limit` (query, optional): 조회할 개수 (기본값: 30, 최대: 100)

**응답** (200):
```json
[
  {
    "frequency_id": "politics_2024-12-31",
    "category": "politics",
    "script": "어제의 정치 뉴스 요약입니다...",
    "audio_url": "https://s3.amazonaws.com/briefly-news-audio/politics_2024-12-31.mp3",
    "date": "2024-12-31",
    "created_at": "2024-12-31T06:00:00Z",
    "duration": 165
  },
  {
    "frequency_id": "economy_2024-12-31",
    "category": "economy",
    "script": "경제 뉴스 히스토리...",
    "audio_url": "https://s3.amazonaws.com/briefly-news-audio/economy_2024-12-31.mp3", 
    "date": "2024-12-31",
    "created_at": "2024-12-31T06:00:00Z",
    "duration": 195
  }
]
```

**주의사항**:
- 오늘 날짜는 제외하고 과거 데이터만 반환
- 날짜 순으로 최신부터 정렬

**사용 예시**:
```javascript
// 히스토리 페이지네이션
const loadHistory = async (page = 1, limit = 20) => {
  const history = await fetch(`/api/frequencies/history?limit=${limit}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }).then(r => r.json());
  
  return history;
};
```

---

#### 4-3. 특정 카테고리 주파수 조회

```http
GET /api/frequencies/{category}
Authorization: Bearer {token}
```

**설명**: 특정 카테고리의 오늘 주파수 상세 정보 조회

**매개변수**:
- `category` (path, required): 카테고리명 (한글 또는 영문 모두 지원)
  - 한글: "정치", "경제", "사회", "생활/문화", "세계", "IT/과학", "스포츠"
  - 영문: "politics", "economy", "society", "lifestyle", "world", "it", "sports"

**응답** (200):
```json
{
  "frequency_id": "politics_2025-01-01",
  "category": "politics",
  "script": "브리플리 정치 주파수입니다. 오늘의 정치 뉴스를 종합해서 전해드리겠습니다. 첫 번째 소식입니다...",
  "audio_url": "https://s3.amazonaws.com/briefly-news-audio/politics_2025-01-01.mp3",
  "date": "2025-01-01",
  "created_at": "2025-01-01T06:00:00Z",
  "duration": 180,
  "news_count": 8,
  "summary_length": 1847
}
```

**에러 응답**:
- `404`: 해당 주파수 없음
  ```json
  {
    "detail": "해당 주파수가 없습니다."
  }
  ```

---

### 🏷️ 5. 카테고리 API (`/api`)

#### 5-1. 전체 카테고리 목록 조회

```http
GET /api/categories
```

**설명**: 시스템에서 지원하는 전체 카테고리 목록 조회

**응답** (200):
```json
{
  "categories": [
    "정치",
    "경제", 
    "사회",
    "생활/문화",
    "세계",
    "IT/과학",
    "스포츠"
  ]
}
```

**사용 예시**:
```javascript
// 온보딩 화면의 카테고리 선택 옵션 구성
const { categories } = await fetch('/api/categories').then(r => r.json());
categories.forEach(category => {
  createCategoryOption(category);
});
```

---

#### 5-2. 사용자 관심 카테고리 조회

```http
GET /api/user/categories
Authorization: Bearer {token}
```

**응답** (200):
```json
{
  "user_id": "kakao_123456789",
  "interests": ["정치", "경제", "IT/과학"]
}
```

---

#### 5-3. 사용자 관심 카테고리 수정

```http
PUT /api/user/categories
Authorization: Bearer {token}
Content-Type: application/json
```

**요청 바디**:
```json
{
  "interests": ["정치", "경제", "스포츠"]
}
```

**응답** (200):
```json
{
  "message": "관심 카테고리 업데이트 완료",
  "interests": ["정치", "경제", "스포츠"]
}
```

**에러 응답**:
- `400`: 유효하지 않은 카테고리
  ```json
  {
    "detail": "지원하지 않는 카테고리입니다: ['잘못된카테고리']"
  }
  ```

---

## 📊 데이터 모델

### NewsCards 테이블

```json
{
  "news_id": "news_20250101_001",           // Primary Key
  "category_date": "politics#2025-01-01",  // GSI Key
  "category": "politics",
  "title": "뉴스 제목",
  "content": "전체 기사 본문 (최대 1500자)",
  "summary": "AI 생성 요약 (800자 이내)",
  "published_at": "2025-01-01T12:00:00Z",
  "publisher": "연합뉴스",
  "url": "https://원본기사링크",
  "image_url": "https://썸네일이미지",
  "created_at": "2025-01-01T06:05:30Z"
}
```

### Frequencies 테이블

```json
{
  "frequency_id": "politics_2025-01-01",   // Primary Key (format: {category}_{date})
  "category": "politics",
  "script": "팟캐스트 대본 전체 (1800-2500자)",
  "audio_url": "https://s3.amazonaws.com/briefly-news-audio/politics_2025-01-01.mp3",
  "date": "2025-01-01",
  "created_at": "2025-01-01T06:30:00Z",
  "duration": 180,                         // 음성 길이 (초)
  "news_count": 8,                         // 요약된 뉴스 개수
  "summary_length": 1847                   // 대본 길이 (문자)
}
```

### Users 테이블

```json
{
  "user_id": "kakao_123456789",            // Primary Key
  "nickname": "홍길동",
  "profile_image": "https://k.kakaocdn.net/dn/profile.jpg",
  "interests": ["정치", "경제", "IT/과학"],
  "onboarding_completed": true,
  "default_length": 3,                     // 기본 재생 길이 (분)
  "created_at": "2025-01-01T00:00:00Z"
}
```

### Bookmarks 테이블

```json
{
  "user_id": "kakao_123456789",            // Primary Key
  "news_id": "news_20250101_001",          // Sort Key  
  "created_at": "2025-01-01T15:30:00Z"
}
```

---

## 🔧 환경변수

개발 및 배포 시 필요한 환경변수들:

```env
# AI 서비스
OPENAI_API_KEY=sk-proj-...                 # GPT-4o-mini API 키
ELEVENLABS_API_KEY=sk_...                  # ElevenLabs TTS API 키  
ELEVENLABS_VOICE_ID=TX3LPaxmHKxFdv7VOQHJ   # 음성 ID

# 뉴스 수집
DEEPSEARCH_API_KEY=...                     # DeepSearch API 키

# 소셜 로그인  
KAKAO_CLIENT_ID=...                        # 카카오 앱 클라이언트 ID
KAKAO_REDIRECT_URI=...                     # 카카오 리다이렉트 URI

# AWS 리소스
DDB_NEWS_TABLE=NewsCards                   # 뉴스 테이블명
DDB_FREQ_TABLE=Frequencies                 # 주파수 테이블명  
DDB_USERS_TABLE=Users                      # 사용자 테이블명
DDB_BOOKMARKS_TABLE=Bookmarks              # 북마크 테이블명
S3_BUCKET=briefly-news-audio               # S3 버킷명
```

---

## 🚀 개발자 가이드

### 로컬 개발 환경 설정

1. **가상환경 생성**:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. **의존성 설치**:
```bash
pip install -r requirements.txt
```

3. **환경변수 설정**:
`.env` 파일 생성 후 위의 환경변수들 설정

4. **로컬 서버 실행**:
```bash
uvicorn app.main:app --reload --port 8000
```

5. **API 문서 확인**:
`http://localhost:8000/docs`

### 테스트 실행

```bash
# 전체 테스트
cd test
python run_all_tests.py

# 개별 테스트 (Windows)
$env:PYTHONIOENCODING='utf-8'; python test_frequency_unit.py
```

### AWS 배포

```bash
# SAM 빌드
sam build

# 배포
sam deploy --guided
```

---

## 📝 에러 코드 및 처리

### HTTP 상태 코드

| 상태 코드 | 설명 | 일반적인 원인 |
|----------|------|---------------|
| 200 | 성공 | 요청 성공적으로 처리 |
| 400 | 잘못된 요청 | 매개변수 오류, 유효하지 않은 데이터 |
| 401 | 인증 실패 | JWT 토큰 없음/만료/잘못됨 |
| 403 | 권한 없음 | 접근 권한 부족 |
| 404 | 리소스 없음 | 요청한 데이터가 존재하지 않음 |
| 500 | 서버 내부 오류 | 서버 측 처리 오류 |

### 공통 에러 응답 형식

```json
{
  "detail": "구체적인 에러 메시지"
}
```

### 주요 에러 케이스

#### 인증 관련
```json
// 토큰 없음
{
  "detail": "토큰이 필요합니다"
}

// 토큰 만료
{
  "detail": "토큰이 만료되었습니다"
}

// 카카오 로그인 실패
{
  "detail": "카카오 서버 연결 실패"
}
```

#### 데이터 관련
```json
// 뉴스 없음
{
  "detail": "뉴스를 찾을 수 없습니다."
}

// 주파수 없음  
{
  "detail": "해당 주파수가 없습니다."
}

// 유효하지 않은 카테고리
{
  "detail": "지원하지 않는 카테고리입니다: 잘못된카테고리"
}
```

---

## 🎯 사용 예시

### 완전한 워크플로우 예시

```javascript
// 1. 카카오 로그인
window.location.href = '/api/auth/kakao/login';

// 2. 콜백에서 토큰 받기 (자동 처리)
const token = localStorage.getItem('access_token');

// 3. 사용자 정보 확인
const user = await fetch('/api/auth/me', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

// 4. 온보딩 체크
const { onboarded } = await fetch('/api/user/onboarding/status', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

if (!onboarded) {
  // 5. 관심 카테고리 설정
  await fetch('/api/user/categories', {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(['정치', '경제', 'IT/과학'])
  });
  
  // 6. 온보딩 완료
  await fetch('/api/user/onboarding', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });
}

// 7. 내 주파수 조회
const frequencies = await fetch('/api/frequencies', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

// 8. 오늘의 뉴스 조회
const todayNews = await fetch('/api/news/today').then(r => r.json());

// 9. 뉴스 북마크
await fetch('/api/news/bookmark', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ news_id: 'news_12345' })
});
```

---

## 📞 지원 및 문의

- **개발자**: Briefly Team
- **이슈 트래킹**: GitHub Issues
- **문서 업데이트**: 이 파일은 API 변경 시 함께 업데이트됩니다

---

## 📚 참고 링크

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [AWS Lambda Python](https://docs.aws.amazon.com/lambda/latest/dg/python-programming-model.html)
- [카카오 로그인 API](https://developers.kakao.com/docs/latest/ko/kakaologin/rest-api)
- [ElevenLabs TTS API](https://elevenlabs.io/docs/api-reference)
- [OpenAI API](https://platform.openai.com/docs)

---

*이 문서는 Briefly Backend API v1.0 기준으로 작성되었습니다. (최종 업데이트: 2025-01-14)* 