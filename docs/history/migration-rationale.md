# React (Next.js) → React Native Expo 전환 이유 분석

> 📌 **과거 의사결정 기록입니다.** 이 문서가 다루는 전환(Next.js → React Native)은 실제로
> 진행됐지만, 이후 클라이언트는 **Flutter 로 다시 전환**되어 현재는 `flutter/` 가 유일한
> 클라이언트입니다. `frontend/` 와 `mobile/` 은 보존용이며 더 이상 개발하지 않습니다.
>
> 아래 내용은 당시의 판단 근거로 남겨둡니다. 여기서 든 요구사항(네이티브 오디오 재생,
> OAuth 통합, 백그라운드 재생 등)은 현재 Flutter 에서 `just_audio` / `supabase_flutter` /
> `google_sign_in` 으로 충족하고 있습니다.

## 프로젝트 개요
- **Briefly**: AI 기반 뉴스 팟캐스트 플랫폼
- **당시 기존 스택**: Next.js 14 (frontend/)
- **당시 새 스택**: React Native Expo (mobile/)
- **현재 스택**: Flutter (flutter/)

---

## 전환의 합당한 이유

### 1. 네이티브 오디오 기능의 필수성

**문제점 (Next.js/Web)**
- 웹 브라우저의 Audio API는 백그라운드 재생에 제한이 있음
- iOS Safari에서 화면 잠금 시 오디오 재생이 중단됨
- 백그라운드에서 재생 컨트롤(잠금화면/알림센터)을 표시할 수 없음

**해결 (React Native Expo)**
```typescript
// mobile/src/contexts/AudioPlayerContext.tsx
await Audio.setAudioModeAsync({
  staysActiveInBackground: true,      // 백그라운드 재생
  playsInSilentModeIOS: true,         // 무음 모드에서도 재생
  shouldDuckAndroid: true,            // 다른 앱 오디오와 공존
});
```

**근거**: Briefly는 팟캐스트 앱으로, 사용자가 화면을 끄고 이동 중에도 청취할 수 있어야 함. 이는 웹에서는 기술적으로 불가능함.

---

### 2. 네이티브 인증 통합 (카카오 로그인)

**문제점 (Next.js/Web)**
- OAuth 리다이렉트 방식으로만 구현 가능
- 브라우저 ↔ 앱 전환 시 UX가 불편함
- 카카오톡 앱이 설치되어 있어도 웹뷰로만 로그인 가능

**해결 (React Native Expo)**
```json
// mobile/app.json
"plugins": [
  ["@react-native-kakao/core", {
    "nativeAppKey": "...",
    "android": { "redirectUri": "kakao...://oauth" },
    "ios": { "redirectUri": "kakao...://oauth" }
  }]
]
```

**근거**:
- 카카오톡 앱 연동 로그인으로 원터치 인증 가능
- Custom URL Scheme으로 앱 ↔ 앱 직접 통신
- 한국 사용자의 90%가 카카오톡 사용 → UX 개선 효과 극대화

---

### 3. 모바일 퍼스트 UX 최적화

**문제점 (Next.js/Web)**
- 뉴스 앱 특성상 주 사용 환경은 모바일
- 웹 앱은 네이티브 제스처(스와이프, 당겨서 새로고침 등) 구현이 어려움
- 브라우저 주소창/탭바로 인한 화면 공간 낭비

**해결 (React Native Expo)**
```typescript
// mobile/src/screens/HomeScreen.tsx
<FlatList
  refreshControl={
    <RefreshControl
      refreshing={isRefreshing}
      onRefresh={handleRefresh}
    />
  }
/>
```

**근거**:
- 네이티브 Pull-to-Refresh, 스크롤 성능 최적화
- 풀스크린 앱 경험으로 콘텐츠 몰입도 향상
- 하단 탭 네비게이션의 자연스러운 구현

---

### 4. 디바이스 기능 접근성

**문제점 (Next.js/Web)**
- Push Notification 웹 표준은 iOS에서 제한적 (2023년 이후 일부 지원)
- Secure Storage 접근 불가 (localStorage만 사용 가능, 보안 취약)
- 포그라운드 서비스/Wake Lock 제한

**해결 (React Native Expo)**
```json
// mobile/package.json 의존성
"expo-secure-store": "~15.0.3",  // 보안 저장소 (키체인/키스토어)
"expo-av": "^16.0.7",            // 미디어 재생
"expo-web-browser": "~15.0.9",   // 인앱 브라우저

// mobile/app.json 권한
"android": {
  "permissions": ["FOREGROUND_SERVICE", "WAKE_LOCK"]
}
```

**근거**:
- JWT 토큰 보안 저장 (SecureStore)
- 앱이 종료되어도 푸시 알림으로 새 팟캐스트 알림 가능
- 백그라운드 오디오 재생을 위한 포그라운드 서비스

---

### 5. 앱스토어 배포 및 발견성

**문제점 (Next.js/Web)**
- PWA로 설치 유도해도 실제 설치율 매우 낮음
- 앱스토어 검색에서 발견 불가
- 모바일 웹 → 앱 전환 시 리텐션 손실

**해결 (React Native Expo)**
```json
// mobile/app.json
"ios": { "bundleIdentifier": "com.briefly.app" },
"android": { "package": "com.briefly.app" }
```

**근거**:
- App Store / Google Play 검색으로 유기적 유입 가능
- 홈 화면 아이콘으로 리텐션 증가
- 앱 리뷰/평점으로 신뢰도 확보

---

### 6. 개발 효율성 (Expo)

**Expo 선택 이유**:
| 항목 | 순수 React Native | Expo |
|------|------------------|------|
| 초기 설정 | 복잡 (Xcode, Android Studio 필수) | 간단 (npm install만으로 시작) |
| 네이티브 모듈 | 수동 링킹 필요 | 자동 (expo-av, expo-secure-store 등) |
| OTA 업데이트 | 구현 필요 | EAS Update 내장 |
| 빌드 | 로컬 빌드 환경 필요 | EAS Build (클라우드) |

```json
// mobile/app.json
"newArchEnabled": true  // React Native New Architecture 활성화
```

**근거**:
- 1인/소규모 팀에서 iOS/Android 동시 개발 가능
- Hot Reload로 빠른 개발 사이클
- EAS로 CI/CD 파이프라인 간소화

---

## 요약: 전환 핵심 동기

| 순위 | 이유 | 비즈니스 임팩트 |
|------|------|---------------|
| 1 | **백그라운드 오디오 재생** | 팟캐스트 앱의 핵심 기능 (웹에서 불가능) |
| 2 | **카카오 네이티브 로그인** | 한국 사용자 전환율 향상 |
| 3 | **앱스토어 배포** | 유저 획득/리텐션 채널 확보 |
| 4 | **네이티브 UX** | 뉴스 소비에 최적화된 경험 |
| 5 | **보안 저장소** | JWT 토큰 안전한 관리 |

---

## 결론

Briefly는 **오디오 콘텐츠 중심의 뉴스 앱**으로, 핵심 기능인 **백그라운드 팟캐스트 재생**이 웹 기술로는 구현 불가능합니다. React Native Expo로의 전환은 기술적 제약을 해결하는 동시에, 한국 시장에 최적화된 카카오 로그인과 앱스토어 배포를 통해 사용자 경험과 비즈니스 성장 모두를 달성하기 위한 필수적인 선택입니다.
