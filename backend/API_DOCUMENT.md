#  Briefly Backend API 문서

##  프로젝트 개요

**Briefly**는 AI 기반 뉴스 팟캐스트 백엔드 시스템으로, 매일 뉴스를 수집하여 GPT-4o-mini로 요약하고 ElevenLabs TTS로 음성을 생성하는 자동화 서비스입니다.

###  핵심 기능
-  **AI 뉴스 요약**: GPT-4o-mini + Greedy 클러스터링(80% 유사도)으로 중복 제거
-  **TTS 변환**: ElevenLabs 고품질 음성 생성
-  **스케줄링**: 매일 오전 6시(KST) 자동 실행
-  **인증**: 카카오 로그인 + JWT 토큰
-  **데이터**: AWS DynamoDB + S3 스토리지

###  **구현된 유즈케이스**
- **총 13개 핵심 유즈케이스** 구현 완료
- **UC-001~003**: 사용자 인증 및 온보딩 (3개)
- **UC-004~006**: 뉴스 조회 및 탐색 (3개)
- **UC-007~008**: 팟캐스트 및 음성 서비스 (2개)  
- **UC-009~011**: 개인화 및 설정 (3개)
- **UC-012~013**: 자동화 시스템 (2개)

###  시스템 아키텍처

```
 External APIs           Backend Services          Data Storage
┌─────────────────┐     ┌─────────────────────┐     ┌─────────────────┐
│ • OpenAI GPT    │────▶│   FastAPI Lambda    │────▶│   DynamoDB      │
│ • ElevenLabs    │     │                     │     │   - NewsCards   │
│ • BigKinds      │     │ • API Routes        │     │   - Frequencies │
│ • 카카오 로그인  │     │ • Services          │     │   - Users       │
└─────────────────┘     │ • Tasks             │     │   - Bookmarks   │
                        └─────────────────────┘     └─────────────────┘
                                   │                          │
                        ┌─────────────────────┐     ┌─────────────────┐
                        │ Scheduler Lambda    │     │   S3 Storage    │
                        │ (Daily 6AM KST)     │     │   - Audio Files │
                        └─────────────────────┘     └─────────────────┘
```

###  배포 정보

- **Base URL**: `https://your-api-gateway-url/`
- **배포 도구**: AWS SAM
- **실행 환경**: AWS Lambda (Python 3.12)
- **스케줄러**: EventBridge (매일 오전 6시 KST)

---

##  인증 시스템

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

---

#### 2-2. 북마크 목록 조회

```http
GET /api/user/bookmarks
Authorization: Bearer {token}
```

**설명**: 사용자가 북마크한 뉴스 목록 조회
- 전체 뉴스 객체에 `bookmarked_at` 필드가 추가되어 반환됨

**응답** (200):
```json
[
  {
    "news_id": "news_12345",
    "category_date": "politics#2025-01-08",
    "category": "politics",
    "rank": 1,
    "title": "뉴스 제목",
    "images": "https://www.bigkinds.or.kr/resources/images/path.jpg",
    "provider_link_page": "https://news.com/article",
    "provider": "연합뉴스",
    "byline": "홍길동 기자",
    "published_at": "2025-01-08T10:00:00",
    "hilight": "기사 하이라이트...",
    "content": "전체 본문...",
    "collected_at": "2025-01-08T06:00:00Z",
    "bookmarked_at": "2025-01-08T12:00:00Z"
  }
]
```

---

#### 2-3. 내 주파수 조회

```http
GET /api/user/frequencies
Authorization: Bearer {token}
```

**설명**: 사용자의 관심 카테고리별 공유 주파수 요약 조회 (오늘 날짜 기준)

**응답** (200):
```json
[
  {
    "frequency_id": "politics#2025-01-27",
    "category": "politics",
    "script": "오늘의 정치 뉴스 요약...",
    "audio_url": "https://s3.amazonaws.com/briefly-news-audio/politics-2025-01-27.mp3",
    "date": "2025-01-27"
  }
]
```

---

#### 2-4. 관심 카테고리 조회

```http
GET /api/user/categories
Authorization: Bearer {token}
```

**설명**: 사용자의 관심 카테고리 목록 조회

**응답** (200):
```json
{
  "interests": ["정치", "경제"]
}
```

---

#### 2-5. 관심 카테고리 수정

```http
PUT /api/user/categories
Authorization: Bearer {token}
```

**설명**: 사용자의 관심 카테고리 목록 수정

**요청 Body**:
```json
{
  "interests": ["정치", "경제", "IT/과학"]
}
```

**응답** (200):
```json
{
  "message": "관심 카테고리가 업데이트되었습니다."
}
```

---

#### 2-6. 온보딩 완료

```http
POST /api/user/onboarding
Authorization: Bearer {token}
```

**설명**: 온보딩 완료 처리

**응답** (200):
```json
{
  "message": "온보딩 완료"
}
```

---

#### 2-7. 온보딩 상태 확인

```http
GET /api/user/onboarding/status
Authorization: Bearer {token}
```

**설명**: 온보딩 완료 여부 확인

**응답** (200):
```json
{
  "onboarded": true
}
```

---

#### 2-8. 온보딩 페이지 정보

```http
GET /api/user/onboarding
Authorization: Bearer {token}
```

**설명**: 온보딩 페이지 정보 제공

**응답** (200):
```json
{
  "user_id": "kakao_123456789",
  "nickname": "홍길동",
  "onboarding_completed": false,
  "interests": []
}
```

---

### 📰 3. 뉴스 API (`/api/news`)

#### 3-1. 카테고리별 뉴스 조회

```http
GET /api/news?category={category}
```

**설명**: 특정 카테고리의 오늘 뉴스 목록 조회

**매개변수**:
- `category` (query, required): 뉴스 카테고리
  - 지원 카테고리: `정치`, `경제`, `사회`, `문화`, `국제`, `지역`, `스포츠`, `IT/과학`, `전체`

**응답** (200):
```json
[
  {
    "news_id": "news_12345",
    "category_date": "politics#2025-01-08",
    "category": "politics",
    "rank": 1,
    "title": "뉴스 제목",
    "images": "https://www.bigkinds.or.kr/resources/images/path.jpg",
    "provider_link_page": "https://news.com/article",
    "provider": "연합뉴스",
    "byline": "홍길동 기자",
    "published_at": "2025-01-08T10:00:00",
    "hilight": "기사 하이라이트 200자...",
    "content": "전체 본문...",
    "collected_at": "2025-01-08T06:00:00Z"
  }
]
```

**에러 응답**:
- `400`: 지원하지 않는 카테고리
  ```json
  {
    "detail": "지원하지 않는 카테고리입니다: 세계"
  }
  ```

---

#### 3-2. 홈 탭 - 언론사별 뉴스

```http
GET /api/news/home?date={date}
```

**설명**: 언론사별로 최신 뉴스를 그룹핑하여 반환 (Home 탭용)

**매개변수**:
- `date` (query, optional): 조회 날짜 (YYYY-MM-DD), 기본값은 오늘

**응답** (200):
```json
{
  "연합뉴스": [
    {
      "news_id": "news_123",
      "category_date": "politics#2025-01-08",
      "category": "politics",
      "rank": 1,
      "title": "뉴스 제목",
      "images": "https://www.bigkinds.or.kr/resources/images/path.jpg",
      "provider_link_page": "https://news.com/article",
      "provider": "연합뉴스",
      "byline": "홍길동 기자",
      "published_at": "2025-01-08T15:30:00",
      "hilight": "기사 하이라이트...",
      "content": "전체 본문...",
      "collected_at": "2025-01-08T06:00:00Z"
    }
  ],
  "조선일보": [
    {
      "news_id": "news_456",
      "category_date": "economy#2025-01-08",
      "category": "economy",
      "rank": 2,
      "title": "뉴스 제목 2",
      "images": "",
      "provider_link_page": "https://news2.com/article",
      "provider": "조선일보",
      "byline": "김철수 기자",
      "published_at": "2025-01-08T14:20:00",
      "hilight": "경제 기사 하이라이트...",
      "content": "전체 경제 본문...",
      "collected_at": "2025-01-08T06:00:00Z"
    }
  ]
}
```

---

#### 3-3. 오늘의 뉴스 그룹핑

```http
GET /api/news/today
```

**설명**: 오늘의 뉴스를 카테고리별로 그룹핑하여 반환 (Today 탭용)
- 각 카테고리별로 이미지가 있는 기사 6개씩 반환

**응답** (200):
```json
{
  "정치": [
    {
      "news_id": "news_12345",
      "category_date": "politics#2025-01-08",
      "category": "politics",
      "rank": 1,
      "title": "정치 뉴스 제목",
      "images": "https://www.bigkinds.or.kr/resources/images/path1.jpg",
      "provider_link_page": "https://news.com/article",
      "provider": "연합뉴스",
      "byline": "홍길동 기자",
      "published_at": "2025-01-08T10:00:00",
      "hilight": "기사 하이라이트...",
      "content": "전체 본문...",
      "collected_at": "2025-01-08T06:00:00Z"
    }
  ],
  "경제": [
    {
      "news_id": "news_67890",
      "category_date": "economy#2025-01-08",
      "category": "economy",
      "rank": 2,
      "title": "경제 뉴스 제목",
      "images": "https://www.bigkinds.or.kr/resources/images/path2.jpg",
      "provider_link_page": "https://news.com/article2",
      "provider": "조선일보",
      "byline": "김철수 기자",
      "published_at": "2025-01-08T09:30:00",
      "hilight": "경제 뉴스 하이라이트...",
      "content": "전체 본문...",
      "collected_at": "2025-01-08T06:00:00Z"
    }
  ]
}
```

---

#### 3-4. 뉴스 상세 조회

```http
GET /api/news/{news_id}
```

**설명**: 개별 뉴스 카드 상세 내용 조회

**응답** (200):
```json
{
  "news_id": "news_12345",
  "category_date": "politics#2025-01-08",
  "category": "politics",
  "rank": 1,
  "title": "뉴스 제목",
  "images": "https://www.bigkinds.or.kr/resources/images/path.jpg",
  "provider_link_page": "https://news.com/article",
  "provider": "연합뉴스",
  "byline": "홍길동 기자",
  "published_at": "2025-01-08T10:00:00",
  "hilight": "기사 하이라이트 200자...",
  "content": "뉴스 본문 전체...",
  "collected_at": "2025-01-08T06:00:00Z"
}
```

**에러 응답**:
- `404`: 뉴스를 찾을 수 없음
  ```json
  {
    "detail": "뉴스를 찾을 수 없습니다."
  }
  ```

---

#### 3-5. 뉴스 북마크 추가

```http
POST /api/news/bookmark
Authorization: Bearer {token}
```

**설명**: 뉴스 북마크 추가

**요청 Body**:
```json
{
  "news_id": "news_123"
}
```

**응답** (200):
```json
{
  "message": "북마크 완료"
}
```

---

#### 3-6. 뉴스 북마크 삭제

```http
DELETE /api/news/bookmark/{news_id}
Authorization: Bearer {token}
```

**설명**: 뉴스 북마크 삭제

**응답** (200):
```json
{
  "message": "북마크 삭제됨"
}
```

---

###  4. 주파수 API (`/api/frequencies`)

#### 4-1. 내 주파수 목록

```http
GET /api/frequencies
Authorization: Bearer {token}
```

**설명**: 사용자의 관심 카테고리별 공유 주파수 목록 (오늘 날짜 기준)

**응답** (200):
```json
[
  {
    "frequency_id": "politics#2025-01-27",
    "category": "politics",
    "script": "오늘의 정치 뉴스 요약...",
    "audio_url": "https://s3.amazonaws.com/briefly-news-audio/politics-2025-01-27.mp3",
    "date": "2025-01-27",
    "created_at": "2025-01-27T06:30:00"
  }
]
```

---

#### 4-2. 주파수 히스토리

```http
GET /api/frequencies/history?limit={limit}
Authorization: Bearer {token}
```

**설명**: 사용자의 관심 카테고리별 주파수 히스토리 (과거 데이터)

**매개변수**:
- `limit` (query, optional): 조회할 개수 (기본값: 30, 최대: 100)

**응답** (200):
```json
[
  {
    "frequency_id": "politics#2025-01-26",
    "category": "politics",
    "script": "어제의 정치 뉴스 요약...",
    "audio_url": "https://s3.amazonaws.com/briefly-news-audio/politics-2025-01-26.mp3",
    "date": "2025-01-26",
    "created_at": "2025-01-26T06:30:00"
  }
]
```

---

#### 4-3. 카테고리별 주파수 상세

```http
GET /api/frequencies/{category}
Authorization: Bearer {token}
```

**설명**: 특정 카테고리의 주파수 상세 정보 조회

**응답** (200):
```json
{
  "frequency_id": "politics#2025-01-27",
  "category": "politics",
  "script": "오늘의 정치 뉴스 요약...",
  "audio_url": "https://s3.amazonaws.com/briefly-news-audio/politics-2025-01-27.mp3",
  "date": "2025-01-27",
  "created_at": "2025-01-27T06:30:00"
}
```

**에러 응답**:
- `404`: 해당 주파수가 없음
  ```json
  {
    "detail": "해당 주파수가 없습니다."
  }
  ```

---

### 📂 5. 카테고리 API (`/api`)

#### 5-1. 전체 카테고리 목록

```http
GET /api/categories
```

**설명**: 전체 카테고리 목록 반환 (인증 불필요)

**응답** (200):
```json
{
  "categories": ["정치", "경제", "사회", "문화", "국제", "지역", "스포츠", "IT/과학"]
}
```

---

#### 5-2. 사용자 카테고리 조회

```http
GET /api/user/categories
Authorization: Bearer {token}
```

**설명**: 로그인된 사용자의 관심 카테고리 조회

**응답** (200):
```json
{
  "user_id": "kakao_123456789",
  "interests": ["정치", "경제"]
}
```

---

#### 5-3. 사용자 카테고리 수정

```http
PUT /api/user/categories
Authorization: Bearer {token}
```

**설명**: 로그인된 사용자의 관심 카테고리 수정

**요청 Body**:
```json
{
  "interests": ["정치", "경제", "IT/과학"]
}
```

**응답** (200):
```json
{
  "message": "관심 카테고리 업데이트 완료",
  "interests": ["정치", "경제", "IT/과학"]
}
```

**에러 응답**:
- `400`: 잘못된 카테고리
  ```json
  {
    "detail": "지원하지 않는 카테고리입니다: ['세계']"
  }
  ```

---

###  6. 기타 엔드포인트

#### 6-1. 루트 헬스체크

```http
GET /
```

**설명**: API 서버 상태 확인

**응답** (200):
```json
{
  "message": "Welcome to Briefly API"
}
```

---

#### 6-2. 온보딩 페이지 정보

```http
GET /onboarding
```

**설명**: 온보딩 페이지 정보 제공 (인증 불필요)

**응답** (200):
```json
{
  "message": "온보딩 페이지입니다",
  "available_categories": ["정치", "경제", "사회", "문화", "국제", "지역", "스포츠", "IT/과학"]
}
```

---

##  공통 에러 응답

### 인증 에러
- `401 Unauthorized`: JWT 토큰 없음/만료
- `403 Forbidden`: 권한 없음

### 요청 에러
- `400 Bad Request`: 잘못된 요청 파라미터
- `404 Not Found`: 리소스를 찾을 수 없음
- `422 Validation Error`: 요청 형식 오류

### 서버 에러
- `500 Internal Server Error`: 서버 내부 오류

---

##  API 사용 예시

### 1. 사용자 인증 플로우
```javascript
// 1. 카카오 로그인
window.location.href = '/api/auth/kakao/login';

// 2. 콜백에서 토큰 받기
const response = await fetch('/api/auth/kakao/callback?code=AUTH_CODE');
const { access_token } = await response.json();

// 3. 토큰으로 API 호출
const userInfo = await fetch('/api/auth/me', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
```

### 2. 뉴스 조회 플로우
```javascript
// 1. 전체 뉴스 조회
const allNews = await fetch('/api/news?category=전체');

// 2. 특정 카테고리 뉴스
const politicsNews = await fetch('/api/news?category=정치');

// 3. 뉴스 상세 조회
const newsDetail = await fetch('/api/news/news_123');
```

### 3. 주파수 조회 플로우
```javascript
// 1. 내 관심 주파수 조회
const myFrequencies = await fetch('/api/frequencies', {
  headers: { 'Authorization': `Bearer ${token}` }
});

// 2. 주파수 히스토리 조회
const history = await fetch('/api/frequencies/history?limit=10', {
  headers: { 'Authorization': `Bearer ${token}` }
});
```

---

##  환경 변수

```bash
# 카카오 로그인
KAKAO_CLIENT_ID=your_kakao_client_id
KAKAO_REDIRECT_URI=your_redirect_uri

# AI 서비스
OPENAI_API_KEY=your_openai_key
ELEVENLABS_API_KEY=your_elevenlabs_key
ELEVENLABS_VOICE_ID=your_voice_id

# 뉴스 API (BigKinds)
BIGKINDS_ACCESS_KEY=your_bigkinds_key

# AWS 리소스
DDB_NEWS_TABLE=NewsCards
DDB_FREQ_TABLE=Frequencies
DDB_USERS_TABLE=Users
DDB_BOOKMARKS_TABLE=Bookmarks
S3_BUCKET=briefly-news-audio
```

---

##  개발 로드맵

###  완료된 기능
- 카카오 로그인 및 JWT 인증
- 뉴스 수집 및 요약 시스템
- TTS 음성 변환 및 S3 저장
- 사용자 프로필 및 북마크 관리
- 주파수 생성 및 조회

###  향후 확장 가능 기능
- 푸시 알림 시스템
- 뉴스 검색 기능  
- 음성 재생 분석
- 실시간 뉴스 스트리밍

---