# Podcast Generation Comparison

로컬에서 동일한 한국어 뉴스 입력으로 여러 팟캐스트 생성 방식을 비교하는 실험 스크립트.

## 목적

`backend_v3_rework` 브랜치에서 새 팟캐스트 파이프라인 방향을 결정하기 위한 A/B 샘플링.

비교 대상:

1. **Podcastfy** (현재 사용 중) — `compare_podcastfy.py`
2. **NotebookLM (비공식 API)** — `compare_notebooklm.py`
3. **Direct (GPT + ElevenLabs)** — `compare_direct.py` (추가 예정)

동일 입력(`sample_news.json`)으로 각 스크립트를 돌리고 `outputs/` 에 MP3를 떨어뜨려서 사람이 직접 들어보고 비교합니다.

## 로컬 실행 환경

**AWS Lambda에서는 돌릴 수 없습니다** (특히 NotebookLM). 반드시 로컬 개발 머신에서만 실행하세요.

### 공통 요구사항

- Python 3.12+
- `../../.env` 또는 쉘 환경변수에 아래 키 설정
  - `OPENAI_API_KEY`
  - `ELEVENLABS_API_KEY` (podcastfy, direct용)
  - `ELEVENLABS_VOICE_ID_PERSON1`, `ELEVENLABS_VOICE_ID_PERSON2`

### Podcastfy

```bash
pip install podcastfy
python compare_podcastfy.py
```

### NotebookLM 비공식

⚠️ **경고**: `notebooklm-py` 는 Google 의 비공식/리버스 엔지니어링 API 를 사용합니다.
- 프로덕션 사용 금지 (Lambda 호환 불가, 쿠키 만료, ToS 리스크)
- 오직 품질 비교용 샘플 생성에만 사용
- 개인 구글 계정 대신 **실험용 테스트 계정** 사용 권장

```bash
pip install notebooklm-py
notebooklm login                   # 브라우저가 열립니다. 한 번만 로그인
notebooklm language list           # 한국어 코드 확인
python compare_notebooklm.py
```

## 비교 기준

`outputs/` 에 생성된 MP3 를 듣고 다음 항목을 수기로 채점 (1~5):

| 항목 | 설명 |
|---|---|
| 발음/자연스러움 | 한국어 억양, 이름/지명 읽기 |
| 대화 흐름 | 화자 간 턴테이킹 자연스러움 |
| 내용 정확도 | 뉴스 본문 왜곡 여부 |
| 톤 적절성 | 카테고리(정치/경제/사회…)에 맞는 톤 |
| 제어 가능성 | 프롬프트/설정으로 톤 조정이 가능한가 |
| 생성 시간 | 초 단위 |
| 비용 | 호출 1회당 추정 비용 |

결과는 `results.md` 에 정리.
