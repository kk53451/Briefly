# Briefly — Flutter app

AI-powered Korean news podcast app. Supabase 백엔드 (프로젝트 `esaktypcwhpcgmdvxvxq`).

## Setup

1. **Install dependencies**
   ```bash
   flutter pub get
   ```

2. **Environment variables**
   - `.env.example` 을 `.env` 로 복사 (자동 생성 완료됨)
   - Google client IDs 채워넣기
   - `.env` 는 `flutter_dotenv`가 앱 시작 시 로드

3. **iOS deep link** — `ios/Runner/Info.plist` 에 `briefly://` URL scheme 추가 (Kakao OAuth callback)
   ```xml
   <key>CFBundleURLTypes</key>
   <array>
     <dict>
       <key>CFBundleURLSchemes</key>
       <array><string>briefly</string></array>
     </dict>
   </array>
   ```

4. **Android deep link** — `android/app/src/main/AndroidManifest.xml` 의 `<activity>` 안에 intent-filter 추가
   ```xml
   <intent-filter android:autoVerify="false">
     <action android:name="android.intent.action.VIEW" />
     <category android:name="android.intent.category.DEFAULT" />
     <category android:name="android.intent.category.BROWSABLE" />
     <data android:scheme="briefly" android:host="auth-callback" />
   </intent-filter>
   ```

5. **Audio background (Android)** — foreground service 권한/서비스 등록 (`just_audio_background` 문서 참고)

6. **Supabase Dashboard** (수동 1회)
   - Auth → Providers: Kakao, Google 활성화 + 키 입력
   - Auth → URL Configuration → Additional Redirect URLs 에 `briefly://auth-callback` 추가
   - Bucket `briefly-audio` 는 이미 생성됨 (public)

## Run

```bash
flutter run                    # 연결된 디바이스
flutter run -d chrome          # 웹 (개발 편의용)
```

## 폴더 구조

```
lib/
├── main.dart               # 엔트리: dotenv + audio background + Supabase init
├── app.dart                # MaterialApp.router + 테마 + 라우터 주입
├── core/
│   ├── config/
│   │   ├── env.dart        # .env 파싱 유틸
│   │   └── supabase.dart   # Supabase.initialize + client 접근자
│   ├── theme/app_theme.dart
│   ├── router/app_router.dart   # go_router + auth redirect
│   └── constants/categories.dart
├── features/
│   ├── auth/
│   │   ├── auth_repository.dart   # Kakao(web OAuth) + Google(native id_token)
│   │   ├── auth_controller.dart   # Riverpod: session/auth state providers
│   │   └── login_screen.dart
│   ├── home/               # 홈 탭 (TBD)
│   ├── today/              # 투데이 탭 (TBD)
│   ├── frequency/          # 팟캐스트 (TBD)
│   ├── headlines/          # 오늘의 브리핑 (TBD)
│   ├── bookmarks/          # 북마크 (TBD)
│   └── profile/            # 프로필/설정 (TBD)
└── shared/
    ├── models/             # 데이터 모델 (TBD)
    └── widgets/            # 재사용 위젯 (TBD)
```

## Supabase 직접 조회 패턴

```dart
final rows = await supabase
  .from('news_cards')
  .select()
  .eq('date', '2026-04-19')
  .eq('slot', 'AM')
  .order('rank');

final url = supabase.storage
  .from('briefly-audio')
  .getPublicUrl(audioPath);
```

## Release blockers

- **Apple Sign-in** — iOS 앱이 소셜 로그인 제공 시 필수 (Apple HIG). `sign_in_with_apple` 패키지 + Supabase Auth Apple provider 활성화.
- **Kakao Biz App** — `account_email` scope 사용 시 필요.
- **Bundle id** — 현재 `com.briefly.briefly`. 출시 전 `android/app/build.gradle`(applicationId) + `ios/Runner.xcodeproj`(PRODUCT_BUNDLE_IDENTIFIER) 를 `com.briefly.app` 으로 통일.
