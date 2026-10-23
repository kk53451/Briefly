# Briefly 문서와 보존 자료

현행 실행 코드는 `backend/`와 `flutter/`입니다.
시작 방법과 현재 구조는 [루트 README](../README.md)를 따르세요.

| 문서 | 용도 |
|---|---|
| [설치 검증 기록](setup-validation.md) | 현재 README 절차의 실제 검증 결과와 남은 실행 조건 |
| [DEPRECATED](DEPRECATED.md) | 종료한 구현, 보존 태그, 복구 방법 |
| [디자인](design/README.md) | 와이어프레임 원본, 디자인 결정, 화면 기록 |
| [연구·평가](research/README.md) | 클러스터링 실험, 데이터 감사, 팟캐스트 튜닝 |
| [과거 설계](history/README.md) | 이전 구조와 기술 전환의 의사결정 |
| [현행 검증 도구](../backend/test/README.md) | 테스트 샘플과 대본·오디오 검증 실행법 |

연구·설계 기록에는 작성 당시의 경로와 설정이 포함되어 있습니다.
해당 기록의 실행 코드는 DEPRECATED 문서에 명시한 태그에서 확인할 수 있습니다.
현재 `backend/`는 Supabase 배치 파이프라인이며, 과거 자료의 동명 FastAPI 폴더와 구분합니다.
