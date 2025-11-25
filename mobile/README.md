# Briefly Mobile App

AI 기반 뉴스 팟캐스트 플랫폼 - React Native Expo 앱

## 개요

Briefly는 AI가 자동으로 뉴스를 수집, 요약하고 오디오 팟캐스트로 제공하는 모바일 애플리케이션입니다.

### 주요 기능

- **카카오 로그인**: 간편한 소셜 로그인
- **개인화 온보딩**: 관심 카테고리 선택
- **홈 탭**: 언론사별 최신 뉴스 피드
- **투데이 탭**: 카테고리별 큐레이션 뉴스
- **팟캐스트 플레이어**: 2가지 스타일(미니멀/상세) 전환 가능
- **백그라운드 재생**: 앱을 닫아도 팟캐스트 계속 재생
- **다크/라이트 테마**: 자동 전환 또는 수동 설정
- **북마크 기능**: 관심있는 뉴스 저장

## 기술 스택

- **프레임워크**: React Native (Expo SDK 54)
- **언어**: TypeScript
- **네비게이션**: React Navigation (Stack + Bottom Tabs)
- **오디오**: Expo AV (백그라운드 재생 지원)
- **상태관리**: Context API
- **스타일링**: StyleSheet (테마 시스템)
- **API 통신**: Axios
- **로컬 저장소**: AsyncStorage

## 프로젝트 구조

```
mobile/
├── src/
│   ├── components/          # 재사용 가능한 컴포넌트
│   │   └── NewsImage.tsx    # 이미지 placeholder 컴포넌트
│   ├── constants/           # 상수 정의
│   │   ├── theme.ts         # 색상, 타이포그래피, 간격
│   │   └── categories.ts    # 카테고리 정의
│   ├── contexts/            # React Context
│   │   ├── ThemeContext.tsx
│   │   ├── AuthContext.tsx
│   │   └── AudioPlayerContext.tsx
│   ├── navigation/          # 네비게이션 구조
│   │   ├── RootNavigator.tsx   # 루트 (인증 플로우)
│   │   └── MainNavigator.tsx   # 메인 탭
│   ├── screens/             # 화면 컴포넌트
│   │   ├── LoginScreen.tsx
│   │   ├── OnboardingScreen.tsx
│   │   ├── HomeScreen.tsx
│   │   ├── TodayScreen.tsx
│   │   ├── PodcastScreen.tsx
│   │   └── ProfileScreen.tsx
│   ├── services/            # API 클라이언트
│   │   └── api.ts
│   ├── types/               # TypeScript 타입
│   │   ├── api.ts
│   │   └── navigation.ts
│   └── assets/              # 이미지, 폰트 등
├── App.tsx                  # 엔트리 포인트
├── app.json                 # Expo 설정
└── package.json
```

## 시작하기

### 사전 요구사항

- Node.js 18+
- npm 또는 yarn
- Expo Go 앱 (테스트용) 또는 Android Studio / Xcode

### 설치

```bash
cd mobile
npm install
```

### 환경 변수 설정

`mobile/.env` 파일 생성 (필요 시):

```bash
# 현재는 api.ts에서 직접 설정
# 운영 환경에서는 환경 변수 사용 권장
API_BASE_URL=https://your-api-gateway-url.amazonaws.com
KAKAO_CLIENT_ID=your_kakao_client_id
```

### 개발 서버 실행

```bash
# Expo 개발 서버 시작
npm start

# Android 에뮬레이터
npm run android

# iOS 시뮬레이터 (Mac만 가능)
npm run ios

# 웹 브라우저
npm run web
```

### Expo Go로 테스트

1. 스마트폰에 Expo Go 앱 설치
2. `npm start` 실행 후 나타나는 QR 코드 스캔
3. 앱이 자동으로 실행됨

## 주요 화면 설명

### 1. 로그인 화면 (`LoginScreen`)

- 카카오 OAuth 인증
- 그라디언트 배경에 로고 표시
- 첫 진입 시 자동으로 표시

### 2. 온보딩 화면 (`OnboardingScreen`)

- 8개 카테고리 중 관심사 선택
- 최소 1개 이상 선택 필수
- 선택 완료 후 메인 화면 진입

### 3. 홈 탭 (`HomeScreen`)

- 언론사별로 그룹핑된 최신 뉴스
- API: `GET /api/news/home`
- Pull-to-refresh 지원

### 4. 투데이 탭 (`TodayScreen`)

- 카테고리별 큐레이션 뉴스
- API: `GET /api/news/today`
- 각 카테고리당 6개 뉴스 표시

### 5. 팟캐스트 탭 (`PodcastScreen`)

**2가지 플레이어 스타일:**

- **미니멀 스타일**: 큰 앨범 아트, 단순한 컨트롤
- **상세 스타일**: 스크립트 미리보기, 재생목록, 고급 컨트롤

**기능:**
- 재생/일시정지
- 15초 앞/뒤로 이동
- 재생 속도 조절 (1x, 1.5x)
- 반복 재생
- 백그라운드 재생

### 6. 프로필 탭 (`ProfileScreen`)

- 사용자 정보 표시
- 관심 카테고리 관리
- 북마크 통계
- 다크/라이트 테마 토글
- 로그아웃

## 테마 시스템

### 색상 팔레트

로고의 푸른색 (#3B82F6)을 메인 컬러로 사용:

```typescript
Colors.light = {
  primary: '#3B82F6',
  background: '#FFFFFF',
  text: '#0F172A',
  // ...
}

Colors.dark = {
  primary: '#60A5FA',
  background: '#0F172A',
  text: '#F8FAFC',
  // ...
}
```

### 사용법

```typescript
import { useTheme } from '../contexts/ThemeContext';

const { colors, activeTheme, toggleTheme } = useTheme();

<View style={{ backgroundColor: colors.background }}>
  <Text style={{ color: colors.text }}>Hello</Text>
</View>
```

## API 통신

### API 클라이언트 사용

```typescript
import { apiClient } from '../services/api';

// 뉴스 목록 가져오기
const news = await apiClient.getTodayNews();

// 북마크 추가
await apiClient.addBookmark(newsId);

// 사용자 프로필 업데이트
await apiClient.updateProfile({ nickname: '새이름' });
```

### 인증 토큰 자동 추가

API 클라이언트는 자동으로 JWT 토큰을 요청 헤더에 추가합니다.

```typescript
// 토큰은 AuthContext에서 자동 관리
const { user, login, logout } = useAuth();
```

## 오디오 재생

### AudioPlayer Context 사용

```typescript
import { useAudioPlayer } from '../contexts/AudioPlayerContext';

const {
  currentTrack,
  isPlaying,
  play,
  pause,
  resume,
  skipForward,
  skipBackward,
  setPlaybackRate,
} = useAudioPlayer();

// 팟캐스트 재생
await play(frequencyItem);

// 15초 앞으로
await skipForward(15);

// 재생 속도 변경
await setPlaybackRate(1.5);
```

### 백그라운드 재생

iOS와 Android 모두 백그라운드 재생을 지원하도록 설정되어 있습니다:

- iOS: `UIBackgroundModes: ["audio"]`
- Android: `FOREGROUND_SERVICE`, `WAKE_LOCK` 권한

## 이미지 Placeholder

이미지 URL이 없거나 로드 실패 시 자동으로 그라디언트 placeholder 표시:

```typescript
import { NewsImage } from '../components/NewsImage';

<NewsImage uri={news.image_url} style={styles.image} />
```

## 빌드 및 배포

### Android APK 빌드

```bash
# EAS Build 사용 (권장)
npm install -g eas-cli
eas build --platform android

# 로컬 빌드
npm run build:android
```

### iOS 빌드 (Mac 필요)

```bash
eas build --platform ios
```

### 앱 스토어 배포

1. EAS Submit 사용:
```bash
eas submit --platform android
eas submit --platform ios
```

2. 수동 배포:
- Android: Google Play Console에 APK/AAB 업로드
- iOS: App Store Connect에 IPA 업로드

## 주의사항

### 현재 구현되지 않은 기능

- [ ] 뉴스 상세 화면 (WebView 필요)
- [ ] 북마크 목록 화면
- [ ] 카테고리 수정 화면
- [ ] 검색 기능
- [ ] 푸시 알림
- [ ] 오프라인 모드
- [ ] 공유 기능

### 카카오 로그인 설정

실제 배포 시 다음 설정이 필요합니다:

1. Kakao Developers에서 앱 등록
2. Redirect URI 설정: `briefly://auth/callback`
3. `LoginScreen.tsx`의 `KAKAO_CLIENT_ID` 수정

### API Base URL 변경

운영 환경 배포 시 `src/services/api.ts`의 API_BASE_URL을 수정하세요:

```typescript
const API_BASE_URL = __DEV__
  ? 'http://localhost:8000'
  : 'https://your-production-api.com';
```

## 트러블슈팅

### Metro Bundler 캐시 문제

```bash
npm start -- --reset-cache
```

### Android 빌드 오류

```bash
cd android
./gradlew clean
cd ..
npm run android
```

### iOS Pod 설치 문제

```bash
cd ios
pod install
cd ..
npm run ios
```

## 라이선스

MIT License

## 기여

이 프로젝트는 Briefly 팀이 관리합니다.

## 문의

문제가 발생하거나 문의사항이 있으시면 이슈를 생성해주세요.
