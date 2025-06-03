briefly-frontend/
├── app/                          # Next.js App Router
│   ├── layout.tsx               # 루트 레이아웃
│   ├── page.tsx                 # 홈페이지 (랭킹으로 리다이렉트)
│   ├── globals.css              # 글로벌 스타일
│   ├── ranking/page.tsx         # 랭킹 페이지
│   ├── today/page.tsx           # 오늘의 뉴스 페이지
│   ├── frequency/page.tsx       # 내 주파수 페이지
│   ├── profile/
│   │   ├── page.tsx            # 프로필 페이지
│   │   └── categories/page.tsx  # 카테고리 설정 페이지
│   ├── news/[id]/page.tsx       # 뉴스 상세 페이지
│   ├── onboarding/page.tsx      # 온보딩 페이지
│   └── auth/callback/page.tsx   # 카카오 로그인 콜백
│
├── components/                   # 재사용 가능한 컴포넌트
│   ├── ui/                      # shadcn/ui 기본 컴포넌트
│   ├── page-header.tsx          # 페이지 헤더 (로고, 로그인)
│   ├── navigation-tabs.tsx      # 하단 탭 네비게이션
│   ├── category-filter.tsx      # 카테고리 필터
│   ├── news-card.tsx           # 뉴스 카드
│   ├── news-carousel.tsx       # 뉴스 캐러셀
│   ├── audio-player.tsx        # 오디오 플레이어
│   ├── frequency-card.tsx      # 주파수 카드
│   ├── ranking-news.tsx        # 랭킹 뉴스 컴포넌트
│   ├── today-news-redesigned.tsx # 오늘의 뉴스 (리디자인)
│   ├── my-frequency.tsx        # 내 주파수 컴포넌트
│   ├── user-profile.tsx        # 사용자 프로필
│   ├── category-edit.tsx       # 카테고리 편집
│   ├── theme-toggle.tsx        # 테마 토글
│   └── logo.tsx                # 로고 컴포넌트
│
├── lib/                         # 유틸리티 및 설정
│   ├── api.ts                  # API 클라이언트
│   ├── utils.ts                # 유틸리티 함수
│   ├── constants.ts            # 상수 정의
│   ├── mock-data.ts            # 목업 데이터
│   └── toast.ts                # Toast 알림 헬퍼
│
├── types/                       # TypeScript 타입 정의
│   └── api.ts                  # API 관련 타입
│
├── public/                      # 정적 파일
│   ├── logo-light.png          # 라이트 테마 로고
│   ├── logo-dark.png           # 다크 테마 로고
│   └── diverse-avatars.png     # 아바타 이미지
│
└── 설정 파일들
    ├── next.config.mjs         # Next.js 설정
    ├── tailwind.config.ts      # Tailwind CSS 설정
    ├── package.json            # 의존성 관리
    ├── .env.local              # 환경 변수 (개발)
    ├── .env.production         # 환경 변수 (프로덕션)
    └── .env.example            # 환경 변수 예시
