# Briefly Mobile - React Native App

**매일 업데이트되는 개인화 AI 뉴스 팟캐스트 서비스**

React Native (Expo)로 구현된 Briefly 모바일 애플리케이션입니다.

## 주요 기능

### 🎯 사용자 인증
- **카카오 소셜 로그인**: 간편한 소셜 로그인 지원
- **온보딩 프로세스**: 첫 사용자를 위한 카테고리 선택

### 📰 뉴스 서비스
- **오늘의 뉴스**: 카테고리별 최신 뉴스 조회
- **인기 뉴스 랭킹**: 조회수 기반 인기 뉴스
- **뉴스 상세 보기**: 전체 기사 내용 및 원문 링크
- **북마크 기능**: 관심 뉴스 저장 및 관리

### 🎙️ 팟캐스트 플레이어
- **뮤직 플레이어 스타일 UI**: 직관적이고 아름다운 인터페이스
- **백그라운드 재생**: 앱을 벗어나도 계속 재생
- **재생 컨트롤**: 재생/일시정지, 15초 앞뒤 이동
- **프로그레스 바**: 실시간 재생 위치 표시 및 탐색

### 👤 프로필 관리
- **관심 카테고리 설정**: 개인화된 뉴스 큐레이션
- **사용자 정보**: 프로필 및 계정 정보 관리

## 기술 스택

- **Framework**: React Native (Expo SDK 52+)
- **Language**: TypeScript
- **Navigation**: React Navigation 6
- **Audio Player**: Expo AV
- **State Management**: React Context API
- **HTTP Client**: Axios
- **Storage**: AsyncStorage
- **UI Components**: Custom components with themed design

## 프로젝트 구조

```
mobile/
├── src/
│   ├── components/           # 재사용 가능한 UI 컴포넌트
│   │   ├── Button.tsx       # 버튼 컴포넌트
│   │   ├── Card.tsx         # 카드 컴포넌트
│   │   ├── NewsCard.tsx     # 뉴스 카드
│   │   └── MusicPlayer.tsx  # 음악 플레이어 UI
│   │
│   ├── screens/             # 화면 컴포넌트
│   │   ├── LoginScreen.tsx
│   │   ├── OnboardingScreen.tsx
│   │   ├── TodayScreen.tsx
│   │   ├── RankingScreen.tsx
│   │   ├── PodcastScreen.tsx
│   │   ├── ProfileScreen.tsx
│   │   ├── NewsDetailScreen.tsx
│   │   └── CategoriesScreen.tsx
│   │
│   ├── navigation/          # 네비게이션 설정
│   │   ├── RootNavigator.tsx
│   │   ├── AuthNavigator.tsx
│   │   ├── MainNavigator.tsx
│   │   └── types.ts
│   │
│   ├── contexts/            # React Context
│   │   ├── AuthContext.tsx
│   │   └── AudioPlayerContext.tsx
│   │
│   ├── services/            # API 및 서비스
│   │   ├── api.ts          # REST API 클라이언트
│   │   ├── storage.ts      # AsyncStorage 래퍼
│   │   └── audioPlayer.ts  # 오디오 플레이어 서비스
│   │
│   ├── types/               # TypeScript 타입 정의
│   │   └── api.ts
│   │
│   └── constants/           # 상수 및 테마
│       ├── categories.ts
│       └── theme.ts
│
├── App.tsx                  # 앱 엔트리 포인트
├── app.json                 # Expo 설정
└── package.json             # 의존성 관리
```

## 설치 및 실행

### 1. 의존성 설치

```bash
cd mobile
npm install
```

### 2. 개발 서버 실행

```bash
# iOS 시뮬레이터
npm run ios

# Android 에뮬레이터
npm run android

# Expo Go 앱으로 실행
npm start
```

### 3. 환경 변수 설정

`src/services/api.ts` 파일에서 API URL을 설정하세요:

```typescript
const API_BASE_URL = "http://your-backend-url:8000";
```

## 디자인 특징

### 다크 테마
- 모던하고 눈이 편한 다크 모드 디자인
- 일관된 색상 시스템 (Primary: #6366f1, Secondary: #ec4899)
- 계층적 배경색 구조

### 뮤직 플레이어 스타일 팟캐스트 UI
- **앨범 아트 스타일 카테고리 표시**: 그라데이션 배경과 아이콘
- **대형 플레이 버튼**: 직관적인 재생 컨트롤
- **프로그레스 슬라이더**: 부드러운 탐색 기능
- **15초 스킵 버튼**: 효율적인 콘텐츠 소비

### 반응형 레이아웃
- 모바일 환경에 최적화된 터치 인터페이스
- Safe Area 지원으로 노치/홈 버튼 영역 고려
- 스크롤 가능한 긴 콘텐츠 지원

## 주요 기능 상세

### 백그라운드 오디오 재생
- iOS에서 백그라운드 오디오 모드 활성화
- Android에서 포그라운드 서비스 권한 설정
- 잠금 화면에서도 재생 컨트롤 가능

### 카카오 로그인 플로우
1. 로그인 버튼 클릭
2. WebBrowser로 카카오 인증 페이지 오픈
3. 사용자 인증 후 콜백 URL로 리다이렉트
4. Deep Link로 앱에서 코드 수신
5. 백엔드 API를 통해 토큰 교환
6. AsyncStorage에 토큰 저장

### 상태 관리
- **AuthContext**: 사용자 인증 상태 및 프로필 관리
- **AudioPlayerContext**: 오디오 재생 상태 및 컨트롤

## API 연동

백엔드 API와 연동하여 다음 기능을 제공합니다:

- `GET /api/news/today`: 오늘의 뉴스 조회
- `GET /api/frequencies`: 사용자 맞춤 팟캐스트 조회
- `POST /api/news/bookmark`: 뉴스 북마크 추가/제거
- `PUT /api/user/categories`: 관심 카테고리 업데이트
- `GET /api/auth/me`: 현재 사용자 정보 조회

## 빌드 및 배포

### iOS 빌드

```bash
eas build --platform ios
```

### Android 빌드

```bash
eas build --platform android
```

## 개발 가이드

### 새로운 화면 추가
1. `src/screens/` 에 화면 컴포넌트 생성
2. `src/navigation/types.ts` 에 라우트 타입 추가
3. 네비게이터에 화면 등록

### 새로운 API 엔드포인트 추가
1. `src/types/api.ts` 에 타입 정의
2. `src/services/api.ts` 에 메서드 구현

### 테마 커스터마이징
`src/constants/theme.ts` 파일에서 색상, 간격, 폰트 크기 등을 수정할 수 있습니다.

## 라이센스

MIT License

---

**Briefly Mobile App** - AI 기반 뉴스 팟캐스트 플랫폼 🎙️
