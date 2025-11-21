# 📱 Briefly Android 앱 설정 및 실행 가이드

**Briefly 모바일 앱을 처음 실행하는 개발자를 위한 완벽 가이드**

---

## 📋 목차

1. [필수 환경 확인](#1-필수-환경-확인)
2. [Android Studio 설정](#2-android-studio-설정)
3. [환경변수 설정](#3-환경변수-설정)
4. [Android 에뮬레이터 생성](#4-android-에뮬레이터-생성)
5. [프로젝트 설정](#5-프로젝트-설정)
6. [백엔드 서버 실행](#6-백엔드-서버-실행)
7. [모바일 앱 실행](#7-모바일-앱-실행)
8. [문제 해결](#8-문제-해결)

---

## 1. 필수 환경 확인

### ✅ 설치 확인

터미널(PowerShell 또는 CMD)에서 다음 명령어를 실행하여 설치 여부를 확인하세요:

```bash
# Node.js 버전 확인 (18.x 이상 필요)
node --version

# npm 버전 확인
npm --version

# Python 버전 확인 (3.12.x 권장)
python --version

# Android Studio 설치 확인
where android
```

### 📦 필요한 소프트웨어

- ✅ **Node.js 18+** - [다운로드](https://nodejs.org/)
- ✅ **Python 3.12+** - [다운로드](https://www.python.org/)
- ✅ **Android Studio** - 설치 완료 ✓
- ✅ **Git** - [다운로드](https://git-scm.com/)

---

## 2. Android Studio 설정

### 2.1 SDK 설치

1. Android Studio 실행
2. 우측 상단 **More Actions** → **SDK Manager** 클릭
3. **SDK Platforms** 탭에서 설치:
   - ☑️ Android 13.0 (Tiramisu) - API Level 33
   - ☑️ Android 14.0 (UpsideDownCake) - API Level 34

4. **SDK Tools** 탭에서 설치:
   - ☑️ Android SDK Build-Tools
   - ☑️ Android Emulator
   - ☑️ Android SDK Platform-Tools
   - ☑️ Intel x86 Emulator Accelerator (HAXM installer)

5. **Apply** → **OK** 클릭하여 설치 시작

### 2.2 SDK 경로 확인

SDK Manager에서 **Android SDK Location** 확인:
```
C:\Users\{사용자명}\AppData\Local\Android\Sdk
```

이 경로를 메모장에 복사해두세요 (환경변수 설정에 필요).

---

## 3. 환경변수 설정

### 3.1 시스템 환경변수 추가 (Windows)

1. **시작 메뉴** 검색: `환경 변수`
2. **시스템 환경 변수 편집** 클릭
3. **환경 변수** 버튼 클릭

### 3.2 ANDROID_HOME 변수 생성

**시스템 변수** 섹션에서:

1. **새로 만들기** 클릭
2. 변수 이름: `ANDROID_HOME`
3. 변수 값: `C:\Users\{사용자명}\AppData\Local\Android\Sdk`
4. **확인** 클릭

### 3.3 Path 변수 수정

**시스템 변수**에서 `Path` 선택 → **편집** 클릭 → 다음 4개 추가:

```
%ANDROID_HOME%\platform-tools
%ANDROID_HOME%\emulator
%ANDROID_HOME%\tools
%ANDROID_HOME%\tools\bin
```

### 3.4 환경변수 적용 확인

**새 터미널 창**을 열고 확인:

```bash
# adb 명령어 테스트
adb version

# 환경변수 확인
echo %ANDROID_HOME%
```

정상 출력되면 설정 완료!

---

## 4. Android 에뮬레이터 생성

### 4.1 Device Manager 열기

Android Studio에서:
1. 우측 상단 **More Actions** → **Virtual Device Manager** 클릭
2. 또는 **Tools** → **Device Manager**

### 4.2 가상 기기 생성

1. **Create Device** 버튼 클릭

2. **하드웨어 선택**:
   - Category: **Phone**
   - 모델: **Pixel 5** 또는 **Pixel 6** 선택
   - **Next** 클릭

3. **시스템 이미지 선택**:
   - Release Name: **Tiramisu** (API Level 33)
   - Target: **Android 13.0 (Google APIs)**
   - **Download** 클릭 (처음이면 다운로드 필요)
   - 다운로드 완료 후 **Next** 클릭

4. **설정 확인**:
   - AVD Name: `Pixel_5_API_33` (기본값)
   - Startup orientation: **Portrait**
   - **Show Advanced Settings** 클릭 (선택사항)
     - RAM: `2048 MB` 이상
     - VM heap: `512 MB`
     - Internal Storage: `2048 MB` 이상
   - **Finish** 클릭

### 4.3 에뮬레이터 실행 테스트

Device Manager에서 생성한 기기 우측의 **▶ (Play)** 버튼 클릭하여 정상 부팅 확인.

---

## 5. 프로젝트 설정

### 5.1 Node.js 의존성 설치

```bash
# 프로젝트 루트로 이동
cd D:\Github\Briefly\frontend

# 의존성 설치
npm install

# Expo CLI 전역 설치 (선택사항)
npm install -g expo-cli
```

### 5.2 환경변수 파일 생성

`frontend/.env` 파일 생성:

```bash
# 로컬 개발 환경 (Android 에뮬레이터)
API_BASE_URL=http://10.0.2.2:8000

# Kakao Developer에서 발급받은 Client ID
KAKAO_CLIENT_ID=your_kakao_client_id_here

# 앱 스킴
APP_SCHEME=briefly
```

**중요:**
- Android 에뮬레이터는 `localhost` 대신 `10.0.2.2` 사용
- 실제 기기 테스트 시에는 PC의 실제 IP 주소 사용 (예: `http://192.168.0.10:8000`)

### 5.3 Kakao Client ID 발급 (필수)

1. [Kakao Developers](https://developers.kakao.com/) 접속
2. **내 애플리케이션** → **애플리케이션 추가하기**
3. 앱 이름: `Briefly` 입력 후 생성
4. **앱 키** → **Native 앱 키** 복사
5. `.env` 파일의 `KAKAO_CLIENT_ID`에 붙여넣기

### 5.4 Kakao 플랫폼 설정

Kakao Developers 콘솔에서:

1. **플랫폼** → **Android 플랫폼 등록**
2. 패키지명: `com.briefly.app`
3. 마켓 URL: (비워둠)
4. **저장** 클릭

---

## 6. 백엔드 서버 실행

### 6.1 Python 가상환경 생성 (권장)

```bash
# backend 폴더로 이동
cd D:\Github\Briefly\backend

# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (PowerShell)
.\venv\Scripts\Activate.ps1

# 가상환경 활성화 (CMD)
venv\Scripts\activate
```

### 6.2 Python 의존성 설치

```bash
# requirements.txt에서 설치
pip install -r requirements.txt
```

### 6.3 백엔드 환경변수 설정

`backend/.env` 파일 생성:

```bash
# OpenAI API
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o-mini

# ElevenLabs TTS
ELEVENLABS_API_KEY=sk_...
ELEVENLABS_VOICE_ID=TX3LPaxmHKxFdv7VOQHJ

# BigKinds API
BIGKINDS_ACCESS_KEY=your_bigkinds_key

# Kakao OAuth
KAKAO_CLIENT_ID=your_kakao_client_id
KAKAO_REDIRECT_URI=briefly://oauth

# DynamoDB Tables
DDB_NEWS_TABLE=NewsCards
DDB_FREQ_TABLE=Frequencies
DDB_USERS_TABLE=Users
DDB_BOOKMARKS_TABLE=Bookmarks

# S3 Bucket
S3_BUCKET=briefly-news-audio
```

### 6.4 서버 실행

```bash
# 0.0.0.0으로 바인딩 (에뮬레이터 접근 가능)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**성공 메시지:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
```

**API 문서 확인:** http://localhost:8000/docs

---

## 7. 모바일 앱 실행

### 7.1 Android 에뮬레이터 실행

Android Studio Device Manager에서 생성한 에뮬레이터 시작:
- **▶ (Play)** 버튼 클릭
- 부팅 완료까지 대기 (약 30초~1분)

### 7.2 Expo 개발 서버 시작

**새 터미널 창**을 열어 실행:

```bash
# frontend 폴더로 이동
cd D:\Github\Briefly\frontend

# Expo 개발 서버 시작
npx expo start
```

**Expo 개발 서버가 실행되면:**
```
› Metro waiting on exp://192.168.0.10:8081
› Scan the QR code above with Expo Go (Android) or the Camera app (iOS)

› Press a │ open Android
› Press w │ open web

› Press j │ open debugger
› Press r │ reload app
› Press m │ toggle menu
› Press o │ open project code in your editor

› Press ? │ show all commands
```

### 7.3 앱 실행

터미널에서 **`a`** 키를 눌러 Android 에뮬레이터에서 앱 실행:

```
› Opening on Android...
```

**또는 직접 실행:**

```bash
npm run android
```

### 7.4 첫 실행 시 Metro Bundler 빌드

처음 실행 시 JavaScript 번들링이 진행됩니다:

```
 BUNDLE  ./index.js

 ██████████████████████████████████████████ 100.0% (1234/1234)

 BUNDLE  [android, dev] ./index.js ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ 100.0% (1234/1234), done.
```

### 7.5 앱 실행 확인

에뮬레이터에 **Briefly** 앱이 설치되고 실행됩니다:
1. 폰트 로딩 화면 (ActivityIndicator)
2. 로그인 화면 표시 (카카오 로그인 버튼)

---

## 8. 문제 해결

### ❌ "SDK location not found"

**증상:** Gradle 빌드 실패

**해결:**
```bash
# frontend/android/local.properties 파일 생성
echo sdk.dir=C:\\Users\\YourUsername\\AppData\\Local\\Android\\Sdk > android/local.properties
```

### ❌ "adb: command not found"

**증상:** adb 명령어를 찾을 수 없음

**해결:**
1. 환경변수 `Path`에 `%ANDROID_HOME%\platform-tools` 추가 확인
2. 터미널 재시작

### ❌ "Unable to connect to development server"

**증상:** 앱이 백엔드 API에 연결 불가

**해결:**
```bash
# 1. 백엔드가 0.0.0.0으로 바인딩되어 있는지 확인
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 2. .env 파일 확인
# API_BASE_URL=http://10.0.2.2:8000 (localhost 아님!)

# 3. 방화벽 확인
# Windows 방화벽에서 포트 8000 허용
```

### ❌ 폰트 로드 실패

**증상:** "Error loading fonts" 메시지

**해결:**
```bash
# 캐시 클리어 후 재시작
npx expo start -c

# 폰트 파일 존재 확인
ls assets/fonts/
```

### ❌ Metro bundler 오류

**증상:** "Unable to resolve module"

**해결:**
```bash
# node_modules 삭제 후 재설치
rm -rf node_modules
npm install

# 캐시 클리어
npx expo start -c
```

### ❌ 에뮬레이터가 너무 느림

**해결:**
1. Device Manager에서 에뮬레이터 삭제 후 재생성
2. RAM 크기 증가 (3072 MB)
3. BIOS에서 Intel VT-x 또는 AMD-V 활성화
4. Cold Boot 대신 Quick Boot 사용

### ❌ Gradle 빌드 오류

**해결:**
```bash
cd frontend/android
.\gradlew clean
cd ..
npm run android
```

---

## 🎉 성공적인 실행 확인

앱이 정상적으로 실행되면 다음을 확인할 수 있습니다:

1. ✅ **폰트 로딩 완료** - ActivityIndicator 사라짐
2. ✅ **로그인 화면 표시** - 카카오 로그인 버튼 보임
3. ✅ **프리미엄 폰트 적용** - Outfit, Pretendard 폰트 렌더링
4. ✅ **다크 테마 적용** - 배경색 #0F172A

---

## 📞 추가 지원

문제가 계속되면 다음을 확인하세요:

1. **Expo 공식 문서**: https://docs.expo.dev/
2. **React Native 문서**: https://reactnative.dev/
3. **프로젝트 CLAUDE.md**: 전체 아키텍처 및 개발 가이드
4. **프로젝트 FONTS.md**: 폰트 관련 상세 가이드

---

**마지막 업데이트:** 2024-11-21
**버전:** 1.0.0
**작성자:** Claude Code
