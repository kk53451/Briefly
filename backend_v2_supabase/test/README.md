# Briefly v2 실험 가이드

이 문서는 `backend_v2`의 뉴스 팟캐스트 파이프라인 실험 구조와 실행 방법을 설명합니다.
처음 보시는 분이 파이프라인을 이해하고 재현할 수 있도록 작성되었습니다.

---

## 1. 전체 아키텍처 한눈에 보기

```
Naver 뉴스 수집 (하루치, 7개 카테고리)
        ↓
  카테고리별로 완전히 분리된 파이프라인이 병렬 실행
        ↓
┌────────────┬────────────┬────────────┬────────────┐
│  정치      │  경제      │  사회      │  문화 ...  │
│  575건     │  605건     │  535건     │  459건     │
└──────┬─────┴──────┬─────┴──────┬─────┴──────┬─────┘
       ↓            ↓            ↓            ↓
  (각 카테고리 내부에서)
       ↓
  1. 임베딩 (KURE-v1)
  2. Near-duplicate 제거
  3. UMAP 차원 축소 + HDBSCAN 클러스터링
  4. Top 5 토픽(클러스터) 선정
  5. GPT 대본 생성 (Closed-World + Source-Tagged)
  6. Hallucination 검증 (GPT + 규칙)
  7. NotebookLM 팟캐스트 생성
  8. Whisper 전사 + G-Eval 품질 평가
```

**중요한 점:** 각 카테고리는 **완전히 독립**된 파이프라인을 돕니다.
경제 카테고리의 클러스터링 결과에 다른 카테고리 기사는 전혀 포함되지 않습니다.

---

## 2. 용어 정리 (헷갈리기 쉬운 부분)

### 2-1. "카테고리"

Naver 뉴스의 대분류. 우리는 7개를 사용합니다:

| 한글 | 영어 | Naver sid |
|---|---|---|
| 정치 | politics | 100 |
| 경제 | economy | 101 |
| 사회 | society | 102 |
| 문화 | culture | 103 |
| 국제 | international | 104 |
| IT/과학 | tech | 105 |

"지역(local)"은 다양성 부족, "스포츠(sports)"는 파이프라인 미지원으로 제외됨.

### 2-2. "클러스터" 와 "토픽"

**클러스터 = 토픽**. 같은 뜻입니다. 혼용해도 무방.

- HDBSCAN으로 기사들을 묶으면 "클러스터"라고 부름
- 팟캐스트 대본 관점에서는 "토픽"이라고 부름
- 예: "경제 카테고리에서 21개 클러스터가 나왔고, 이 중 상위 5개를 토픽으로 선정"

### 2-3. "기사 수" 의 여러 레이어

하나의 카테고리 안에서도 여러 단계의 "기사 수" 가 있습니다:

```
605건: BigKinds API에서 수집된 원본 경제 기사
   ↓ Near-duplicate 제거 (cosine > 0.95)
586건: 중복 제거 후
   ↓ HDBSCAN 클러스터링
21개 클러스터 + 노이즈: 586건이 21개 토픽 + 일부 미분류로 나뉨
   ↓ 토픽 크기 내림차순 정렬, 상위 5개 선정
5개 토픽:
   토픽 1 "MZ 3무"         → 68건
   토픽 2 "중동전 추경"     → 28건
   토픽 3 "전북 유학생"     → 25건
   토픽 4 "SKT AI 서버"     → 25건
   토픽 5 "고유가 지원금"   → 24건
   (합계 170건)
```

### 2-4. "소스 풀 (60건)"

GPT 대본 생성 시 **"지식의 전부"** 로 제공하는 기사 묶음.
현재 최대 60건까지 허용 (NotebookLM 무료 티어 50건 한도와 별개로, GPT 입력용).

**⚠️ 주의: 소스 풀 구성 방식이 실험 버전마다 달랐음 (아래 실험 히스토리 참고)**

---

## 3. 파일 구조

```
backend_v2/
├── app/
│   ├── services/
│   │   ├── naver_news_service.py       # Naver 뉴스 수집
│   │   ├── embedding_service.py        # KURE-v1 로컬 임베딩
│   │   ├── clustering_service.py       # UMAP + HDBSCAN + 토픽 랭킹
│   │   ├── script_service.py           # GPT 대본 생성 + 검증
│   │   ├── eval_service.py             # G-Eval 대본 품질 평가
│   │   ├── podcast_eval_service.py     # G-Eval 팟캐스트 전사본 평가
│   │   └── notebooklm_service.py       # NotebookLM A/B/C 3가지 방식
│   └── tasks/
│       └── scheduler.py                # 일일 배치 오케스트레이터
└── test/
    ├── compare_abc_methods.py          # A/B/C 팟캐스트 비교 실험
    ├── transcribe_podcasts.py          # Whisper 전사 + G-Eval
    ├── data/
    │   └── embedding_cache/            # KURE-v1 임베딩 캐시 (.npy)
    └── results/                        # 실험 결과물
        ├── script_*.txt                # 생성된 대본
        ├── abc_experiment_*.json       # 실험 요약
        ├── podcast_eval_*.json         # 팟캐스트 평가
        └── *_transcript.txt            # Whisper 전사본
```

---

## 4. A/B/C 실험이란?

NotebookLM에 어떤 방식으로 소스를 넣는 것이 최선인지 비교하는 실험.

### 방식 A: 원본 기사만 투입
```
토픽 5개 × 3개 기사 = 15건의 원본 기사 → NotebookLM
```
- 장점: GPT 대본 단계 없음 (간단)
- 단점: NotebookLM이 소스를 자유롭게 재해석

### 방식 B: GPT 대본만 투입
```
GPT가 합성한 통합 대본 1건 → NotebookLM
```
- 장점: 내용이 정제되어 있음
- 단점: NotebookLM이 대본을 "재해석"해서 실제 오디오가 원본과 달라질 수 있음

### 방식 C: 기사 + 대본 함께 투입
```
GPT 대본 1건 + 원본 기사 15건 → NotebookLM
```
- 장점: 풍부한 소스 + 정제된 가이드
- 단점: 소스가 많아 처리 시간 오래 걸림 (타임아웃 위험)

---

## 5. 실험 실행 방법

### 5-1. 환경 준비

```bash
cd backend_v2

# .env 설정 확인 (OPENAI_API_KEY, OPENAI_MODEL 등)
cat .env

# NotebookLM 로그인 (쿠키 만료 시 재실행 필요, 보통 주 1~2회)
notebooklm login
```

### 5-2. 대본만 먼저 생성 & 평가 (빠름, ~10분)

```bash
python -m test.compare_abc_methods --category economy --script-only
```

흐름:
1. 임베딩 (캐시 재사용 시 즉시)
2. 클러스터링
3. **GPT 대본 생성 (gpt-5.4 + reasoning=high)**
4. Hallucination 검증 (GPT + 규칙 기반)
5. G-Eval 대본 평가

출력:
- `test/results/script_economy_{timestamp}.txt` : 최종 대본
- `test/results/abc_experiment_economy_{timestamp}.json` : G-Eval 결과

### 5-3. 전체 A/B/C 비교 (느림, ~30분)

```bash
python -m test.compare_abc_methods --category economy
```

`--script-only` 없이 실행하면 위 단계 + 방식 A/B/C 각각 NotebookLM 팟캐스트 생성까지 진행합니다.

출력:
- `outputs/podcast_경제_method{A|B|C}_*.mp3` : 3가지 MP3

### 5-4. 팟캐스트 전사 + 품질 평가

```bash
python -m test.transcribe_podcasts
```

흐름:
1. faster-whisper turbo (GPU 가속) 로 MP3 → 텍스트
2. 각 전사본을 G-Eval (gpt-5.4 + reasoning=high) 로 평가
3. A/B/C 비교 테이블 출력

출력:
- `test/results/*_transcript.txt` : 전사본
- `test/results/podcast_eval_{timestamp}.json` : 평가 결과

---

## 6. 실험 히스토리 — 어떻게 진화했는가

### 1차: 초기 버전
- Judge: `gpt-4o`
- 소스 풀: 토픽당 3개 기사 × 5토픽 = 15건
- G-Eval 결과: **4.8/5.0** ✅
- **문제**: judge 가 약해서 오탐. 대본에 hallucination이 있는데도 놓침.

### 2차: Judge 업그레이드
- Judge: `gpt-5.4` + reasoning=high
- G-Eval 소스 풀: 카테고리 전체 중 60건 제공
- G-Eval 결과: **2.2/5.0** ❌ (실제 문제 드러남)
- **발견**: 대본에 실제로 hallucination이 많음. 숫자/통계가 원본과 불일치.

### 3차: 전체 gpt-5.4 + reasoning=high
- 대본 생성: `gpt-5.4` + reasoning=high
- 검증: `gpt-5.4` + reasoning=high
- G-Eval: `gpt-5.4` + reasoning=high
- **문제**: `max_completion_tokens`가 부족해서 reasoning 토큰이 다 먹고 실제 출력이 비어버림. 한도 상향 후 해결.
- G-Eval 결과: **3.0/5.0**
- **발견**: 대본 생성 단계에서 GPT가 여전히 외부 지식(학습 데이터)을 끌어와 사용. "스타벅스 디카페인 2억 잔" 같은 출처 없는 숫자 등장.

### 4차: Closed-World + Source-Tagged + 60건 풀
- 프롬프트 기법:
  1. **Closed-World Assumption**: "제공된 기사가 네 지식의 전부다"
  2. **Source-Tagged Facts**: 각 기사에 [S1]~[S60] 태그, 사실마다 태그 강제
  3. **Negative Example Injection**: hallucination 사례 명시
  4. **Chain-of-Verification**: 생성 중 자체 검증 9단계
- 대본 생성 & 검증 모두 **60건 전체** 기사 풀 사용
- G-Eval 결과: **3.0/5.0**
- **개선**: 정확성 **1 → 4** (최대 개선). 숫자/인용구 대부분 원본 일치.
- **새 문제**: 일관성 2/5. 산만함. (원인 분석 결과 → 5차 실험 필요)

### 5차 이후 예정: 토픽 기반 비례 샘플링 (예정)
- **문제 진단**: 4차의 "60건" 은 카테고리 586건 중 **앞에서 60개를 그냥 자른 것**. 인기도 순으로 섞여 있어서 5개 토픽과 무관한 기사까지 포함됨. GPT가 그 기사들까지 대본에 밀어넣어 산만해짐.
- **해결안**: 5개 토픽(170건)에 속한 기사들만 비례 배분으로 60건 선정.
  - 예: 토픽 1(68건)에서 24건, 토픽 2(28건)에서 10건, ...
  - 각 토픽 내에서는 centroid 최근접 순으로 선정 (가장 대표적인 기사부터)

---

## 7. 용어 사전 (빠른 참조)

| 용어 | 의미 |
|---|---|
| **카테고리 (category)** | Naver 뉴스 대분류 6종 (정치/경제/사회/문화/국제/IT과학) |
| **클러스터 / 토픽** | HDBSCAN이 묶은 유사 기사 그룹. 카테고리 내부에서만 생성 |
| **소스 풀 (source pool)** | GPT 대본 생성기에 제공하는 기사 묶음. 최대 60건 |
| **Closed-World** | "제공된 소스가 지식의 전부" 라는 프롬프트 제약 |
| **Source-Tagged Facts** | 기사에 [S1][S2] 태그 부여, 대본의 사실마다 태그 강제 |
| **Chain-of-Verification** | 생성 중 LLM이 자기 출력을 체크리스트로 검증 |
| **G-Eval** | LLM-as-a-Judge 방식의 자동 품질 평가 (5개 차원, 1~5점) |
| **Hallucination** | 원본 소스에 없는 사실을 LLM이 만들어낸 것 |
| **reasoning_effort** | gpt-5.x / o1 / o3 모델의 reasoning 강도 (low/medium/high/xhigh) |

---

## 8. 사용된 모델 & 비용 요약

| 단계 | 모델 | 비용 (1회 기준) |
|---|---|---|
| 뉴스 수집 | 직접 스크래핑 | 무료 |
| 임베딩 | KURE-v1 (로컬 GPU) | 무료 |
| 클러스터링 | UMAP + HDBSCAN (로컬) | 무료 |
| 대본 생성 | gpt-5.4 + reasoning=high | ~$0.15 |
| 대본 검증 | gpt-5.4 + reasoning=high | ~$0.10 |
| G-Eval (대본) | gpt-5.4 + reasoning=high | ~$0.10 |
| 팟캐스트 생성 | NotebookLM (비공식 API) | 무료 (쿠키 기반) |
| Whisper 전사 | faster-whisper turbo (로컬 GPU) | 무료 |
| G-Eval (팟캐스트) | gpt-5.4 + reasoning=high | ~$0.15 |

**1 카테고리 1회 전체 실험 비용: 약 $0.50**
**7 카테고리 × 1일 2회 (프로덕션): 약 $7/일 = $210/월**

*(reasoning=high 는 reasoning 토큰을 많이 사용해 표시 가격보다 실제 청구액이 높을 수 있음)*

---

## 9. 자주 발생하는 이슈

### NotebookLM 쿠키 만료
```
ValueError: Authentication expired or invalid.
→ terminal 에서: notebooklm login
```
2~3일 ~ 1주일 주기로 발생. 브라우저 로그인 후 Enter 키로 해결.

### gpt-5.4 max_completion_tokens 부족
증상: 대본이 0자로 나옴.
원인: reasoning 토큰이 한도의 대부분을 차지해 실제 출력이 잘림.
해결: `max_completion_tokens=30000` 이상으로 상향.

### OpenAI JSON parse 에러 (400)
원인: 기사 본문에 제어 문자(`0x00` 등)가 포함됨.
해결: `_sanitize()` 함수로 전처리 (현재 적용됨).

### Whisper CUDA 오류 "cublas64_12.dll not found"
원인: PyTorch CPU 버전이 설치되어 있음.
해결:
```bash
pip install torch --force-reinstall --index-url https://download.pytorch.org/whl/cu126
```

### HuggingFace 심링크 권한 에러 (Windows)
증상: `OSError: [WinError 1314] 클라이언트가 필요한 권한을 가지고 있지 않습니다`
해결: 관리자 권한 실행 또는 Windows 개발자 모드 활성화. 동작은 됨.

---

## 10. 다음 작업 목록

- [ ] **5차 실험**: 토픽 기반 비례 샘플링으로 소스 풀 구성 → 4차의 산만함 문제 해결 기대
- [ ] 다른 카테고리(politics, society) 에서도 동일 실험 수행하여 일반화 검증
- [ ] 방식 A/B/C 팟캐스트 G-Eval 자동화 (현재는 대본 G-Eval 까지만 자동)
- [ ] 프로덕션 스케줄러에 하루 2회 cron 등록 (Ubuntu 노트북)
- [ ] DynamoDB/S3 업로드 연동
