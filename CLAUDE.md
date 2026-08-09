# CLAUDE.md

이 파일은 Claude Code(claude.ai/code)가 이 저장소에서 작업할 때 참고하는 가이드입니다.

## 프로젝트 개요

**Briefly** — 한국어 뉴스를 자동 수집·클러스터링해서 하루 2회(오전/오후) **통합 브리핑 팟캐스트**로 만들고, 모바일 앱으로 전달하는 개인 프로젝트.

**현재 아키텍처는 2계층입니다. API 서버 계층이 없습니다.**

```
backend_v2_supabase/   로컬 배치 파이프라인 (cron, 하루 2회)
        ↓ 직접 쓰기
    Supabase           Postgres 3테이블 + Storage(오디오)
        ↑ 직접 읽기
    flutter/           모바일 앱 (supabase_flutter 로 DB 직접 조회)
```

Flutter 앱은 **Supabase 를 직접 호출합니다.** 중간에 REST API 서버가 없으므로, 데이터 형태를 바꾸려면 파이프라인의 저장 로직과 앱의 조회 로직을 같이 고쳐야 합니다.

**핵심 스택**
- 배치: Python 3.12 (CLI 스케줄러, FastAPI 아님)
- 수집: 네이버 뉴스 스크래핑 (`httpx` + `BeautifulSoup`)
- 임베딩: KURE-v1 로컬 추론 (`sentence-transformers`, 1024차원)
- 클러스터링: UMAP + HDBSCAN
- 대본: OpenAI `gpt-5.4`
- 헤드라인: Ollama `gemma4:e4b-it-q4_K_M` 로컬
- 오디오: NotebookLM (`notebooklm-py`, 비공식 API)
- 저장: Supabase (Postgres + Storage)
- 앱: Flutter + Riverpod + go_router + just_audio
- 알림: Discord 웹훅 2채널

## 저장소 구조

**현재 활성 — 여기서 작업합니다**
| 경로 | 역할 |
|---|---|
| `backend_v2_supabase/` | 배치 파이프라인 (유일한 백엔드) |
| `flutter/` | 모바일 앱 (유일한 클라이언트) |

**히스토리 — 보존용, 수정하지 않습니다**
| 경로 | 무엇이었나 |
|---|---|
| `backend/` | v1. FastAPI + AWS Lambda + DynamoDB + BigKinds + ElevenLabs |
| `backend_v2/` | v2 초기. 파이프라인은 현재와 유사하나 저장이 DynamoDB/S3 |
| `frontend/` | v1 웹 (Next.js 14) |
| `mobile/` | React Native + Expo 앱 |
| `mobile_v2_expo/` | Expo 재작성 시도 |
| `Briefly_design/` | 디자인 산출물 |

과거 버전의 코드·문서를 현재 동작의 근거로 삼지 마세요. BigKinds, ElevenLabs, DynamoDB, Kakao OAuth, Union-Find 클러스터링은 **전부 v1 유물이며 현재 파이프라인에 없습니다.**

## 개발 명령어

### 배치 파이프라인

```bash
cd backend_v2_supabase
pip install -r requirements.txt

# 전체 실행 (현재 KST 시각으로 오전/오후 자동 판정)
python -m app.tasks.scheduler

# 슬롯 명시
python -m app.tasks.scheduler --time-slot morning
python -m app.tasks.scheduler --time-slot afternoon

# 특정 카테고리만 (Feed 단계 한정)
python -m app.tasks.scheduler --categories economy politics

# 오디오 생략 (대본까지만)
python -m app.tasks.scheduler --skip-podcast

# Feed 단계만 (대본·오디오 통째로 생략)
python -m app.tasks.scheduler --skip-script
```

cron 등록 (Ubuntu):
```bash
0 5  * * * cd ~/Briefly/backend_v2_supabase && /usr/bin/python3 -m app.tasks.scheduler --time-slot morning   >> /var/log/briefly.log 2>&1
0 16 * * * cd ~/Briefly/backend_v2_supabase && /usr/bin/python3 -m app.tasks.scheduler --time-slot afternoon >> /var/log/briefly.log 2>&1
```

Windows 에서 테스트할 때는 콘솔이 cp949 라 이모지 로그가 `UnicodeEncodeError` 로 죽습니다:
```bash
$env:PYTHONIOENCODING='utf-8'; python -m app.tasks.scheduler --skip-script
```

### Flutter 앱

```bash
cd flutter
flutter pub get
flutter run
flutter build apk --release
```

## 파이프라인 구조

`app/tasks/scheduler.py` 가 오케스트레이터입니다. **2 Phase 로 나뉩니다.**

### Feed Phase — 6개 카테고리 전부

카테고리별로 순차 실행하되, 수집만 `ThreadPoolExecutor(max_workers=6)` 로 병렬 prefetch 합니다. 임베딩·클러스터링은 GPU 메모리를 공유하므로 순차 유지합니다.

| # | 단계 | 구현 |
|---|---|---|
| 1 | 뉴스 수집 | `naver_news_service.py` |
| 2 | 임베딩 (1024d) | `embedding_service.py` — 완료 후 `unload_model()` 로 GPU 해제 |
| 3 | Near-duplicate 제거 | `clustering_service.py` — cosine ≥ 0.95 |
| 4 | UMAP + HDBSCAN 클러스터링 | `clustering_service.py` — 동적 mcs, 거대 클러스터 fallback |
| 5 | 가중 토픽 랭킹 | `clustering_service.py` — `0.25·size + 0.60·corpus + 0.15·diversity` |
| 5-b | `news_cards` 저장 | `supabase_storage_service.py` — rank 1~20 |
| 6 | 헤드라인 생성/저장 | `headline_service.py` (Ollama) → `headlines` 테이블, top 5 |
| 7 | 통합 브리핑용 소스 풀 | `clustering_service.py` — **하드뉴스 3개 카테고리만** |

### Briefing Phase — 하루 1회 (슬롯당)

**정치·경제·국제** 3개 카테고리의 top 토픽을 하나로 엮어 **단일 통합 대본**을 만듭니다. 사회·문화·IT/과학은 Feed 단계만 수행하고 팟캐스트에는 들어가지 않습니다.

```
카테고리당 top 4 토픽 × 3분야 = 12 토픽
→ gpt-5.4 대본 생성 (목표 7,500자)
→ NotebookLM 오디오 (~15분 소요, 8~10분 분량)
→ podcasts 테이블 1행 저장
```

**과거 모델과 혼동 주의**: v1/v2 는 "카테고리별 팟캐스트 1개"였습니다. 현재는 **하루 슬롯당 통합 브리핑 1개**입니다.

## 데이터 모델 (Supabase)

`app/services/supabase_storage_service.py` 참조.

| 테이블 | 키 | 내용 |
|---|---|---|
| `podcasts` | UNIQUE (`date`, `slot`) | 통합 브리핑. 하루 최대 2행 |
| `headlines` | UNIQUE (`category`, `date`, `slot`) | 카테고리별 피드 헤드라인 (top 5) |
| `news_cards` | PK `news_id` | 카테고리별 피드 카드 (rank 1~N upsert) |

`podcasts` 주요 필드: `script`, `audio_url`, `title`, `covered_keywords`, `duration_sec`

`covered_keywords` 는 다음 실행의 **중복 토픽 제거**에 쓰입니다. 최근 24시간 내 팟캐스트의 키워드 집합과 2개 이상 겹치는 토픽은 제외합니다.

### Storage

버킷 `briefly-audio` (public):
```
{date}/briefing_{slot}.mp3      예: 2026-05-15/briefing_AM.mp3
```

슬롯은 `AM` / `PM` 이고, 한글 `오전` / `오후` 와 매핑됩니다.

## 중요한 구현 세부사항

### 카테고리

```python
# app/constants/category_map.py — 6개. 지역·스포츠 제외.
CATEGORY_MAP = {
    "정치":     {"api_name": "politics",      "naver_sid": "100"},
    "경제":     {"api_name": "economy",       "naver_sid": "101"},
    "사회":     {"api_name": "society",       "naver_sid": "102"},
    "문화":     {"api_name": "culture",       "naver_sid": "103"},
    "국제":     {"api_name": "international", "naver_sid": "104"},
    "IT/과학":  {"api_name": "tech",          "naver_sid": "105"},
}
```

UI 는 한글, API/DB 는 영문(`api_name`)을 씁니다. **스포츠 카테고리는 영구 제외입니다** — 추가를 제안하지 마세요.

이 중 팟캐스트에 들어가는 하드뉴스는 `HARD_NEWS_CATEGORIES_KO = ["정치", "경제", "국제"]` 3개뿐입니다 (`scheduler.py`).

### 시간대

모든 날짜는 KST 기준입니다 (`app/utils/date.py`).

```python
get_today_kst()      # "YYYY-MM-DD"
get_now_kst()        # tz-aware datetime
get_briefing_slot()  # 정오 기준 "오전" / "오후"
```

### 수집 시간 윈도우 — 현재 비활성

`scheduler.py` 의 `BRIEFING_WINDOW_ENABLED = False` 입니다. 출시 전 단계라 임의 시각에 돌려도 기사가 확보되도록 윈도우 필터를 끄고 네이버 "오늘 카테고리 리스트" 전체를 씁니다. 켜면 오전은 전날 18시~당일 5시, 오후는 당일 5시~16시 범위로 `published_at` 을 필터링합니다.

이 플래그를 만지기 전에 다운스트림이 `win_stats` 의 키를 참조한다는 점을 확인하세요 — 윈도우 OFF 모드도 같은 형태의 dict 를 반환해야 합니다.

### 로컬 모델 의존성

임베딩(KURE-v1)과 헤드라인(Gemma4)은 **로컬에서 돕니다.** 실행 머신에 다음이 필요합니다:
- CUDA GPU (없으면 CPU 폴백 — 매우 느림)
- Ollama 실행 중 + `gemma4:e4b-it-q4_K_M` pull 완료

`konlpy`(Okt)는 **선택적**입니다. `clustering_service._get_okt()` 가 lazy 로딩하고 없으면 `None` 을 반환해 정규식 토크나이저로 폴백합니다. JVM 부팅이 무거워 모듈당 1회만 인스턴스화합니다.

### 에러 처리 철학

배치가 중간에 죽으면 그날 콘텐츠가 통째로 없어지므로, 치명적이지 않은 실패는 삼키고 진행합니다.
- `news_cards` 저장 실패 → 로그만 남기고 계속 (팟캐스트는 만들어야 함)
- NotebookLM 인증 실패 → `--skip-podcast` 모드로 자동 전환, 대본은 저장
- 오디오 생성 실패 → 대본은 그대로 저장
- Discord 전송 실패 → 파이프라인에 영향 없음

반면 임베딩·클러스터링·헤드라인 실패는 `raise` 해서 해당 카테고리를 `failed` 로 마킹합니다. 결과가 쓸모없어지기 때문입니다.

### 대본 품질 장치

`script_service.py` + `script_postprocess.py`:
- **Closed-World 프롬프트** — 소스 기사에 없는 내용 생성 금지
- **Source-Tagged** — `[S1]...[SN]` 태그로 사실 주장 추적
- **규칙 기반 숫자 검증** — 대본의 수치를 원본 기사에서 직접 대조
- **후처리** — 연속 화자 병합, 메타언어 탐지, 숫자 과밀 경고

LLM 호출은 `app/services/engines/` 로 추상화되어 있습니다 (`ScriptEngine` ABC + `OpenAIScriptEngine`). 모델을 바꾸려면 엔진을 추가하세요.

## 테스트

`backend_v2_supabase/test/` — pytest 스위트가 아니라 **실행형 스크립트**입니다.

| 파일 | 용도 |
|---|---|
| `test_supabase_storage_smoke.py` | Supabase 쓰기 경로 스모크 |
| `generate_integrated_briefing_dryrun.py` | 대본 생성만 드라이런 |
| `regenerate_audio.py` | 기존 대본으로 오디오만 재생성 |
| `transcribe_podcasts.py` | 생성된 오디오 전사 |
| `transcribe_and_evaluate.py` | 전사 + 품질 평가 |

대본/전사본 품질 평가는 `.claude/skills/briefly-eval-v3` 스킬을 씁니다.

## 컨벤션

- Python `snake_case`, 클래스 `PascalCase`
- 로그에 이모지 접두사: ✅ 성공 / ⚠️ 경고 / ❌ 실패
- 로그에 컨텍스트 포함: 카테고리, 기사 수, 소요 시간
- 커밋 메시지는 한국어
- 현재 브랜치는 `backend_v3_rework` 이지만 **백엔드는 "v2" 로 부릅니다** (브랜치명만 v3)
- master 에 force push 금지

## 환경 변수

`backend_v2_supabase/.env` (git 제외됨):

```bash
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-5.4
OPENAI_JUDGE_MODEL=gpt-5.4

SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=...
SUPABASE_AUDIO_BUCKET=briefly-audio

DISCORD_WEBHOOK_URL=...            # alerts 채널
DISCORD_PIPELINE_WEBHOOK_URL=...   # pipeline 채널
```

Flutter 쪽 Supabase 설정은 `flutter/lib/core/config/` 에 있습니다.

## 자주 겪는 문제

**Ollama 호출이 빈 응답을 반환**
`headline_service._call_ollama` 는 `num_predict=2000` 으로 부릅니다. 이 모델은 thinking 토큰을 쓰기 때문에 값을 줄이면 thinking 도중 잘려 `response` 가 빈 문자열로 옵니다.

**Ollama 가 500 + `GGML_ASSERT` 로 죽음**
모델이 해당 하드웨어/빌드에서 로드 불가한 경우입니다. `curl http://localhost:11434/api/tags` 로 모델 존재를 확인하고, 다른 태그로 시도해 보세요.

**임베딩 캐시가 이상한 결과를 줌**
`data/embedding_cache/*.npy` 캐시 키는 텍스트 내용 기반이고 **모델명을 포함하지 않습니다.** 임베딩 모델을 바꾸면 차원이 다른 캐시를 잘못 로드합니다. 모델 교체 시 캐시를 비우세요.

**Supabase 쓰기가 전부 실패**
무료 플랜은 비활동 시 프로젝트가 자동 일시정지(INACTIVE)됩니다. 대시보드에서 Restore 하세요.

**대본은 있는데 오디오가 없음**
NotebookLM 인증 만료입니다. `notebooklm login` 을 수동 실행하세요. 파이프라인은 이 경우 Discord 로 경고하고 대본만 저장합니다.
