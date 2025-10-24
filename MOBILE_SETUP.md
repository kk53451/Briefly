# Briefly Mobile App 설정 가이드

## 개요

Briefly의 React Native 모바일 애플리케이션이 성공적으로 구현되었습니다. 이 문서는 모바일 앱의 설정 및 실행 방법을 안내합니다.

## 구현된 기능

### ✅ 완성된 기능 목록

1. **사용자 인증**
   - 카카오 소셜 로그인
   - JWT 토큰 기반 인증
   - 자동 로그인 (토큰 저장)

2. **온보딩**
   - 관심 카테고리 선택
   - 사용자 프로필 초기 설정

3. **뉴스 서비스**
   - 오늘의 뉴스 (카테고리별)
   - 인기 뉴스 랭킹
   - 뉴스 상세 보기
   - 북마크 기능
   - 원문 링크 열기

4. **팟캐스트 플레이어** 🎵
   - 뮤직 플레이어 스타일 UI
   - 백그라운드 오디오 재생
   - 재생/일시정지
   - 15초 앞/뒤 스킵
   - 프로그레스 바 및 시간 표시
   - 앨범 아트 스타일 카테고리 표시

5. **프로필 관리**
   - 사용자 정보 표시
   - 관심 카테고리 수정
   - 로그아웃

## 프로젝트 구조

```
mobile/
├── src/
│   ├── components/          # UI 컴포넌트
│   ├── screens/             # 화면
│   ├── navigation/          # 네비게이션
│   ├── contexts/            # Context API
│   ├── services/            # API & 오디오 플레이어
│   ├── types/               # TypeScript 타입
│   └── constants/           # 상수 & 테마
├── App.tsx
├── app.json
└── package.json
```

## 시작하기

### 1. 의존성 설치

```bash
cd mobile
npm install
```

### 2. 백엔드 API URL 설정

`mobile/src/services/api.ts` 파일을 열고 API URL을 수정하세요:

```typescript
const API_BASE_URL = "http://localhost:8000"; // 또는 실제 서버 URL
```

개발 환경에서는:
- **iOS 시뮬레이터**: `http://localhost:8000`
- **Android 에뮬레이터**: `http://10.0.2.2:8000`
- **실제 기기**: `http://YOUR_COMPUTER_IP:8000`

### 3. 앱 실행

```bash
# Expo 개발 서버 시작
npm start

# iOS 시뮬레이터에서 실행
npm run ios

# Android 에뮬레이터에서 실행
npm run android
```

## 디자인 시스템

### 색상 테마

앱은 다크 테마를 기본으로 사용합니다:

- **Primary**: `#6366f1` (Indigo)
- **Secondary**: `#ec4899` (Pink)
- **Background**: `#0f172a` (Slate 900)
- **Card Background**: `#1e293b` (Slate 800)
- **Text**: `#f1f5f9` (White)
- **Text Secondary**: `#94a3b8` (Slate 400)

### 주요 UI 컴포넌트

1. **Button**: Primary, Secondary, Outline 변형 지원
2. **Card**: 뉴스 및 콘텐츠 표시용 카드
3. **NewsCard**: 뉴스 아이템 전용 카드
4. **MusicPlayer**: 팟캐스트 플레이어 UI

## 백그라운드 오디오 재생

### iOS 설정

`app.json`에 백그라운드 오디오 모드가 이미 설정되어 있습니다:

```json
"ios": {
  "infoPlist": {
    "UIBackgroundModes": ["audio"]
  }
}
```

### Android 설정

필요한 권한이 `app.json`에 포함되어 있습니다:

```json
"android": {
  "permissions": [
    "android.permission.INTERNET",
    "android.permission.FOREGROUND_SERVICE",
    "android.permission.WAKE_LOCK"
  ]
}
```

## 카카오 로그인 설정

### 백엔드 요구사항

백엔드에서 다음 엔드포인트를 제공해야 합니다:

1. `GET /api/auth/kakao/login`: 카카오 로그인 URL 반환
2. `GET /api/auth/kakao/callback?code={code}`: 인증 코드로 토큰 교환

### Deep Link 설정

`app.json`에 URL Scheme이 설정되어 있습니다:

```json
"scheme": "briefly"
```

백엔드 콜백 URL은 `briefly://` 로 시작해야 합니다.

## API 엔드포인트

앱에서 사용하는 주요 API 엔드포인트:

### 인증
- `GET /api/auth/kakao/login`
- `GET /api/auth/kakao/callback`
- `GET /api/auth/me`
- `POST /api/auth/logout`

### 뉴스
- `GET /api/news/today`
- `GET /api/news?category={category}`
- `GET /api/news/{newsId}`
- `POST /api/news/bookmark`
- `DELETE /api/news/bookmark/{newsId}`

### 사용자
- `GET /api/user/profile`
- `PUT /api/user/profile`
- `GET /api/user/bookmarks`
- `GET /api/user/categories`
- `PUT /api/user/categories`
- `GET /api/user/onboarding/status`
- `POST /api/user/onboarding`

### 팟캐스트
- `GET /api/frequencies`
- `GET /api/frequencies/history`
- `GET /api/frequencies/{category}`

### 카테고리
- `GET /api/categories`

## 문제 해결

### 1. "Network request failed" 오류

- API URL이 올바른지 확인
- 백엔드 서버가 실행 중인지 확인
- 실제 기기에서 테스트 시 컴퓨터와 같은 네트워크에 연결되어 있는지 확인

### 2. 오디오 재생이 안 됨

- 오디오 URL이 유효한지 확인
- S3 Presigned URL이 만료되지 않았는지 확인
- 백그라운드 권한이 설정되어 있는지 확인

### 3. 카카오 로그인이 작동하지 않음

- 백엔드의 카카오 앱 키가 올바른지 확인
- 리다이렉트 URI가 올바르게 설정되어 있는지 확인
- Deep Link Scheme이 일치하는지 확인

## 빌드 및 배포

### EAS Build 설정

```bash
# EAS CLI 설치
npm install -g eas-cli

# EAS 로그인
eas login

# 프로젝트 설정
eas build:configure

# iOS 빌드
eas build --platform ios

# Android 빌드
eas build --platform android
```

### 개발 빌드

```bash
# 개발용 APK 생성 (Android)
eas build --platform android --profile development

# 개발용 IPA 생성 (iOS)
eas build --platform ios --profile development
```

## 추가 개발 가이드

### 새 화면 추가

1. `src/screens/` 에 컴포넌트 생성
2. `src/navigation/types.ts` 에 라우트 타입 추가
3. 네비게이터에 화면 등록

### 테마 커스터마이징

`src/constants/theme.ts` 파일에서 색상, 간격, 폰트 등을 수정:

```typescript
export const Colors = {
  primary: "#6366f1",
  // ... 다른 색상
};
```

### API 추가

1. `src/types/api.ts` 에 타입 정의
2. `src/services/api.ts` 에 메서드 구현

## 개발 팁

- **Hot Reload**: 코드 변경 시 자동으로 앱이 새로고침됩니다
- **Debugging**: React Native Debugger 또는 Chrome DevTools 사용
- **Expo Go**: 실제 기기에서 빠르게 테스트 가능

## 성능 최적화

- 이미지는 `resizeMode` prop으로 최적화
- 긴 리스트는 `FlatList`로 렌더링 (현재는 `ScrollView` 사용)
- 불필요한 리렌더링 방지를 위해 `React.memo` 사용 고려

## 라이센스

MIT License

---

**문의사항이 있으시면 프로젝트 이슈에 등록해주세요!**
