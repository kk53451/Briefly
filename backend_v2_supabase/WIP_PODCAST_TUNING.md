# Briefly 통합 브리핑 — 오디오 품질·길이 튜닝 진행 로그

> 이 문서는 **작업 중간 인계용**. 다른 세션에서 이어 받을 때 배경·시도 이력·미결정 사항을 빠르게 파악하라고 작성.
> 마지막 업데이트: 2026-04-21 04:15 KST

---

## 1. 프로젝트 컨텍스트

**Briefly** 는 한국 직장인 대상 일일 뉴스 팟캐스트 플랫폼. 2026-04-19 에 구조를 크게 바꿈:

- **이전**: 카테고리별 개별 팟캐스트 (정치 하나, 경제 하나 … 8개)
- **현재(v3)**: **정치·경제·국제 3 하드뉴스를 엮은 통합 브리핑**, 하루 오전·오후 2회
  - 사회·문화·IT/과학 은 **피드용(Home/Today 탭)** 으로만 수집, 팟캐스트 미포함

**활성 백엔드**: `backend_v2_supabase/` (AWS → Supabase 로 이전한 fork)

**파이프라인 구조**:
```
Feed Phase  (6 카테고리 병렬 수집, 순차 임베딩/클러스터링)
   └→ NewsCards + Headlines 저장 (Home/Today 탭용)
   └→ 하드뉴스 3개만 통합 브리핑용 토픽·REF 풀 구성

Briefing Phase  (하루 1회, time_slot 당)
   └→ GPT-5.4 로 통합 대본 생성 (정치→경제→국제 순)
   └→ NotebookLM 에 [PRIMARY] 대본 + [REF] 원본 기사 = 총 28~37개 소스 업로드
   └→ NotebookLM 이 두 진행자 대화 오디오 생성 (AudioLength 에 따라 길이)
   └→ Supabase podcasts 테이블 + Storage 저장
```

---

## 2. 지금 튜닝 중인 것

**NotebookLM 이 대본을 받아 오디오로 만들 때 발생하는 품질·길이 문제**를 잡고 있음. 아래 6가지 지표로 평가 (`test/transcribe_and_evaluate.py` + G-Eval GPT-5.4 judge):

| 차원 | 의미 |
|---|---|
| source_fidelity | 원본 기사 사실 충실도 |
| conversational_flow | 두 진행자 대화 자연스러움 |
| completeness | 토픽 커버리지·오프닝·클로징 |
| listenability | 귀로 들을 때 이해도 (TTS 오독 포함) |
| neutrality | 정치적/편향적 표현 없음 |
| engagement | 몰입감·후킹 |
| script_adherence | 원본 대본 구조 준수도 |

최종 목표: **8~10분 오디오 / broadcast_ready=True / Overall ≥ 4.0**

---

## 3. 적용된 설계 결정 (계속 유효)

### α — Instructions 내부 길이 수치 정합
이전 `INSTRUCTIONS_V2_TEMPLATE` 에 길이 지시가 모순됐음 (선언 8~10분인데 내부 배분 수치 합하면 10~12분). 내부 수치를 재조정:

- 전체 선언: **"약 8~10분 분량"**
- 분야별: "각 분야 **약 2~3분씩**"
- 토픽별: "약 **40~50초 내외**"

위치: [`notebooklm_service.py` L184-240 근처](app/services/notebooklm_service.py)

### A — Strict Source Contract
"PRIMARY 대본 밖 내용 창작 금지" 를 instructions 최상단에 절대 원칙으로 명시. 실제 실패 사례(하메네이 사망·공영주차장 5부제 등)를 구체 예시로 포함.

### β — 은유 금지 + 토픽 독립 + 중립성 강화
1차 실측에서 드러난 3개 대형 문제 각각 섹션화:
- `## 은유·비유 금지`: 도시락통·스파게티·피자·벙커 등 실패 비유 블랙리스트
- `## 토픽 독립 원칙`: "생존을 위한 거래" 류 메타 서사 금지
- `## 중립성 — 평가·해석·냉소 금지 강화`: "짜고 치는 고스톱"·"표 계산" 등 냉소 관용구 금지

### Plan A — 토픽 4개 × 대본 7,500자
3차 이전까지는 카테고리당 3 토픽이라 SHORT 모드에서 6분 미달. Plan A 로:
- `PODCAST_TOPICS_PER_CATEGORY = 4` (3→4, 총 12 토픽)
- `BRIEFING_TARGET_LENGTH = 7500` (6000→7500)
- `REF = 36` 건 (27→36, 토픽 수 증가 비례)
- `SYSTEM_PROMPT` 의 글자 목표 `7000-8500자`

위치: [`scheduler.py`](app/tasks/scheduler.py) 상수 섹션

### 기타 부수 개선
- **Fast-fail sniffer**: NotebookLM `RPC CREATE_ARTIFACT failed` 를 감지해 30분 헛대기 방지 → 1초 내 `RuntimeError`
- **duration_sec probe**: `ffprobe` 1차 + `mutagen` fallback. 이전 mutagen 만 썼을 때 DASH-MP4 에서 `0.0` 반환하는 버그 우회
- **title 생성 A1**: Gemma4 헤드라인 프롬프트를 평서문 명사형 압축으로 재작성 (의문문 형태 금지)
- **`_tts_safe_numbers`**: 숫자 단위 탈락 방지 (예: `50조 → 오조` 되는 것 막기 — 다만 여전히 일부 오독 발생)
- **Discord 웹훅 개선**: 완료 알림에 title 한 줄 요약 + `⏱️ 분/초` 포맷 소요시간
- **병렬 수집**: ThreadPoolExecutor max_workers=3, 카테고리 수집 시간 48분→16분 축소

---

## 4. 실험 연대기 (G-Eval 점수 추이)

| # | 날짜 | 설정 | 오디오 길이 | Overall | 비고 |
|---|---|---|---|---|---|
| 1 | 04-19 21:12 | α+A, DEFAULT, 4999자, 27REF | **22분 42초** | **2.3** | hallucinate 대량(하메네이 사망 등), 심층탐구 톤, 비유 범벅 |
| 2 | 04-20 22:24 | α+A+β, SHORT, 4999자, 27REF | **6분 8초** | 2.9 | 1차 문제 대부분 박멸 ✓, 하지만 맥락 얕음 |
| 3 | 04-21 00:46 | +Plan A, SHORT, 5896자, 27REF | **5분 50초** | **2.9** | 대본 늘려도 SHORT 가 ~6분 상한 (발견) |
| 4 | 04-21 04:10 | +Plan A, DEFAULT, 5896자, 27REF, **Pro 계정** | **12분 19초** | **3.0** | β 가 DEFAULT 분량 절반으로 누름(22→12분), 남은 문제는 TTS 고유명사 오독 |

**과거 single-category 방식 B (2026-04-15, 경제만, 대본만)** 는 **Overall 3.3** 이었음. 지금 통합이 살짝 낮지만, 단일-카테고리 방식 A(2.8)·C(2.7) 보다는 높음. 즉 "과거가 무조건 더 좋았다"는 환상이고, 실제로는 **설계 트레이드오프의 이동**.

### 차원별 변화 (B 방식 3.3 ↔ 현재 3.0)

| 차원 | B (과거 최고) | 3차 (현재) | 해석 |
|---|---|---|---|
| source_fidelity | 2 | 2 | 동일 (진짜 hallucinate 는 폭감, 지금은 TTS 오독이 점수 깎음) |
| conversational_flow | 4 | 2 | 12 토픽 전환 기계적, β 가 자연스러운 비유 브릿지 금지 |
| completeness | 3 | **4** | 12 토픽 커버 효과 ✓ |
| listenability | **4** | **2** | **TTS 고유명사 오독 — 유일한 진짜 회귀** |
| neutrality | 4 | 4 | 동일 |
| engagement | 4 | 3 | β 로 후킹·드라마틱 요소 제거 (의도된 감소) |
| script_adherence | 2 | **4** | 대본 충실도 훨씬 개선 ✓ |

---

## 5. 현재 병목 — **listenability 2 / TTS 고유명사 오독**

G-Eval 3차가 지목한 구체 오류 (전사본 기준):
- **`정원오` → "정원호"** (서울시장 후보, 오인식)
- **`김재연` → "김재현"**
- **`제31해병원정대` → "제30일 해경정대"** (군사용어 완전 붕괴)
- 발화 오류: `"상해하는"`, `"주민삼 개선"`, `"로펀"`, `"수밀바서척"`, `"이 주율의 휴전"`, `"통일교 출신 장관"`

**왜 이제 드러났나**: 이전 1차(22분) 는 NotebookLM 이 대본에 없는 쉬운 일반 단어로 **창작·부풀림** 해서 TTS 실패가 상대적으로 덜 보였음. 지금은 β 덕에 대본을 97% 충실히 읽으니(5896자 대본 → 5734자 전사본) **TTS 가 어려운 실제 고유명사를 직접 마주침** → 오독 폭발.

**근본 원인**: NotebookLM TTS 엔진의 한국어 고유명사·군사용어·복합 직함 처리 한계. Instructions 로는 직접 고치기 어려움.

---

## 6. 결정 대기 사항 — 3가지 경로

### E1 — 대본 단계 TTS 친화화 (권장)
`script_service.py` 프롬프트 개선:
- 복합 명사 분리: `"제31해병원정대"` → `"31 해병 원정대"`
- 직함·이름 어순 조정: `"통일교 출신 장관"` → `"통일교 출신인 장관"`
- GPT 에게 "TTS 발음 가독성 고려" 지시
- 저비용 실험, 효과 있으면 listenability 2→3~4, Overall 3.0→3.5 예상

### E2 — 고유명사 발음 사전 (유지보수 부담)
`_tts_safe_numbers` 처럼 `_tts_safe_names` 헬퍼 작성, 자주 오독하는 고유명사 수동 매핑 테이블.

### E3 — 현 수준 수용 + MVP 배포
- Overall 3.0 은 consumer podcast MVP 로 쓸만한 수준
- 실제 청취자 피드백이 더 가치 있을 수 있음
- cron 배포하고 추후 튜닝

### 그 외 보류 중인 것
- 타깃 시간: "8~10분" → 실제로는 12분대 수용 여부 (12분이 oversight_ready 관점에서 오히려 자연스러움)
- AudioLength: `DEFAULT` 고정 (Pro 계정 전제)

---

## 7. 주의 사항 — NotebookLM 계정 quota

**Free 계정에서는 오늘 DEFAULT/LONG 이 막혔음** (`CREATE_ARTIFACT` RPC 가 0.7초 만에 거절). SHORT 만 작동. 3번 연속 거절로 확정:
- Free 계정에서는 `AudioLength.DEFAULT`/`LONG` 이 일일 쿼터에 의해 차단되는 패턴
- **Pro 계정으로 전환 후 DEFAULT 정상 작동** (3차 실험)

`notebooklm login` 으로 쿠키 교체. 쿠키 만료 시 자동 refresh 가 브라우저 띄우므로 수동 개입 필요할 때 있음.

---

## 8. 주요 파일·함수

### Instructions·프롬프트
- **`app/services/notebooklm_service.py`** — `INSTRUCTIONS_V2_TEMPLATE` (약 7,666자). 핵심 섹션:
  - `## 사실 계약` (A)
  - `## 프로그램 정체성` (α)
  - `## 금지 표현`
  - `## 구조 (약 8~10분)` (α)
  - `## 사실과 숫자` + `### 단위 보존`
  - `## 커버리지` (α)
  - `## 중립성 — 평가·해석·냉소 금지` (β)
  - `## 은유·비유 금지` (β)
  - `## 토픽 독립 원칙` (β)
  - `## 소스 활용 원칙` (A)
- **`app/services/script_service.py`** — `SYSTEM_PROMPT` + `GENERATION_PROMPT_TEMPLATE`. Closed-World + Source-Tagged 프롬프트.
- **`app/services/headline_service.py`** — Gemma4 로컬 헤드라인 프롬프트 (A1 명사형 압축).

### 스케줄러·파이프라인
- **`app/tasks/scheduler.py`** — 메인 진입점. 주요 상수:
  ```python
  HARD_NEWS_CATEGORIES_KO = ["정치", "경제", "국제"]
  PODCAST_TOPICS_PER_CATEGORY = 4          # Plan A
  PODCAST_REF_ARTICLES_PER_TOPIC = 3       # 토픽당 REF 3 건
  BRIEFING_TARGET_LENGTH = 7500            # 대본 목표 자수
  DEDUP_KEYWORD_OVERLAP_THRESHOLD = 2      # previous-topics dedup
  COLLECT_PARALLELISM = 3                  # 병렬 수집
  WINDOW_MIN_ARTICLES = 10                 # 윈도우 fallback 임계
  ```

### NotebookLM 통합
- **`app/services/notebooklm_service.py`**:
  - `generate_podcast(script, time_slot, reference_articles, ...)` — 외부 API
  - `_generate_podcast_async` — 본체. 현재 `audio_length=AudioLength.DEFAULT`
  - `_build_podcast_sources(script, time_slot, reference_articles)` — PRIMARY 1 + REF N 리스트 구성
  - `probe_audio_duration_seconds(path)` — ffprobe 1차, mutagen 2차
  - Sniffer: `CREATE_ARTIFACT` 거절 감지 (인라인 클래스)
  - `wait_for_completion(timeout=1800.0)` — 30분 상한

### Supabase
- **`app/services/supabase_storage_service.py`**:
  - `save_podcast(date, slot, script, audio_path, title, covered_keywords, duration_sec)` — 저장
  - `fetch_recent_covered_keywords(lookback_hours=24)` — dedup 조회
- **스키마** (원격 적용 완료):
  - `podcasts(id, date, slot, script, audio_path, created_at, title, covered_keywords jsonb, duration_sec int)`
  - UNIQUE(date, slot) — 하루 2 행(AM/PM)
- **관련 마이그레이션**:
  - `app/db/migrations/0005_rename_frequencies_to_podcasts.sql` (frequencies→podcasts)
  - `0007_add_podcast_title_and_covered_keywords.sql`
  - `0008_add_podcast_duration_sec.sql`

### 테스트·실측 도구
- **`test/generate_integrated_briefing_dryrun.py`** — 샘플 데이터(`backend/test/data/news_*.json`) 로 오프라인 대본 생성. NotebookLM 미호출. Fast feedback loop.
- **`test/regenerate_audio.py`** — 기존 대본 재사용 + Supabase REF 재구성 + NotebookLM 만 재호출. Instructions·AudioLength 튜닝 사이클의 핵심 도구. 약 10~15분.
- **`test/transcribe_and_evaluate.py`** — MP3 전사(faster-whisper GPU) + G-Eval 평가. 6~8분. 자동으로 최신 MP3·대본 쌍 감지.
- **`test/test_supabase_storage_smoke.py`** — Supabase 저장 smoke test.

---

## 9. 재현용 명령어

### 깨끗한 전체 파이프라인 (약 40~60분)
```bash
cd backend_v2_supabase
python -X utf8 -m app.tasks.scheduler \
    --time-slot afternoon \
    --categories politics economy international
```
- 6 카테고리 중 3 하드뉴스만 Feed + Briefing. 새 날짜로 저장.
- NotebookLM DEFAULT 필요 → Pro 쿠키 상태여야 함.

### 대본 고정 + NotebookLM 재호출 (약 15분)
```bash
python -X utf8 -m test.regenerate_audio \
    --script outputs/scripts/briefing_PM_2026-04-20_001030.txt \
    --date 2026-04-20 --slot PM
```
- Instructions 튜닝 빠른 검증.

### 오디오 품질 평가 (약 6분)
```bash
python -X utf8 -m test.transcribe_and_evaluate \
    --mp3 outputs/podcast_오후_podcast_20260421_035708.mp3 \
    --script outputs/scripts/briefing_PM_2026-04-20_001030.txt \
    --date 2026-04-20 --slot PM
```
- 전사 + 7차원 G-Eval. `test/results/podcast_eval_{ts}.json` 저장.

### 대본만 빠르게 생성 (오프라인 샘플 데이터, 약 5분)
```bash
python -X utf8 -m test.generate_integrated_briefing_dryrun \
    --time-slot 오후 --target-length 7500
```
- NotebookLM 없이 대본 품질만 확인.

### NotebookLM 쿠키 재로그인
```bash
# 기존 쿠키 제거 (선택)
rm "$USERPROFILE\.notebooklm\storage_state.json"
# (PowerShell: Remove-Item "$env:USERPROFILE\.notebooklm\storage_state.json")

notebooklm login
# 브라우저 열림 → Google 로그인 → Enter
```
- playwright navigation interrupted 에러 뜨면 단순 재실행으로 대개 풀림.

---

## 10. 최신 실측 산출물 (2026-04-21 03:57 기준)

### 오디오 (로컬)
- `outputs/podcast_오후_podcast_20260419_205528.mp3` — 1차 DEFAULT 20:39 (baseline, hallucinate 대량)
- `outputs/podcast_오후_podcast_20260420_221513.mp3` — 2차 SHORT 6:08
- `outputs/podcast_오후_podcast_20260421_003449.mp3` — 3차 SHORT 5:50 (Plan A)
- **`outputs/podcast_오후_podcast_20260421_035708.mp3`** — **4차 DEFAULT 12:19 (Pro, 현재 최신)**

### Supabase Storage
- `briefly-audio/2026-04-19/briefing_PM.mp3` (1차)
- 이후 실측은 local 만 생성, Storage 업로드는 scheduler.py 경유 필요

### 대본 (로컬)
- `outputs/scripts/briefing_PM_2026-04-19_205528.txt` — 1차 대본 (4999자)
- **`outputs/scripts/briefing_PM_2026-04-20_001030.txt`** — **2·3·4차 대본 (5896자, 현재)**

### 전사본
- `test/results/podcast_*_transcript.txt`
- `test/results/podcast_eval_*.json` — G-Eval JSON

---

## 11. "다음 세션에서 할 일" 후보 (우선순위 높은 순)

1. **사용자 결정 받기** — E1 / E2 / E3 중 어느 경로
2. **E1 진행 시**: `script_service.py` 의 `SYSTEM_PROMPT` 에 TTS 친화화 섹션 추가
   - 복합 명사 공백 분리 룰
   - 직함·이름 명확화
   - 고유명사 발음 힌트 병기 (`정원오(JEONG-WON-OH)` 등 — 단 TTS 가 이걸 실제로 활용할지는 실측 필요)
3. **E1 실측**: `regenerate_audio.py` — 기존 대본을 버리고 **새 대본 생성 필요** (GPT 프롬프트가 바뀌었으니). 전체 파이프라인 1회.
4. **수렴 판단**: Overall 3.5 이상이면 cron 배포 준비 (`cron` 설정, NotebookLM 쿠키 유지 정책).
5. **이후 추후 과제 (별도)**:
   - flutter 앱 UI 측 (사용자가 최근 flutter 작업 재개, backend-only 스코프 해제됨)
   - 시간 윈도우 수집 (지금은 "오늘의 네이버 리스트" 쓰고 있음, 원래는 "전날 18시~당일 05시" 같은 시간 범위 필터 필요 — 아직 미구현)
   - cron 배포

---

## 12. 구조적 문제 기록 (언젠가 다뤄야 할 것)

### NotebookLM 자체의 약점
- 한국어 고유명사·군사용어·직함 TTS 오독
- Free 계정의 DEFAULT/LONG 쿼터 제한 (Pro 필요)
- DASH-fragmented MP4 출력 → mutagen duration probe 실패 (ffprobe fallback 필요)
- Library `notebooklm-py` 의 `CREATE_ARTIFACT` 실패 시 swallowed (우리가 sniffer 로 우회)

### 설계상 트레이드오프
- **통합 브리핑 vs 카테고리별**: 통합은 completeness·script_adherence 이득, 반대급부로 conversational_flow·engagement 손해. 전반적 품질 비슷하거나 약간 상승(B 3.3 → 현재 3.0).
- **β 규정 엄격성**: 비유·메타서사·후킹 금지가 방송 품질과 engagement 사이의 트레이드오프. 지금은 방송 품질 쪽으로 치우침.

### 미해결 의문
- **타깃 8~10분이 진짜 맞나?** 12분대도 consumer podcast 로 자연스러움. 사용자 테스트 필요.
- **REF 27 vs 36 차이가 유의미한가?** Plan A 로 36 만들었지만 아직 직접 비교 안 함.
- **Supabase 쪽 `frequencies` → `podcasts` rename 후 기존 `cleanup_old_audio()` cron 작동하는가?** 0006 마이그레이션으로 함수 업데이트함. 실행 검증 아직.

---

## 13. 참고 지점

- **Pipeline 결과 JSON**: `outputs/pipeline_result_PM_*.json` — 각 run 결과 요약
- **Discord 웹훅**: 두 채널(#alerts, #pipeline) 로 이정표 전송. env `DISCORD_WEBHOOK_URL`, `DISCORD_PIPELINE_WEBHOOK_URL`.
- **project 메모리**: `~/.claude/projects/d--Github-Briefly/memory/` (Claude 세션 메모리, 사용자가 scope·정책 설정)
- **Git 현재 브랜치**: `backend_v3_rework` (master 아님)

---

**마지막 성공 실험 요약**:
```
04-21 03:57  Pro 계정 + α+A+β+Plan A+DEFAULT
             대본 5896자 + REF 27
             → 오디오 12:19, Overall 3.0
             → hallucinate·비유·메타서사 0회 ✓
             → 남은 문제: TTS 고유명사 오독 (listenability 2)
```

**다음 한 수**: E1 (대본 TTS 친화화) 적용 후 재실측 권장.
