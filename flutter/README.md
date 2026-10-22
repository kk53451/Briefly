# Briefly — Flutter 앱

한국어 뉴스·통합 브리핑 팟캐스트 클라이언트입니다.
Supabase에서 기사·헤드라인·팟캐스트를 직접 조회합니다.
현재 저장소에는 **Android와 iOS** 프로젝트가 포함되어 있습니다.

## 실행 준비

저장소 루트에서 `flutter/`로 이동한 뒤 의존성과 환경변수를 준비합니다.

```bash
cd flutter
flutter pub get
```

`.env.example`을 `.env`로 복사하고 사용할 프로젝트의 값을 입력하세요.
PowerShell에서는 `Copy-Item .env.example .env`, macOS/Linux에서는 `cp .env.example .env`를 사용합니다.
기존 `.env`가 있다면 복사하지 말고 설정을 확인하세요.

- `SUPABASE_URL`, `SUPABASE_ANON_KEY`: 앱이 사용할 프로젝트 URL과 공개 클라이언트 키
- `SUPABASE_AUDIO_BUCKET`: 기본값 `briefly-audio`
- `GOOGLE_WEB_CLIENT_ID`: Google 네이티브 로그인에 필요
- `GOOGLE_IOS_CLIENT_ID`: iOS Google 로그인에 사용할 클라이언트 ID

`.env`는 `flutter_dotenv`가 시작 시 읽으며 앱 asset으로 빌드에 포함됩니다.
백엔드의 서비스 역할 키는 이 파일에 넣지 마세요.

## 플랫폼과 인증 설정

다음 설정은 이미 소스에 들어 있습니다.

- [AndroidManifest.xml](android/app/src/main/AndroidManifest.xml): `briefly://auth-callback` 딥링크, 오디오 백그라운드 서비스와 권한
- [Info.plist](ios/Runner/Info.plist): `briefly` URL scheme, `audio` 백그라운드 모드

사용할 Supabase 프로젝트의 Kakao·Google provider와 `briefly://auth-callback` redirect 설정은 별도로 확인하세요.
Google 네이티브 로그인은 배포용 앱 식별자·인증서·플랫폼별 OAuth 설정도 일치해야 합니다.
Storage와 데이터베이스의 초기 SQL은 [백엔드 마이그레이션](../backend_v2_supabase/app/db/migrations/)에 있습니다.
로컬 파일만으로 원격 프로젝트의 설정 완료 여부를 알 수는 없습니다.

## 실행과 빌드

```bash
flutter run                    # 연결된 Android/iOS 디바이스
flutter build apk --release    # Android APK
```

iOS 실행·빌드는 macOS와 Xcode가 필요합니다.
웹 프로젝트(`web/`)는 저장소에 포함되어 있지 않습니다.
Android release 설정은 현재 debug 서명을 사용하므로 배포 전에 서명 구성이 필요합니다.

## 소스 구조

| 경로 | 역할 |
|---|---|
| `lib/main.dart` | 환경변수·날짜 형식·오디오·Supabase 초기화 |
| `lib/app.dart` | 앱 테마와 라우터 연결 |
| `lib/core/` | 설정, 라우터, 테마, 카테고리 상수 |
| `lib/features/auth/` | Kakao OAuth, Google 네이티브 로그인, 게스트 모드 |
| `lib/features/home/` | 카테고리별 뉴스 카드 |
| `lib/features/today/` | 오늘의 브리핑·헤드라인 |
| `lib/features/frequency/` | 팟캐스트 플레이어·에피소드 목록 |
| `lib/features/news_detail/` | 기사 상세 |
| `lib/features/search/` | 검색 |
| `lib/features/profile/` | 프로필 |
| `lib/features/settings/` | 글꼴 설정 |
| `lib/features/onboarding/`, `shell/`, `splash/` | 온보딩, 탭 구성, 시작 화면 |
| `lib/shared/` | 데이터 모델과 공통 위젯 |

북마크 저장 기능과 프로필 활동 지표 연동은 아직 구현되지 않았습니다.
별도 `headlines/`, `bookmarks/` 기능 폴더는 없습니다.
디자인 원본은 [설계 자료](../docs/design/README.md)에 보존합니다.

## 검증 상태

정적 분석은 `flutter analyze`로 실행합니다.
기존 산술 placeholder 테스트는 정리했으며, 앱 동작을 검증하는 Dart 자동 테스트는 아직 없습니다.
로그인·오디오 재생·데이터 조회는 실제 환경에서 별도로 확인해야 합니다.
