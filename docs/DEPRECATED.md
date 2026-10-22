# 종료된 구현과 보존 정책

**정리일: 2026-10-23**

현행 실행 코드는 `backend_v2_supabase/`와 `flutter/`입니다.
아래 구현은 개발·지원을 종료했으며 master 작업 트리에서 제거했습니다.
옛 실행 환경의 동작은 보장하지 않습니다.

## DEPRECATED 목록

| 이전 경로 | 종료한 구현 | 대체 구현 | 보존 위치 |
|---|---|---|---|
| `backend/` | FastAPI + AWS Lambda + DynamoDB + BigKinds | `backend_v2_supabase/` | `archive/pre-cleanup-2026-10-23:backend/` |
| `backend_v2/` | DynamoDB/S3 기반 초기 배치 파이프라인 | `backend_v2_supabase/` | `archive/pre-cleanup-2026-10-23:backend_v2/` |
| `frontend/` | Next.js 웹 클라이언트 | `flutter/` | `archive/pre-cleanup-2026-10-23:frontend/` |
| `mobile/` | 기존 React Native + Expo 앱 | `flutter/` | `archive/pre-cleanup-2026-10-23:mobile/` |
| `mobile_v2_expo/` | Expo 재작성 실험 | `flutter/` | `archive/pre-cleanup-2026-10-23:mobile_v2_expo/` |
| `backend_v2_supabase/test/transcribe_podcasts.py` | 구 A/B/C 오디오 전사 실험, 삭제된 `backend/test/data/`에 의존 | `backend_v2_supabase/test/transcribe_and_evaluate.py` | `archive/pre-cleanup-2026-10-23:backend_v2_supabase/test/transcribe_podcasts.py` |

최종 점검에서 앱 동작을 검증하지 않는 `flutter/test/widget_test.dart`의
산술 placeholder 테스트도 제거했습니다. 원본은 같은 보존 태그에 있습니다.

## 보존 태그

| 태그 | 내용 |
|---|---|
| `archive/master-before-cleanup-2026-10-23` | 정리 전 master `9790cbd9` |
| `archive/pre-cleanup-2026-10-23` | 미커밋 소스와 미추적 앱·자료를 포함한 스냅샷 커밋 `3debbafa` |
| `archive/backend-v3-2026-10-23` | 독립 커밋 `4149d08a` |
| `archive/frontend-v1-2026-10-23` | 독립 커밋 `28ae5e67` |
| `archive/frontend-v2-2026-10-23` | 독립 커밋 `81890470`, `c509a1e1`을 포함한 브랜치 끝 |

스냅샷에는 이전 백엔드·모바일의 미커밋 수정 20개 파일과
미추적 Expo 소스·디자인·문서·화면 기록 91개 파일을 포함했습니다.
사용자 `.gitignore` 수정도 보존했습니다.

환경변수, 로컬 MCP/에이전트 설정, 세션 기록, 설치된 의존성,
로컬 출력물, `backend_v2.zip`은 저장소 밖의 검증된 로컬 백업에 보존했습니다.
이 로컬 파일들은 새 보존 커밋에 추가하지 않았습니다.
기존 Git 이력은 재작성하지 않았으며 기존 stash도 유지했습니다.

## 자료 이동

| 이전 위치 | 현재 위치 |
|---|---|
| `backend/test/data/news_2026-04-11.json` | `backend_v2_supabase/test/fixtures/news_2026-04-11.json` |
| `backend/test/results/`의 보고서·JSON·그림 | `docs/research/clustering/` (임베딩 캐시 제외) |
| `Briefly_design/` | `docs/design/prototype/` |
| `_screenshots/` | `docs/design/screenshots/` |
| `DESIGN_SPEC.md` | `docs/design/DESIGN_SPEC.md` |
| `DATA_SERVING_AUDIT.md` | `docs/research/data-serving-audit-2026-04-27.md` |
| `backend_v2_supabase/WIP_PODCAST_TUNING.md` | `docs/research/podcast-tuning-2026-04-21.md` |
| 이전 `backend_v2_supabase/test/README.md` | `docs/research/pipeline-experiments.md` |
| `migration-rationale.md`, `HEADLINES_FEATURE.md` | `docs/history/` |
| 기술 감사 TXT·사용사례 DOCX·발전 계획 DOCX·BigKinds 안내 PDF | `docs/history/` |

재생성 가능한 임베딩 캐시와 종료된 앱의 설치·빌드 산출물은 master에서 제거했습니다.
의존성이 비어 있던 루트 및 Python 백엔드의 `package-lock.json`도 제거했습니다.
`.claude/settings.local.json`과 `.mcp.json`은 로컬에 유지하며 Git 추적을 종료했습니다.

## 독립 커밋 검토 결과

- `backend_v3`의 수집량·동시성 변경은 master의 후속 구현에 반영되어 있었습니다.
  옛 테스트의 DeepSearch → BigKinds import 수정은 누락되어 있지만,
  남은 `section` 인자 등까지 고쳐야 하는 종료된 테스트이므로 복구하지 않았습니다.
- `frontend_v2`의 `mobile/` 트리는 `0dd87f0c`에 동일하게 반영되어 있었습니다.
  옛 `POST /api/auth/kakao/token` 백엔드 경로는 누락되어 있으나
  현재 Flutter의 Supabase OAuth와 별개이므로 복구하지 않았습니다.
- `frontend_v1`은 별도의 초기 앱 구현입니다. 옛 랭킹 화면 등의 고유 코드는 태그에 보존했습니다.

## 복구·열람

파일 하나를 확인하려면:

```bash
git show archive/pre-cleanup-2026-10-23:mobile/src/screens/LoginScreen.tsx
```

옛 코드를 별도 작업 폴더에서 열려면:

```bash
git worktree add --detach ../Briefly-legacy archive/pre-cleanup-2026-10-23
```

특정 브랜치의 고유 구현은 위 명령의 태그를 해당 보존 태그로 바꿔 열람합니다.
태그는 소스 보존 기준이며 환경변수·클라우드 리소스·실행 환경을 복원하지 않습니다.
