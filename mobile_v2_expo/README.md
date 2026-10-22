# Briefly Mobile (v2 — Expo Router + Supabase)

"Warm editorial" 에디션. AI가 큐레이션한 오늘의 뉴스를 팟캐스트로 듣는 앱.

## Stack

- **Expo SDK 54 (New Architecture)** + **Expo Router**
- **Supabase** — Postgres + Auth + Storage (`briefly-audio` public bucket)
- **expo-av** — 팟캐스트 오디오 재생
- **@expo-google-fonts/noto-serif-kr** + **jetbrains-mono** — 에디토리얼 타이포
- **TypeScript strict**

## Structure

```
app/                        ← Expo Router (file-based)
├── _layout.tsx            Root: fonts, SafeArea, splash
├── index.tsx              Session gate → (auth) or (tabs)
├── (auth)/
│   ├── login.tsx          마스트헤드 + Kakao OAuth
│   └── onboarding.tsx     6-카테고리 그리드
├── (tabs)/
│   ├── today.tsx          AM/PM 토글 + 스와이프 카드
│   ├── home.tsx           카테고리 탭 + 리드 + 리스트
│   ├── podcast.tsx        오디오 플레이어 + 재생목록
│   └── profile.tsx
└── news/[id].tsx          뉴스 상세

src/
├── theme/      디자인 토큰 (tokens.ts) + 카테고리 맵 (categories.ts)
├── lib/        supabase 클라이언트, date 유틸
├── hooks/      useAuth / useHeadlines / useNewsCards / usePodcast / useProfile / usePodcastPlayer / useHeadlineTicker
├── components/ BrieflyMark / CatBadge / Placeholder / Screen / Divider / AppText
└── types/      Supabase row 타입
```

## Setup

### 1. `.env` 생성

`.env.example` 복사 후 Supabase Dashboard → Project Settings → API 에서 값 채우기.

```bash
EXPO_PUBLIC_SUPABASE_URL=https://<project-ref>.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOi...
EXPO_PUBLIC_SUPABASE_AUDIO_BUCKET=briefly-audio
```

### 2. 의존성 설치

```bash
npm install
```

### 3. Supabase Kakao OAuth 활성화

Supabase Dashboard → Authentication → Providers → Kakao 에서 Client ID / Secret 입력.
Redirect URL 은 `briefly://auth-callback` (app.config.js 의 `scheme` 과 일치).

Kakao Developers 쪽 redirect URI 도 동일하게 등록해야 함.

### 4. 실행

```bash
npm start
```

## 백엔드 연동

이 앱은 별도 REST API 없이 **Supabase 에 직접** 붙습니다 (backend_v2_supabase 는 cron 배치 파이프라인 전용).

| 화면 | 테이블 | 키 |
| ---- | ------ | --- |
| Today | `headlines` | `(date, slot)` → `items[]` jsonb |
| Home | `news_cards` | `(date, category, rank)` |
| 뉴스 상세 | `news_cards` | `news_id` |
| Podcast | `podcasts` + Storage | `(date, slot)` + `audio_path` |
| Profile | `profiles` | `id = auth.uid()` |

RLS: content 테이블은 anon read 허용, `profiles`/`bookmarks` 는 본인만.

## 카테고리

6개 (v1): 정치 · 경제 · 사회 · 문화 · 국제 · IT/과학.
지역/스포츠는 파이프라인 미지원으로 제외.

## 폰트 주의

- **Noto Serif KR** / **JetBrains Mono**: `@expo-google-fonts/*` 로 런타임 로드됨.
- **Pretendard**: Google Fonts 미제공 → 시스템 한국어 sans 로 폴백. 원하면 `assets/fonts/` 에 Pretendard 파일 드롭 후 `expo-font` 로 로드하고 `src/theme/tokens.ts` 의 `fontFamily.sans` 업데이트.

## TODO (후속)

- 다크 모드 (지금은 라이트 전용)
- 북마크 CRUD 화면
- 미니 플레이어 (탭 이동 중에도 하단 유지)
- 토픽 상세 화면 (투데이 카드 → 관련 기사 클러스터)
- Pretendard 폰트 번들링
