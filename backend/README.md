# Briefly Backend

**FastAPI 기반 AI 뉴스 팟캐스트 자동 생성 시스템**

---

## 개요

Briefly 백엔드는 매일 자동으로 뉴스를 수집하여 AI로 요약하고 TTS로 음성을 생성하는 완전 자동화 시스템입니다.

### 핵심 기능

- **BigKinds API 뉴스 수집**: 8개 카테고리 × 70개 = 560건/일
- **AI Greedy 클러스터링**: 80% 유사도 기반 중복 제거
- **GPT-4o-mini 팟캐스트 대본 생성**: 카테고리별 특화 스타일
- **ElevenLabs TTS 변환**: 고품질 한국어 음성 생성
- **AWS Lambda 스케줄링**: 매일 오전 6시(KST) 자동 실행
- **카카오 소셜 로그인**: JWT 토큰 기반 인증
- **DynamoDB + S3**: 서버리스 데이터 저장

---

## 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                       External APIs                             │
├─────────────────────────────────────────────────────────────────┤
│  BigKinds   │  OpenAI GPT   │  ElevenLabs   │  Kakao Login    │
└─────────────┴───────────────┴───────────────┴──────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AWS Lambda Functions                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐        ┌────────────────────────┐        │
│  │  BrieflyApi      │        │  DailyBrieflyTask      │        │
│  │  (FastAPI)       │        │  (Scheduler)           │        │
│  │  - REST API      │        │  - 매일 6시 KST 실행   │        │
│  │  - 인증/인가     │        │  - 뉴스 수집           │        │
│  │  - 데이터 조회   │        │  - 주파수 생성         │        │
│  └──────────────────┘        └────────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴────────────────┐
              ▼                                ▼
┌─────────────────────────┐    ┌─────────────────────────┐
│      DynamoDB           │    │      S3 Storage         │
├─────────────────────────┤    ├─────────────────────────┤
│  • NewsCards (기사)     │    │  • MP3 오디오 파일      │
│  • Frequencies (주파수) │    │  • Presigned URL        │
│  • Users (사용자)       │    │    (7일 유효)           │
│  • Bookmarks (북마크)   │    │                         │
└─────────────────────────┘    └─────────────────────────┘
```

---

## 프로젝트 구조

```
backend/
├── app/
│   ├── main.py                         # FastAPI 메인 앱
│   │
│   ├── constants/
│   │   └── category_map.py             # 카테고리 매핑 (한글↔영어↔BigKinds)
│   │
│   ├── services/                       # 외부 API 통합
│   │   ├── bigkinds_service.py         # BigKinds API 뉴스 검색
│   │   ├── content_scraper.py          # 웹 스크래핑 (Trafilatura + BS4)
│   │   ├── openai_service.py           # GPT 요약 + Greedy 클러스터링
│   │   └── tts_service.py              # ElevenLabs TTS 변환
│   │
│   ├── routes/                         # API 라우터
│   │   ├── auth.py                     # /api/auth - 카카오 로그인
│   │   ├── user.py                     # /api/user - 사용자 관리
│   │   ├── news.py                     # /api/news - 뉴스 조회
│   │   ├── frequency.py                # /api/frequencies - 주파수 관리
│   │   └── category.py                 # /api/categories - 카테고리 조회
│   │
│   ├── tasks/                          # 배치 작업
│   │   ├── scheduler.py                # EventBridge → Lambda 트리거
│   │   ├── collect_news.py             # 뉴스 수집 (병렬 처리)
│   │   └── generate_frequency.py       # 주파수 생성 (병렬 처리)
│   │
│   └── utils/                          # 유틸리티
│       ├── dynamo.py                   # DynamoDB CRUD
│       ├── s3.py                       # S3 업로드 + Presigned URL
│       ├── jwt_service.py              # JWT 토큰 생성/검증
│       └── date.py                     # KST 날짜 처리
│
├── test/                               # 유닛 테스트
│   ├── run_all_tests.py                # 통합 테스트 실행기
│   ├── test_frequency_unit.py          # 핵심 기능 테스트
│   └── test_clustering.py              # 클러스터링 테스트
│
├── template.yaml                       # AWS SAM 배포 설정
├── requirements.txt                    # Python 의존성
└── README.md                           # 이 파일
```

---

## 시작하기

### 1. 환경 설정

```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일 또는 `template.yaml`에 다음 환경 변수 설정:

```env
# AI 서비스
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o-mini
ELEVENLABS_API_KEY=sk_...
ELEVENLABS_VOICE_ID=TX3LPaxmHKxFdv7VOQHJ

# 뉴스 수집
BIGKINDS_ACCESS_KEY=your-bigkinds-access-key

# 소셜 로그인
KAKAO_CLIENT_ID=your-kakao-client-id
KAKAO_REDIRECT_URI=https://your-domain.com/api/auth/kakao/callback

# JWT 인증
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# AWS 리소스
DDB_NEWS_TABLE=NewsCards
DDB_FREQ_TABLE=Frequencies
DDB_USERS_TABLE=Users
DDB_BOOKMARKS_TABLE=Bookmarks
S3_BUCKET=briefly-news-audio
```

### 3. 로컬 실행

```bash
# FastAPI 개발 서버 실행
uvicorn app.main:app --reload --port 8000

# API 문서 확인
# http://localhost:8000/docs (Swagger UI)
# http://localhost:8000/redoc (ReDoc)
```

---

## 테스트 실행

### 전체 테스트

```bash
cd test
python run_all_tests.py
```

### 개별 테스트 (Windows)

```bash
cd test
$env:PYTHONIOENCODING='utf-8'; python test_frequency_unit.py
$env:PYTHONIOENCODING='utf-8'; python test_clustering.py
```

### 테스트 현황

- **성공률**: 100% (6/6)
- **커버리지**: 핵심 비즈니스 로직 100%
- **실행 시간**: 약 30초

---

## 주요 기능 상세

### 1. BigKinds API 뉴스 수집

**수집 프로세스** (`app/tasks/collect_news.py`):

```python
# 8개 카테고리 병렬 처리 (ThreadPoolExecutor)
categories = ["정치", "경제", "사회", "문화", "국제", "지역", "스포츠", "IT/과학"]

# 카테고리당 200개 요청 → 70개 선별
for category in categories:
    articles = fetch_bigkinds_news(category, size=200)
    valid_articles = filter_valid_articles(articles, limit=70)
    save_to_dynamodb(valid_articles)
```

**필터링 기준**:
- ID/URL 중복 제거 (메모리 + DynamoDB)
- 본문 300자 이상
- 한글 비율 70% 이상
- 유효한 이미지 필터링 (`/` 제거)

### 2. AI Greedy 클러스터링

**클러스터링 알고리즘** (물리적 중복 제거):
```python
# 원본 기사 본문 기반 Greedy 클러스터링
# 임계값: 0.80 (80% 유사도)
groups = cluster_similar_texts(full_contents, threshold=0.80)
# 결과: 70개 → 약 10-20개 그룹
```

**작동 방식**:
- **Greedy 방식**: 각 텍스트를 순서대로 처리하며 기존 클러스터의 대표와 비교
- **코사인 유사도**: OpenAI text-embedding-3-small 기반 임베딩
- **임계값 80%**: 매우 유사한 기사만 통합 (중복 뉴스 제거)

**효과**:
- 토큰 사용량 50% 절감 (70개 → 10-20개)
- 월 비용 대폭 감소
- 대본 품질 향상 (중복 제거로 다양한 내용 포함)

### 3. GPT-4o-mini 팟캐스트 대본 생성

**카테고리별 Few-shot Learning** (`app/services/openai_service.py`):

```python
# 카테고리별 특화 스타일
category_styles = {
    "정치": "신중하고 균형잡힌",
    "경제": "전문적이지만 친근한",
    "사회": "따뜻하고 공감적인",
    "문화": "밝고 흥미진진한",
    "IT": "호기심 가득한",
    "스포츠": "열정적이고 역동적인"
}
```

**대본 생성 기준**:
- 길이: 1,800-2,200자 (음성 3-4분)
- 톤: 친근하고 자연스러운 대화체
- TTS 최적화: 자연스러운 호흡 지점, 강조 표현

### 4. ElevenLabs TTS 변환

**음성 설정** (`app/services/tts_service.py`):

```python
voice_settings = {
    "stability": 0.45,          # 자연스러운 변화 허용
    "similarity_boost": 0.85,   # 음성 특성 강화
    "style": 0.15,              # 스타일 변화
    "model_id": "eleven_multilingual_v2"
}
```

**텍스트 전처리**:
- 숫자 및 단위 표현 개선 (`30%` → `30 퍼센트`)
- 접속사 강조 (`그런데` → `그런데...`)
- 긴 문장 자동 분할 (100자 이상)

### 5. 자동화 스케줄러

**매일 오전 6시 (KST) 실행** (`app/tasks/scheduler.py`):

```python
# EventBridge cron: 0 21 * * ? * (UTC 21시 = KST 6시)

def lambda_handler(event, context):
    # 1단계: 뉴스 수집 (560건)
    collect_today_news()

    # 2단계: 주파수 생성 (8개 카테고리)
    generate_all_frequencies()
```

**병렬 처리**:
- 뉴스 수집: 8개 카테고리 동시 처리 (ThreadPoolExecutor, max_workers=5)
- 주파수 생성: 8개 카테고리 동시 처리 (ThreadPoolExecutor, max_workers=5)

---

## API 엔드포인트

### 인증 `/api/auth`

| 메서드 | 엔드포인트 | 설명 | 인증 |
|--------|------------|------|------|
| `GET` | `/kakao/login` | 카카오 로그인 URL 리다이렉트 | ❌ |
| `GET` | `/kakao/callback` | 카카오 로그인 콜백 (JWT 발급) | ❌ |
| `GET` | `/me` | 현재 로그인 사용자 정보 | ✅ |
| `POST` | `/logout` | 로그아웃 | ❌ |

### 사용자 `/api/user`

| 메서드 | 엔드포인트 | 설명 | 인증 |
|--------|------------|------|------|
| `GET` | `/profile` | 프로필 조회 | ✅ |
| `PUT` | `/profile` | 프로필 수정 | ✅ |
| `GET` | `/bookmarks` | 북마크 목록 | ✅ |
| `GET` | `/frequencies` | 내 주파수 목록 | ✅ |
| `GET` | `/categories` | 관심 카테고리 조회 | ✅ |
| `PUT` | `/categories` | 관심 카테고리 수정 | ✅ |
| `POST` | `/onboarding` | 온보딩 완료 처리 | ✅ |
| `GET` | `/onboarding/status` | 온보딩 상태 확인 | ✅ |

### 뉴스 `/api/news`

| 메서드 | 엔드포인트 | 설명 | 인증 |
|--------|------------|------|------|
| `GET` | `/?category={category}` | 카테고리별 뉴스 (최대 70개) | ❌ |
| `GET` | `/{news_id}` | 뉴스 상세 조회 | ❌ |
| `GET` | `/today` | 오늘의 카테고리별 뉴스 (6개씩, 이미지 포함) | ❌ |
| `GET` | `/home` | 홈 탭 언론사별 뉴스 (6개씩, 최신순) | ❌ |
| `POST` | `/bookmark` | 북마크 추가 | ✅ |
| `DELETE` | `/bookmark/{news_id}` | 북마크 삭제 | ✅ |

**응답 예시** (`GET /api/news/home`):

```json
{
  "연합뉴스": [
    {
      "news_id": "news_12345",
      "title": "뉴스 제목",
      "images": "https://www.bigkinds.or.kr/resources/images/...",
      "published_at": "2025-01-08T10:00:00",
      "provider": "연합뉴스"
    }
  ],
  "조선일보": [...]
}
```

### 주파수 `/api/frequencies`

| 메서드 | 엔드포인트 | 설명 | 인증 |
|--------|------------|------|------|
| `GET` | `/` | 내 관심 카테고리 주파수 (오늘) | ✅ |
| `GET` | `/history?limit=30` | 주파수 히스토리 (과거 30일) | ✅ |
| `GET` | `/{category}` | 특정 카테고리 주파수 상세 | ✅ |

**응답 예시** (`GET /api/frequencies/`):

```json
[
  {
    "frequency_id": "politics#2025-01-08",
    "category": "politics",
    "date": "2025-01-08",
    "script": "안녕하세요, 오늘도 함께해주셔서 감사합니다...",
    "audio_url": "https://s3.amazonaws.com/...?X-Amz-Expires=604800",
    "created_at": "2025-01-08T06:00:00Z"
  }
]
```

### 카테고리 `/api/categories`

| 메서드 | 엔드포인트 | 설명 | 인증 |
|--------|------------|------|------|
| `GET` | `/` | 전체 카테고리 목록 | ❌ |

**응답 예시**:

```json
{
  "categories": ["정치", "경제", "사회", "문화", "국제", "지역", "스포츠", "IT/과학"]
}
```

---

## 데이터베이스 구조

### NewsCards 테이블

```json
{
  "news_id": "news_12345",              // PK
  "category_date": "politics#2025-01-08",  // GSI
  "category": "politics",
  "rank": 1,
  "title": "뉴스 제목",
  "images": "https://www.bigkinds.or.kr/resources/images/path.jpg",
  "provider_link_page": "https://...",
  "provider": "연합뉴스",
  "byline": "홍길동 기자",
  "published_at": "2025-01-08T10:00:00",
  "hilight": "기사 하이라이트...",
  "content": "전체 본문...",
  "collected_at": "2025-01-08T06:00:00Z"
}
```

**GSI**: `category_date-index` (카테고리+날짜 기준 조회)

### Frequencies 테이블

```json
{
  "frequency_id": "politics#2025-01-08",  // PK
  "category": "politics",
  "date": "2025-01-08",
  "script": "팟캐스트 대본...",
  "audio_url": "https://s3.amazonaws.com/...?X-Amz-Expires=604800",
  "created_at": "2025-01-08T06:00:00Z"
}
```

**특징**: 모든 사용자 공유 (사용자별 생성 X)

### Users 테이블

```json
{
  "user_id": "kakao_1234567890",  // PK
  "nickname": "홍길동",
  "profile_image": "https://...",
  "interests": ["정치", "경제", "IT/과학"],
  "onboarding_completed": true,
  "created_at": "2025-01-01T00:00:00Z"
}
```

### Bookmarks 테이블

```json
{
  "user_id": "kakao_1234567890",  // PK (HASH)
  "news_id": "news_12345",        // SK (RANGE)
  "bookmarked_at": "2025-01-08T12:00:00Z"
}
```

---

## AWS SAM 배포

### 배포 명령어

```bash
# 빌드
sam build

# 첫 배포 (대화형)
sam deploy --guided

# 이후 배포
sam deploy
```

### Lambda 함수

1. **BrieflyApi**
   - 핸들러: `app.main.handler`
   - 메모리: 1024MB
   - 타임아웃: 900초 (15분)
   - 역할: FastAPI REST API 서버

2. **DailyBrieflyTask**
   - 핸들러: `app.tasks.scheduler.lambda_handler`
   - 메모리: 1024MB
   - 타임아웃: 900초 (15분)
   - 트리거: EventBridge (cron: 0 21 * * ? *)
   - 역할: 매일 6시 뉴스 수집 + 주파수 생성

### CloudWatch 로그 확인

```bash
# API 로그
sam logs -n BrieflyApi --stack-name briefly-backend --tail

# 스케줄러 로그
sam logs -n DailyBrieflyTask --stack-name briefly-backend --tail
```

---

## 성능 최적화

### 토큰 최적화 전략

| 단계 | 기존 | 최적화 | 절감률 |
|------|------|--------|--------|
| 기사 본문 | 3000자 | 1500자 | 50% |
| 클러스터링 임베딩 | 1500자 | 1000자 | 33% |
| 그룹 요약 | 제한 없음 | 800자 | - |
| 최종 대본 | 2500토큰 | 2000토큰 | 20% |

**결과**: 전체 토큰 사용량 50% 절감

### 메모리 최적화

- Lambda 메모리: 512MB → 1024MB 증가 (클러스터링 작업)
- 배치 처리: 단계별 메모리 효율화
- ThreadPoolExecutor: max_workers=5 (ElevenLabs concurrency 제한에 맞춤)

### 로깅 시스템

```python
import logging
logger = logging.getLogger(__name__)

logger.info("✅ 정보 로그")
logger.warning("⚠️ 경고 로그")
logger.error("❌ 에러 로그")
```

---

## 문제 해결

### 자주 발생하는 이슈

**1. UTF-8 인코딩 오류**

```bash
# Windows PowerShell
$env:PYTHONIOENCODING='utf-8'
```

**2. BigKinds API 타임아웃**

```python
# bigkinds_service.py에서 timeout 조정
response = httpx.post(..., timeout=30.0)  # 기본 30초
```

**3. DynamoDB 연결 오류**

```bash
# AWS 자격증명 확인
aws configure list

# 리전 확인
aws configure get region  # ap-northeast-2
```

**4. OpenAI Rate Limit 초과**

```python
# openai_service.py에서 재시도 로직 확인
# 최대 3회 재시도, temperature 점진 조정 (0.3 → 0.5 → 0.7)
```

**5. Presigned URL 만료**

```python
# frequency.py에서 URL 유효성 검증 및 재생성
# 기본 유효 기간: 7일 (604800초)
```

---

## 모니터링

### 주요 지표

- **API 응답 시간**: 평균 200ms 이하
- **일일 처리량**: 8개 카테고리 × 70개 = 560건/일
- **성공률**: 99% 이상
- **토큰 사용량**: 월 63,000자 (50% 절감 적용)

### CloudWatch 메트릭

- Lambda 실행 시간
- Lambda 메모리 사용량
- DynamoDB 읽기/쓰기 단위
- S3 업로드 성공률
- API Gateway 호출 수
- 오류율 (4xx, 5xx)

---

## 개발 가이드

### 새로운 API 엔드포인트 추가

1. `routes/` 폴더에 라우터 파일 생성
2. `main.py`에 라우터 등록:
   ```python
   from app.routes import new_route
   app.include_router(new_route.router)
   ```
3. 테스트 파일 작성
4. API 문서 업데이트

### 새로운 서비스 추가

1. `services/` 폴더에 서비스 파일 생성
2. 환경 변수 설정 (`.env` 또는 `template.yaml`)
3. 유닛 테스트 작성
4. 통합 테스트에 포함

### 코딩 컨벤션

- **함수명**: snake_case
- **클래스명**: PascalCase
- **상수명**: UPPER_CASE
- **docstring**: 모든 함수에 추가
- **타입 힌트**: 가능한 모든 곳에 사용

---

## 보안 고려사항

### API 키 관리

⚠️ **경고**: 현재 `template.yaml`에 API 키가 하드코딩되어 있습니다.

**프로덕션 배포 전 필수 조치**:

1. AWS Secrets Manager 또는 Parameter Store로 이전
2. Lambda 환경 변수에서 시크릿 참조
3. 모든 노출된 키 즉시 교체

### JWT 토큰

```python
# 토큰 생성
token = create_access_token(user_id)

# 토큰 검증
user = get_current_user(token)  # Depends를 통한 자동 검증
```

### CORS 설정

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ 운영시 구체적 도메인으로 제한 필수
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 라이선스

이 프로젝트는 비공개 프로젝트입니다.
