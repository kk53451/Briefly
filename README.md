# 🎙️ Briefly - AI 뉴스 팟캐스트 플랫폼

**FastAPI + Next.js 기반 개인화 뉴스 요약 음성 서비스**

[![AWS](https://img.shields.io/badge/AWS-Lambda%20%7C%20DynamoDB%20%7C%20S3-orange)](https://aws.amazon.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-green)](https://openai.com/)
[![ElevenLabs](https://img.shields.io/badge/ElevenLabs-TTS-blue)](https://elevenlabs.io/)

## 📋 프로젝트 개요

Briefly는 매일 수집된 뉴스를 AI가 분석하여 개인화된 팟캐스트로 제작해주는 서비스입니다.

### ✨ 핵심 기능
- 🤖 **AI 뉴스 요약**: GPT-4o-mini로 카테고리별 뉴스 대본 생성
- 🎯 **이중 클러스터링**: 물리적 + 의미적 중복 제거로 품질 향상
- 🎵 **고품질 TTS**: ElevenLabs로 자연스러운 음성 변환
- 📱 **개인화**: 관심 카테고리 기반 맞춤형 콘텐츠
- ⏰ **자동화**: 매일 6시 자동 뉴스 수집 및 음성 생성

---

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │     Backend      │    │   External APIs │
│   (Next.js)     │◄──►│   (FastAPI)      │◄──►│                 │
│                 │    │                  │    │ • OpenAI GPT    │
│ • 반응형 UI     │    │ • AWS Lambda     │    │ • ElevenLabs    │
│ • 카카오 로그인 │    │ • DynamoDB       │    │ • DeepSearch    │
│ • 오디오 플레이어│    │ • S3 Storage     │    │ • 카카오 로그인 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

---

## 📁 프로젝트 구조

### 🎨 Frontend (Next.js 14 + TypeScript)

```
frontend/
├── app/                          # Next.js App Router
│   ├── layout.tsx               # 루트 레이아웃
│   ├── page.tsx                 # 홈페이지 (랭킹으로 리다이렉트)
│   ├── ranking/page.tsx         # 📈 랭킹 페이지
│   ├── today/page.tsx           # 📰 오늘의 뉴스 페이지
│   ├── frequency/page.tsx       # 🎙️ 내 주파수 페이지
│   ├── profile/
│   │   ├── page.tsx            # 👤 프로필 페이지
│   │   └── categories/page.tsx  # ⚙️ 카테고리 설정
│   ├── news/[id]/page.tsx       # 📄 뉴스 상세 페이지
│   ├── onboarding/page.tsx      # 🚀 온보딩 페이지
│   └── auth/callback/page.tsx   # 🔐 카카오 로그인 콜백
│
├── components/                   # 재사용 가능한 컴포넌트
│   ├── ui/                      # shadcn/ui 기본 컴포넌트
│   ├── page-header.tsx          # 🎯 페이지 헤더
│   ├── navigation-tabs.tsx      # 📍 하단 탭 네비게이션
│   ├── category-filter.tsx      # 🏷️ 카테고리 필터
│   ├── news-card.tsx           # 📰 뉴스 카드
│   ├── news-carousel.tsx       # 🎠 뉴스 캐러셀
│   ├── audio-player.tsx        # 🎵 오디오 플레이어
│   ├── frequency-card.tsx      # 📻 주파수 카드
│   └── ...
│
├── lib/                         # 유틸리티 및 설정
│   ├── api.ts                  # 🌐 API 클라이언트
│   ├── utils.ts                # 🛠️ 유틸리티 함수
│   ├── constants.ts            # 📊 상수 정의
│   └── mock-data.ts            # 🧪 목업 데이터
│
└── types/                       # TypeScript 타입 정의
    └── api.ts                  # 🔗 API 관련 타입
```

### ⚙️ Backend (FastAPI + AWS)

```
backend/
├── app/
│   ├── main.py                 # 🎯 FastAPI 메인 애플리케이션
│   ├── constants/
│   │   └── category_map.py     # 📋 카테고리 매핑 (한글↔영어)
│   ├── services/               # 🔧 핵심 서비스
│   │   ├── openai_service.py   # 🤖 GPT 요약 + 이중 클러스터링
│   │   ├── deepsearch_service.py # 📰 뉴스 수집 + 본문 추출
│   │   └── tts_service.py      # 🎵 ElevenLabs TTS 변환
│   ├── utils/                  # 🛠️ 유틸리티
│   │   ├── dynamo.py          # 🗄️ DynamoDB 연결
│   │   ├── s3.py              # 💾 S3 파일 업로드
│   │   ├── jwt_service.py     # 🔐 JWT 토큰 관리
│   │   └── date.py            # 📅 날짜 처리 (KST)
│   ├── routes/                # 🛣️ API 라우터
│   │   ├── auth.py           # 🔐 카카오 로그인
│   │   ├── user.py           # 👤 사용자 관리
│   │   ├── news.py           # 📰 뉴스 조회
│   │   ├── frequency.py      # 🎙️ 주파수 관리
│   │   └── category.py       # 🏷️ 카테고리 조회
│   └── tasks/                 # ⏰ 배치 작업
│       ├── scheduler.py       # 📅 매일 6시 스케줄러
│       ├── collect_news.py    # 📥 뉴스 수집
│       └── generate_frequency.py # 🎙️ 음성 생성
├── test/                      # 🧪 유닛 테스트 (100% 통과)
│   ├── run_all_tests.py      # 🏃 통합 테스트 실행기
│   └── test_*.py             # 📝 개별 테스트 파일
├── template.yaml             # 🏗️ AWS SAM 배포 설정
└── requirements.txt          # 📦 Python 의존성
```

---

## 🚀 API 엔드포인트

### 🔐 인증 (Authentication)
| 메서드 | 엔드포인트 | 설명 | 인증 |
|--------|------------|------|------|
| `GET` | `/api/auth/kakao/login` | 카카오 로그인 시작 | ❌ |
| `GET` | `/api/auth/kakao/callback` | 카카오 로그인 콜백 | ❌ |
| `GET` | `/api/auth/me` | 내 정보 조회 | ✅ |
| `POST` | `/api/auth/logout` | 로그아웃 | ✅ |

### 👤 사용자 관리 (User)
| 메서드 | 엔드포인트 | 설명 | 인증 |
|--------|------------|------|------|
| `GET` | `/api/user/profile` | 프로필 조회 | ✅ |
| `PUT` | `/api/user/profile` | 프로필 수정 | ✅ |
| `GET` | `/api/user/categories` | 관심 카테고리 조회 | ✅ |
| `PUT` | `/api/user/categories` | 관심 카테고리 수정 | ✅ |
| `POST` | `/api/user/onboarding` | 온보딩 완료 처리 | ✅ |
| `GET` | `/api/user/bookmarks` | 북마크 목록 | ✅ |

### 📰 뉴스 (News)
| 메서드 | 엔드포인트 | 설명 | 인증 |
|--------|------------|------|------|
| `GET` | `/api/news?category={category}` | 카테고리별 뉴스 | ❌ |
| `GET` | `/api/news/{news_id}` | 뉴스 상세 조회 | ❌ |
| `GET` | `/api/news/today/grouped` | 오늘의 카테고리별 뉴스 | ❌ |
| `POST` | `/api/news/{news_id}/bookmark` | 북마크 추가 | ✅ |
| `DELETE` | `/api/news/{news_id}/bookmark` | 북마크 제거 | ✅ |

### 🎙️ 주파수 (Frequency)
| 메서드 | 엔드포인트 | 설명 | 인증 |
|--------|------------|------|------|
| `GET` | `/api/frequency/today` | 오늘의 주파수 (카테고리별) | ❌ |
| `GET` | `/api/frequency/my` | 내 관심 카테고리 주파수 | ✅ |
| `GET` | `/api/frequency/history` | 주파수 히스토리 | ✅ |

### 🏷️ 카테고리 (Category)
| 메서드 | 엔드포인트 | 설명 | 인증 |
|--------|------------|------|------|
| `GET` | `/api/categories` | 전체 카테고리 목록 | ❌ |

---

## 🛠️ 기술 스택

### Frontend
- **Framework**: Next.js 14 (App Router)
- **언어**: TypeScript
- **스타일링**: Tailwind CSS + shadcn/ui
- **상태관리**: React Hooks
- **인증**: JWT + 카카오 로그인
- **빌드**: Vercel

### Backend
- **Framework**: FastAPI
- **언어**: Python 3.12
- **AI**: OpenAI GPT-4o-mini
- **TTS**: ElevenLabs
- **클라우드**: AWS (Lambda, DynamoDB, S3)
- **배치**: EventBridge (Cron)
- **배포**: AWS SAM

### 외부 API
- **뉴스 수집**: DeepSearch API
- **음성 변환**: ElevenLabs TTS
- **AI 요약**: OpenAI GPT-4o-mini
- **소셜 로그인**: 카카오 로그인 API

---

## 🎯 핵심 기능 상세

### 🤖 AI 뉴스 요약 시스템

**1차 클러스터링 (물리적 중복 제거)**
- 원본 기사 본문 기반
- 코사인 유사도 임계값: 0.80
- 30개 기사 → 평균 15-20개 그룹

**2차 클러스터링 (의미적 중복 제거)**  
- GPT 요약문 기반
- 코사인 유사도 임계값: 0.75
- 의미상 중복된 요약 통합

**토큰 최적화**
- 기사 본문: 3000자 → 1500자
- 클러스터링 임베딩: 1000자 제한
- 그룹 요약: 각 기사 800자 제한
- 최종 대본: 1800-2500자 (최적 길이)

### 🎵 고품질 TTS 변환

**ElevenLabs 설정**
- **모델**: multilingual-v2
- **음성**: 한국어 최적화 voice
- **품질**: mp3_44100_128 (고품질)
- **안정성**: stability=0.5, similarity_boost=0.8

### ⏰ 자동화 시스템

**매일 오전 6시 (KST) 실행**
1. 📥 뉴스 수집 (카테고리별 30개)
2. 🧹 본문 정제 및 노이즈 제거
3. 🤖 이중 클러스터링으로 중복 제거
4. 📝 GPT로 팟캐스트 대본 생성
5. 🎵 ElevenLabs로 음성 변환
6. 💾 S3에 음성 파일 업로드
7. 🗄️ DynamoDB에 메타데이터 저장

---

## 🧪 테스트 시스템

**100% 테스트 통과** ✅
- 📊 핵심 비즈니스 로직: 100% 커버리지
- 🔄 클러스터링 알고리즘 검증
- 🎯 뉴스 수집 정확도 (정확히 30개)
- 📏 대본 길이 검증 (1800-2500자)
- 🏷️ 카테고리 매핑 정확성

```bash
# 전체 테스트 실행
cd backend/test
python run_all_tests.py

# 개별 테스트 실행 (Windows)
$env:PYTHONIOENCODING='utf-8'; python test_frequency_unit.py
```

---

## 🚀 시작하기

### 1. 환경 설정

```bash
# 저장소 클론
git clone https://github.com/your-repo/Briefly.git
cd Briefly

# 백엔드 설정
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 프론트엔드 설정
cd ../frontend
npm install
```

### 2. 환경변수 설정

**백엔드** (`backend/.env`)
```env
OPENAI_API_KEY=sk-proj-...
ELEVENLABS_API_KEY=sk_...
DEEPSEARCH_API_KEY=...
KAKAO_CLIENT_ID=...
```

**프론트엔드** (`frontend/.env.local`)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_KAKAO_CLIENT_ID=...
```

### 3. 개발 서버 실행

```bash
# 백엔드 실행
cd backend
uvicorn app.main:app --reload --port 8000

# 프론트엔드 실행 (새 터미널)
cd frontend
npm run dev
```

### 4. 접속 확인
- **프론트엔드**: http://localhost:3000
- **API 문서**: http://localhost:8000/docs

---

## 📊 성능 지표

### 🎯 시스템 최적화 결과
- ✅ **뉴스 수집**: 30개 정확 수집 (기존: 34-39개 → 30개 고정)
- ✅ **카테고리**: 6개 통일 (정치, 경제, 사회, 생활/문화, IT/과학, 연예)
- ✅ **토큰 사용량**: 50% 절약 (90,000자 → 45,000자)
- ✅ **대본 품질**: 1800-2500자 범위 준수 (평균 2020자)
- ✅ **처리 시간**: 카테고리당 평균 30초

### 📈 비용 최적화
- **OpenAI API**: 토큰 사용량 50% 감소
- **ElevenLabs TTS**: 최적 길이로 비용 효율화
- **AWS Lambda**: 메모리 최적화 (512MB → 1024MB)

---

## 🔧 배포

### AWS SAM 배포
```bash
cd backend
sam build
sam deploy --guided
```

### Vercel 배포 (프론트엔드)
```bash
cd frontend
npm run build
vercel --prod
```

---

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

---

## 👥 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📞 문의

프로젝트에 대한 문의사항이나 개선 제안이 있으시면 언제든 연락주세요.

**Built with ❤️ by Briefly Team** 