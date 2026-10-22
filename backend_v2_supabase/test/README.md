# 현행 파이프라인 검증 도구

`backend_v2_supabase/test/`는 실행형 검증·튜닝 스크립트를 보관합니다.
이전 실험 설명은 [연구 기록](../../docs/research/pipeline-experiments.md)에 보존했습니다.

| 파일 | 용도 | 실행 시 외부 영향 |
|---|---|---|
| `generate_integrated_briefing_dryrun.py` | 샘플 기사로 통합 대본 생성 | 로컬 임베딩과 OpenAI 호출, 결과를 `test/results/`에 저장 |
| `regenerate_audio.py` | 기존 대본의 오디오 재생성 | Supabase 기사 조회 및 NotebookLM 호출 |
| `test_supabase_storage_smoke.py` | DB·Storage 저장 경로 확인 | Supabase에 실제 데이터 쓰기 |
| `test_metrics_loki_smoke.py` | 파이프라인 계측 전송 확인 | 설정된 Loki로 메트릭 전송 |
| `transcribe_podcasts.py` | 옛 A/B/C 실험 오디오 전사·평가 | 로컬 Whisper 모델과 LLM 평가 호출 |
| `transcribe_and_evaluate.py` | 통합 브리핑 전사 및 품질 평가 | 로컬 Whisper 모델, Supabase 조회, LLM 평가 호출 |

외부 서비스·모델 실행이 필요한 스크립트입니다. 전체 파일을 단순한 오프라인 단위 테스트로 일괄 실행하지 마세요.
각 스크립트의 CLI 인자와 환경변수 설명을 확인한 뒤 실행합니다.

## 대본 검증 샘플

기본 샘플은 [fixtures/news_2026-04-11.json](fixtures/news_2026-04-11.json)입니다.
이전 `backend/test/data/`에서 내용 변경 없이 옮겼으며 출처는 [샘플 안내](fixtures/README.md)에 기록했습니다.
기본 입력 경로는 스크립트 위치를 기준으로 계산하므로 옛 `backend/` 폴더에 의존하지 않습니다.

저장소 루트에서:

```bash
cd backend_v2_supabase
python -X utf8 -m test.generate_integrated_briefing_dryrun --time-slot morning
```

다른 입력을 사용하려면 `--data-path <기사 JSON 경로>`를 전달하세요.
기본 검증은 정치·경제·국제 3개 카테고리만 사용합니다.
현재 파이프라인 전체 실행법은 [루트 README](../../README.md)를 따르세요.
