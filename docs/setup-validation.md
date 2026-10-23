# 설치·실행 검증 기록

검증일: 2026-10-23 (KST)

[루트 README](../README.md)의 설치·실행 절차를 Windows에서 점검했습니다.
Python 패키지는 기존 전역 환경과 분리한 새 `backend/venv/`에 설치했습니다.
앱 설치·시작과 로컬 분석은 확인했지만, 외부 서비스 조건 때문에 전체 배치의 저장·오디오 생성까지 성공한 상태는 아닙니다.

## 검증 환경

| 항목 | 환경 |
|---|---|
| OS / Python | Windows 11 x64 / Python 3.12.10 |
| Flutter / Dart | Flutter 3.41.7 / Dart 3.11.5 |
| Android | 실제 Android 10 기기, 디버그 빌드 |
| Java / Gradle | 기본 선택 Java 25.0.2에서 실패 → Gradle 실행 JDK 17.0.17 지정 후 성공 / Gradle 8.14 |
| Python 기본 의존성 | [Windows CPU lockfile](../backend/requirements-windows-cpu.lock.txt) |
| 주요 Python 버전 | torch 2.14.1(CPU), sentence-transformers 6.2.0, transformers 5.20.2, supabase 2.33.0, openai 1.109.1, notebooklm-py 0.4.1 |

검증 중 JDK는 해당 프로세스의 `GRADLE_OPTS`에 `-Dorg.gradle.java.home`을 지정했습니다.
사용자 전체 Flutter 설정은 변경하지 않았습니다. 일반 설치에서는 README의 `flutter config --jdk-dir` 안내를 따를 수 있습니다.
KURE-v1 가중치는 기존 로컬 캐시를 사용했으므로 모델의 최초 다운로드는 이번 검증에 포함되지 않습니다.

## 결과

| 단계 | 결과 | 확인 범위 |
|---|---|---|
| Python 가상환경 생성·기본 패키지 설치 | 통과 | 새 venv에서 requirements 설치, `pip check` 정상 |
| Windows CPU lockfile | 통과 | 실제 설치 버전 기록, lockfile 재해석 시 충돌 없음 |
| 검증 도구의 선택 의존성 | 통과 | `requirements-eval.txt` 설치, `faster_whisper.WhisperModel` import, `pip check` 정상 |
| CLI 진입점 | 통과 | scheduler, 대본 dry-run, 전사·평가, 오디오 재생성의 `--help` |
| 네이버 수집 | 통과 | 경제 카테고리 목록 1페이지 36건과 기사 1건의 본문 수집 |
| KURE-v1 추론 | 통과 | 새 venv에서 모델 로드, 문장 2개를 `(2, 1024)` 벡터로 생성 |
| UMAP/HDBSCAN | 통과 | 90개 벡터의 클러스터링 및 fallback 실행 |
| 실제 샘플 분석 | 통과 | 저장된 정치·경제·국제 기사로 분석, 9개 토픽·150개 대본 소스 구성 |
| OpenAI 모델 조회 | 통과 | 설정된 모델 조회 HTTP 200. 생성 크레딧 보유 여부와는 별개 |
| OpenAI 대본 생성 | 차단 | 실제 dry-run 호출이 `429 credit_balance_exhausted` 반환 |
| Ollama | 차단 | PATH에서 실행 파일을 찾지 못했고 `localhost:11434` 연결도 실패 |
| Supabase DB·Storage | 차단 | 현재 설정된 프로젝트 주소의 DNS 조회 실패 (`getaddrinfo`, 11001) |
| Chromium | 통과 | 새 Playwright 환경의 Chromium 설치 및 headless 브라우저 시작 |
| NotebookLM 인증 | 차단 | 인증 파일은 있으나 `check_auth()` 결과 False. 자동 로그인·생성은 실행하지 않음 |
| Flutter 패키지·정적 분석 | 통과 | `flutter pub get`, `flutter analyze` 정상 |
| Android APK | 통과 | JDK 17 지정 후 `flutter build apk --debug` 성공 |
| Android 앱 실행 | 통과 | `flutter run --no-resident`로 실제 기기 설치·프로세스 시작, Flutter 엔진과 Supabase SDK 초기화 로그 확인 |
| 앱 데이터·로그인·오디오 | 미검증 | SDK 초기화는 원격 DB 접근 성공을 의미하지 않음. Supabase 복구 후 별도 확인 필요 |
| iOS / release 빌드 | 미검증 | Windows에서 iOS 실행 불가. 이번 Android 검증은 debug 빌드 |
| 대본 CLI 실패 처리 | 통과 | 샘플 누락·분석 실패·빈 대본·정상 저장 4개 회귀 테스트, 실제 누락 파일 CLI 종료 코드 1 |

새 Supabase 프로젝트의 SQL 초기화는 실행하지 않았으며, DB·Storage 쓰기도 수행하지 않았습니다.
Discord 메시지와 Loki 검증 이벤트도 보내지 않았습니다.

## 보완한 내용

- `notebooklm-py==0.4.1`을 requirements 자체에 고정했습니다. 현재 사용하는 `DEFAULT_STORAGE_PATH`는 이후 버전에서 제거될 수 있습니다.
- Supabase SDK 버전을 고정하고 Windows CPU 환경의 설치 버전을 lockfile로 남겼습니다. CUDA·다른 OS는 별도 검증이 필요합니다.
- 전사 도구의 `faster-whisper`를 `requirements-eval.txt`로 분리하고, `ffprobe`가 별도 실행 파일임을 명시했습니다.
- 누락된 Loki 설정 4개를 `.env.example`에 추가했습니다. Loki URL에는 push 경로를 중복 입력하지 않습니다.
- Ollama URL·모델을 `.env`로 설정할 수 있게 연결했습니다.
- Flutter 템플릿의 기존 프로젝트 URL·공개 키를 placeholder로 바꾸고, 오디오 URL 생성이 실제 `SUPABASE_AUDIO_BUCKET` 값을 사용하도록 고쳤습니다.
- JDK 17, Android 라이선스 확인, iOS Google 로그인 URL scheme 등록 절차를 보완했습니다.
- 대본 dry-run이 오류를 기록하고도 0으로 끝나던 문제를 수정했습니다. 실패 시 1, 정상 저장 시 0을 반환합니다.

## 전체 실행 전에 남은 조건

1. **기존 Supabase 프로젝트 복구**: 사용자는 현재 프로젝트를 복구할 예정입니다. 실제 `.env` 연결 값은 유지했습니다. 복구 후 backend의 서비스 역할과 앱의 공개 키로 각각 테이블 접근을 확인해야 합니다.
2. **Ollama 실행 환경 준비**: Ollama 설치·실행, `gemma4:e4b-it-q4_K_M` 다운로드 후 헤드라인 생성 확인이 필요합니다. `--skip-script`로 실행해도 필요합니다.
3. **OpenAI 크레딧 확보**: 모델 조회는 성공했지만 생성 요청에 사용할 잔액이 없습니다. 크레딧·한도 확인 후 대본 dry-run을 다시 실행해야 합니다.
4. **NotebookLM 재로그인**: 배치를 실행할 계정과 가상환경에서 `notebooklm login` 후 인증·생성을 확인해야 합니다.
5. **플랫폼별 설정 완료**: `flutter doctor`에 Android 라이선스 일부 미승인 경고가 남습니다. iOS Google 클라이언트 ID는 로컬 `.env`에서 placeholder 상태이고, `REVERSED_CLIENT_ID` scheme도 등록해야 합니다.

위 조건이 갖춰지면 README 순서대로 경제 피드 → 전체 대본 → 오디오 → 앱 조회·재생을 검증하세요.
같은 날짜·슬롯의 콘텐츠는 배치 실행으로 갱신될 수 있습니다.

## 재실행 명령

```bash
# backend/의 가상환경에서
python -m pip check
python -X utf8 -m unittest test.test_dryrun_exit
python -X utf8 -m test.generate_integrated_briefing_dryrun --time-slot morning

# flutter/에서, JDK 17 설정 후
flutter analyze
flutter build apk --debug
flutter run -d <device-id>
```

실제 검증 로그는 로컬 `.tmp/readme-*.log`에 남겼습니다. 인증정보와 개인 로컬 설정은 저장소에 추가하지 않습니다.
