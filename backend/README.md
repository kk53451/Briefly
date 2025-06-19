#  Briefly Backend

**FastAPI 기반 AI 뉴스 팟캐스트 백엔드 시스템**

---

##  개요

Briefly 백엔드는 매일 뉴스를 수집하여 AI로 요약하고 TTS로 음성을 생성하는 자동화 시스템입니다.

###  핵심 기능
-  **AI 뉴스 요약**: GPT-4o-mini + 이중 클러스터링
-  **TTS 변환**: ElevenLabs 고품질 음성 생성
-  **스케줄링**: 매일 6시 자동 실행
-  **인증**: 카카오 로그인 + JWT
-  **데이터**: DynamoDB + S3

---

##  시스템 아키텍처

```
 External APIs           Backend Services          Data Storage
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

---

## 📁 프로젝트 구조

```
backend/
├── app/
│   ├── main.py                     #  FastAPI 메인 애플리케이션
│   ├── constants/
│   │   └── category_map.py         #  카테고리 매핑 (한글↔영어)
│   ├── services/                   #  핵심 서비스
│   │   ├── openai_service.py       #  GPT 요약 + 이중 클러스터링
│   │   ├── deepsearch_service.py   # 📰 뉴스 수집 + 본문 추출
│   │   └── tts_service.py          #  ElevenLabs TTS 변환
│   ├── utils/                      # 🛠️ 유틸리티
│   │   ├── dynamo.py              #  DynamoDB 연결
│   │   ├── s3.py                  # 💾 S3 파일 업로드
│   │   ├── jwt_service.py         #  JWT 토큰 관리
│   │   └── date.py                #  날짜 처리 (KST)
│   ├── routes/                     # 🛣️ API 라우터
│   │   ├── auth.py               #  카카오 로그인
│   │   ├── user.py               # 👤 사용자 관리
│   │   ├── news.py               # 📰 뉴스 조회
│   │   ├── frequency.py          #  주파수 관리
│   │   └── category.py           # 🏷️ 카테고리 조회
│   └── tasks/                     #  배치 작업
│       ├── scheduler.py          #  매일 6시 스케줄러
│       ├── collect_news.py       # 📥 뉴스 수집
│       └── generate_frequency.py #  음성 생성
├── test/                          #  유닛 테스트 (100% 통과)
│   ├── run_all_tests.py          # 🏃 통합 테스트 실행기
│   ├── test_frequency_unit.py    #  핵심 기능 테스트
│   ├── test_clustering.py        #  클러스터링 테스트
│   └── ...                       #  기타 테스트 파일
├── template.yaml                  #  AWS SAM 배포 설정
├── requirements.txt               # 📦 Python 의존성
└── README.md                      # 📖 이 파일
```

---

##  시작하기

### 1. 환경 설정

```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경변수 설정

`.env` 파일 생성:
```env
# AI 서비스
OPENAI_API_KEY=sk-proj-...
ELEVENLABS_API_KEY=sk_...
ELEVENLABS_VOICE_ID=TX3LPaxmHKxFdv7VOQHJ

# 뉴스 수집
DEEPSEARCH_API_KEY=...

# 소셜 로그인
KAKAO_CLIENT_ID=...

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
# http://localhost:8000/docs
```

---

##  테스트 실행

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
-  **성공률**: 100% (6/6)
-  **커버리지**: 핵심 비즈니스 로직 100%
-  **실행시간**: 약 30초

---

##  주요 기능

###  AI 뉴스 요약 시스템

**이중 클러스터링 전략**
```python
# 1차: 원본 기사 물리적 중복 제거 (임계값 0.80)
groups = cluster_similar_texts(full_contents, threshold=0.80)

# 2차: GPT 요약문 의미적 중복 제거 (임계값 0.75)  
final_groups = cluster_similar_texts(summaries, threshold=0.75)
```

**토큰 최적화**
- 기사 본문: 1500자 제한
- 클러스터링 임베딩: 1000자 제한
- 그룹 요약: 각 기사 800자 제한
- 최종 대본: 1800-2500자

###  TTS 변환

**ElevenLabs 설정**
```python
voice_settings = {
    "stability": 0.5,
    "similarity_boost": 0.8,
    "style": 0.2,
    "use_speaker_boost": True
}
```

###  자동화 스케줄러

**매일 오전 6시 (KST) 실행**
1. 뉴스 수집 (카테고리별 30개)
2. 본문 정제 및 노이즈 제거
3. 이중 클러스터링으로 중복 제거
4. GPT로 팟캐스트 대본 생성
5. TTS로 음성 변환
6. S3에 음성 파일 업로드
7. DynamoDB에 메타데이터 저장

---

##  API 엔드포인트

### 인증 `/api/auth`
| 메서드 | 엔드포인트 | 설명 |
|--------|------------|------|
| `GET` | `/kakao/login` | 카카오 로그인 시작 |
| `GET` | `/kakao/callback` | 로그인 콜백 |
| `GET` | `/me` | 내 정보 조회 |
| `POST` | `/logout` | 로그아웃 |

### 사용자 `/api/user`
| 메서드 | 엔드포인트 | 설명 |
|--------|------------|------|
| `GET` | `/profile` | 프로필 조회 |
| `PUT` | `/profile` | 프로필 수정 |
| `GET` | `/categories` | 관심 카테고리 조회 |
| `PUT` | `/categories` | 관심 카테고리 수정 |
| `POST` | `/onboarding` | 온보딩 완료 |
| `GET` | `/onboarding/status` | 온보딩 상태 확인 |
| `GET` | `/bookmarks` | 북마크 목록 |
| `GET` | `/frequencies` | 내 주파수 목록 |

### 뉴스 `/api/news`
| 메서드 | 엔드포인트 | 설명 |
|--------|------------|------|
| `GET` | `/?category={category}` | 카테고리별 뉴스 |
| `GET` | `/{news_id}` | 뉴스 상세 |
| `GET` | `/today` | 오늘의 카테고리별 뉴스 |
| `POST` | `/bookmark` | 북마크 추가 |
| `DELETE` | `/bookmark/{news_id}` | 북마크 제거 |

### 주파수 `/api/frequencies`
| 메서드 | 엔드포인트 | 설명 |
|--------|------------|------|
| `GET` | `/` | 내 관심 카테고리 주파수 |
| `GET` | `/history` | 주파수 히스토리 |
| `GET` | `/{category}` | 특정 카테고리 주파수 상세 |

### 카테고리 `/api/categories`
| 메서드 | 엔드포인트 | 설명 |
|--------|------------|------|
| `GET` | `/` | 전체 카테고리 목록 |

---

##  데이터베이스 구조

### NewsCards
```json
{
  "news_id": "news_12345",
  "category_date": "politics#2025-06-03",
  "category": "politics",
  "title": "뉴스 제목",
  "content": "기사 본문",
  "published_at": "2025-06-03T12:00:00",
  "...": "..."
}
```

### Frequencies
```json
{
  "frequency_id": "politics#2025-06-03",
  "category": "politics",
  "date": "2025-06-03",
  "script": "팟캐스트 대본",
  "audio_url": "https://s3.../politics_20250603.mp3",
  "created_at": "2025-06-03T06:00:00"
}
```

### Users
```json
{
  "user_id": "kakao_1234567890",
  "nickname": "홍길동",
  "interests": ["정치", "경제"],
  "onboarding_completed": true,
  "created_at": "2025-05-01T00:00:00"
}
```

---

##  보안 고려사항

### API 키 관리
-  환경변수로 관리
-  AWS Parameter Store 연동 준비
-  현재 하드코딩 (개발 편의성)

### JWT 토큰
```python
# 토큰 생성
token = create_access_token(data={"sub": user_id})

# 토큰 검증
payload = verify_token(token)
```

### CORS 설정
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 운영시 구체적 도메인 설정 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

##  배포

### AWS SAM 배포
```bash
# 빌드
sam build

# 배포 (첫 배포)
sam deploy --guided

# 배포 (이후)
sam deploy
```

### Lambda 함수
1. **BrieflyApi**: FastAPI 메인 API 서버
2. **DailyBrieflyTask**: 매일 6시 스케줄러

### AWS 리소스
- **DynamoDB**: 4개 테이블 (NewsCards, Frequencies, Users, Bookmarks)
- **S3**: 음성 파일 저장
- **EventBridge**: Cron 스케줄링
- **IAM**: 적절한 권한 설정

---

##  성능 최적화

### 토큰 사용량 50% 절약
- **기존**: 90,000자 → **현재**: 45,000자
- **월 예상 비용**: 50% 절약

### 메모리 최적화
- **Lambda 메모리**: 1024MB (클러스터링 작업)
- **배치 처리**: 단계별 메모리 효율화

### 로깅 시스템
```python
import logging
logger = logging.getLogger(__name__)

logger.info("정보 로그")
logger.warning("경고 로그") 
logger.error("에러 로그")
```

---

##  문제 해결

### 자주 발생하는 이슈

**1. UTF-8 인코딩 오류**
```bash
# Windows PowerShell
$env:PYTHONIOENCODING='utf-8'
```

**2. API 키 오류**
```python
# .env 파일 확인
OPENAI_API_KEY=sk-proj-...
```

**3. DynamoDB 연결 오류**
```bash
# AWS 자격증명 확인
aws configure list
```

### 로그 확인
```bash
# Lambda 로그 (CloudWatch)
sam logs -n BrieflyApi --stack-name briefly-backend

# 로컬 로그
tail -f logs/app.log
```

---

##  모니터링

### 주요 지표
- **API 응답시간**: 평균 200ms 이하
- **일일 처리량**: 카테고리별 30개 기사
- **성공률**: 99% 이상
- **토큰 사용량**: 월 45,000자

### CloudWatch 메트릭
- Lambda 실행 시간
- DynamoDB 읽기/쓰기 단위
- S3 업로드 성공률
- API Gateway 호출 수

---

##  개발 가이드

### 새로운 API 추가
1. `routes/` 폴더에 라우터 파일 생성
2. `main.py`에 라우터 등록
3. 테스트 파일 작성
4. API 문서 업데이트

### 새로운 서비스 추가
1. `services/` 폴더에 서비스 파일 생성
2. 환경변수 설정
3. 유닛 테스트 작성
4. 통합 테스트에 포함

### 코딩 컨벤션
- **함수명**: snake_case
- **클래스명**: PascalCase
- **상수명**: UPPER_CASE
- **docstring**: 모든 함수에 추가
- **타입 힌트**: 가능한 모든 곳에 사용

---

## 🤝 기여하기

1. Issue 확인 및 생성
2. Feature Branch 생성
3. 코드 작성 및 테스트
4. Pull Request 생성
5. 코드 리뷰 및 머지

---

## 📞 문의

- **개발팀**: tech@briefly.com
- **이슈 리포트**: GitHub Issues
- **API 문서**: http://localhost:8000/docs

---

# Backend API Server

## 환경 변수 설정

### TTS 서비스 최적화 (NEW)

자연스러운 팟캐스트를 위한 ElevenLabs 설정:

```bash
# ElevenLabs TTS 설정
ELEVENLABS_API_KEY=your_api_key_here
ELEVENLABS_VOICE_ID=your_voice_id_here

# 권장 음성 ID (한국어 최적화):
# - kdmDKE6EkgrWrrykO9Qt (Alexandra - 자연스러운 여성 음성)
# - L0Dsvb3SLTyegXwtm47J (Archer - 친근한 남성 음성)
# - g6xIsTj2HwM6VR4iXFCw (Jessica - 표현력 풍부한 여성 음성)
```

### TTS 품질 개선 사항

1. **음성 설정 최적화 (v2 모델)**:
   - Stability: 0.65 (안정성 대폭 향상)
   - Similarity Boost: 0.8 (음성 특성 강화)
   - Style: 0.15 (자연스러운 변화 허용)
   - Speaker Boost: 활성화
   - 고품질 출력: MP3 44.1kHz 128kbps

2. **텍스트 전처리 개선**:
   - 자연스러운 감정 표현 추가
   - 호흡 패턴과 쉼 최적화
   - 숫자 읽기 개선

3. **대본 자연스러움 개선**:
   - 친근한 말투와 자연스러운 연결어
   - 감정 변화와 호흡 패턴 최적화
   - 실제 사람처럼 말하는 스타일

## 기존 설정

### OpenAI 설정
```bash
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini  # 또는 gpt-4o
```

### AWS 설정  
```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=ap-northeast-2
AWS_DYNAMODB_TABLE_NAME=briefly-news
AWS_S3_BUCKET_NAME=briefly-audio
```

### DeepSearch API
```bash
DEEPSEARCH_API_KEY=your_deepsearch_api_key
```

## 실행 방법

```bash
# 가상환경 활성화
source venv/Scripts/activate  # Windows
source venv/bin/activate      # Mac/Linux

# 의존성 설치
pip install -r requirements.txt

# 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API 문서

서버 실행 후 다음 URL에서 API 문서 확인:
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)
