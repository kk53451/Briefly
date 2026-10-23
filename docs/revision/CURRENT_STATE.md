# BRIEFLY 현행 코드 진단

검토일: 2026-10-23 (KST)

기준: `master`, HEAD `2e545b28`와 검토 당시의 로컬 변경. 원격 운영 DB나 전체 배치를 실행한 감사가 아니라 저장소의 코드·문서·보존 화면에 대한 정적 검토다. 기존 미커밋 변경을 포함해 읽었으며 수정하지 않았다.

리비전 방향과 제안은 [리비전 초안](README.md)을 따른다.

## 현재 구조와 활용할 자산

| 영역 | 확인한 상태 | 재설계에서 활용할 자산 |
|---|---|---|
| BI | 크림·잉크·적갈색, NotoSerifKR·Pretendard·JetBrainsMono, `Briefly.` 워드마크 | 한글 타이포그래피, 편집물 스타일, 화면 결정 기록 |
| 배치 | Python CLI → 네이버 수집 → KURE-v1 → UMAP/HDBSCAN → 헤드라인·대본·오디오 | 수집·중복 제거·토픽 평가 코드와 fixture |
| 생성 | Ollama 헤드라인, OpenAI 대본, NotebookLM 오디오 | 소스 태그 프롬프트, 숫자 검증, 대본 후처리, 전사·평가 도구 |
| 데이터 | Supabase Postgres·Storage·Auth, 앱에서 직접 조회 | 사용자 인증·관심사와 저장소 연결, 기존 데이터 |
| 앱 | Flutter·Riverpod·go_router·just_audio, Android/iOS 프로젝트 | 인증 흐름, 기사·헤드라인 화면, 오디오 제어, 글자 크기 설정 |
| 운영 | 로컬 결과 JSON, 선택적 Discord·Loki, 외부 스케줄러 필요 | 단계별 로그와 일부 계측 |

주요 근거: [README](../../README.md), [배치](../../backend/app/tasks/scheduler.py), [테마](../../flutter/lib/core/theme/app_theme.dart), [앱 의존성](../../flutter/pubspec.yaml).

## 재설계 전에 알아야 할 문제

아래의 영향은 코드 경로에서 도출했다. 실제 사용자 데이터에서 해당 문제가 발생한 횟수나 손실을 측정한 것은 아니다.

| 우선순위 | 코드에서 확인한 내용 | 영향과 작업 방향 |
|---|---|---|
| 높음 | `save_podcast()`는 예외를 잡고 `saved=False`를 반환하지만 호출자는 이를 검사하지 않고 성공 상태로 진행한다. `save_headlines()`의 bool도 호출부에서 검사하지 않는다. | 생성·저장·발행 성공을 분리하고 실패 결과를 상위 실행 상태와 종료 코드에 반영 |
| 높음 | `save_podcast()`는 오디오가 없거나 업로드가 실패하면 `audio_path=None`을 포함해 같은 날짜·슬롯에 upsert한다. | 성공한 회차를 오디오 생략/실패 상태로 재실행하면 기존 오디오 참조가 비워질 수 있음. 버전별 결과와 발행본 보존 필요 |
| 높음 | `news_cards`의 PK는 기사 ID이고, upsert에 회차 날짜·슬롯·순위가 포함된다. | 같은 기사가 다른 회차에 다시 선정되면 이전 배치의 행을 갱신함. 기사와 회차 내 배치를 분리 |
| 높음 | `byCategory()`는 슬롯 미지정 시 최신 슬롯을 고른다는 주석과 달리 슬롯 조건 없이 조회한다. `topByCategory()`도 날짜·rank로 조회한다. | AM/PM의 서로 다른 기사가 섞일 수 있음. 앱 전체가 같은 발행 회차를 선택하게 해야 함 |
| 높음 | 임베딩 캐시 키는 기사 수·max_chars·첫/마지막 기사 앞 100자를 사용한다. | 중간 기사 변경이나 모델 교체가 키에 반영되지 않음. 전체 유효 입력·모델/전처리 버전 기반 키 필요 |
| 중간 | `MY` 탭은 선택값 `my`를 일반 카테고리 조회로 넘기며 관심사 분기가 없다. | 사용자 관심사에 해당하는 뉴스 조회로 연결되지 않음 |
| 중간 | 홈의 정렬 UI는 고정 표시이며, “방금 업데이트됨”도 문자열 상수다. | 실제 정렬·신선도와 화면 안내가 어긋남. 발행 메타데이터에 연결 |
| 중간 | 다크 모드 스위치는 빈 콜백이며 `AppTheme.dark`는 light를 반환한다. 북마크·알림 설정에는 이동 동작이 없다. 상세의 저장·공유는 아이콘이다. | 활성 기능처럼 보이는 미완성 동작. 릴리스 범위를 정해 구현하거나 상태를 분명히 표현 |
| 중간 | 앱 셸은 탭바만 구성하고 공통 미니 플레이어가 없다. | 읽기 화면에서 재생 상태를 확인·제어하는 연결 경험이 부족 |
| 중간 | backend의 `covered_keywords`는 중첩 배열인데 Flutter 모델은 문자열만 남긴다. | 해당 형식의 토픽 키워드가 앱에서 버려짐. 명시적인 데이터 계약과 파싱 fixture 필요 |
| 제품 | 읽는 헤드라인은 6개 분야의 각 첫 토픽, 오디오는 정치·경제·국제의 별도 상위 토픽으로 구성된다. | 두 경험이 같은 회차의 같은 이슈를 다룬다는 보장이 없음. 회차의 공통 이슈·출처 묶음 필요 |

근거 파일:

- 저장 결과·오디오·카드 ID: [저장 서비스](../../backend/app/services/supabase_storage_service.py), [배치 호출부](../../backend/app/tasks/scheduler.py).
- 슬롯·MY 조회: [뉴스 repository](../../flutter/lib/features/home/data/news_cards_repository.dart), [홈](../../flutter/lib/features/home/home_screen.dart).
- 캐시: [임베딩 서비스](../../backend/app/services/embedding_service.py).
- 미완성 동작: [프로필](../../flutter/lib/features/profile/profile_screen.dart), [뉴스 상세](../../flutter/lib/features/news_detail/news_detail_screen.dart), [셸](../../flutter/lib/features/shell/shell_scaffold.dart), [테마](../../flutter/lib/core/theme/app_theme.dart).
- 키워드 계약: [Episode 모델](../../flutter/lib/shared/models/episode.dart), [저장 서비스](../../backend/app/services/supabase_storage_service.py).
- 읽기 이슈 선정: [헤드라인 repository](../../flutter/lib/features/today/data/headlines_repository.dart).

## 품질·운영의 기준

- 대본은 기사 소스 태그를 생성하고 숫자를 대조한 뒤 태그를 제거한다. 숫자가 원문 어딘가에 있다는 검사는 해당 주장과 올바른 출처의 대응까지 증명하지 않는다. 새 설계에서는 주장의 근거 연결을 결과에 보존하고 평가한다. [대본 생성](../../backend/app/services/script_service.py)
- 수집 시간 윈도우는 현재 꺼져 있다. 기존 AM/PM 표시만으로 뉴스가 특정 시간 범위를 다룬다고 가정하지 않는다. [배치 설정](../../backend/app/tasks/scheduler.py)
- 재시도가 전혀 없는 구조는 아니다. 예를 들어 헤드라인 호출에 재시도가 있다. 다만 전체 작업의 중단 후 재개, 발행 버전, 비용이 발생한 단계의 중복 실행 방지는 별도 설계가 필요하다. [헤드라인 서비스](../../backend/app/services/headline_service.py)
- `backend/test/`는 외부 서비스를 사용하는 수동 검증 CLI가 중심이며, 로컬 변경에는 대본 dry-run 실패 처리 회귀 테스트가 추가되어 있다. Flutter `test/`에서는 테스트 파일을 확인하지 못했고 저장소 루트의 `.github/`도 없다. 이것만으로 외부 CI가 없다고 단정하지는 않는다.
- 기존 [설치 검증 기록](../setup-validation.md)은 Flutter 분석·Android debug 실행 통과와 함께 Supabase 복구, Ollama 준비, OpenAI 크레딧, NotebookLM 인증 등의 후속 조건을 기록한다. 이번 검토에서 서비스의 현재 상태를 재조회하지 않았으므로 이를 최신 운영 상태로 확정하지 않는다.

## 디자인 문서와 실제 구현의 차이

[초기 디자인 명세](../design/DESIGN_SPEC.md)는 파란색 중심 팔레트, 카테고리별 오디오 등 이전 요구사항을 포함한다. 실제 Flutter는 크림·잉크·적갈색이며 오디오는 통합 브리핑 모델이다. [결정 노트](../design/prototype/notes/decisions.md)에 채택된 북마크·미니 플레이어 등이 모두 구현된 상태도 아니다.

검토한 보존 이미지 `04_after_guest.png`와 `06_today_loaded.png`는 빈 데이터 상태다. `current.png`는 Android 홈 화면이므로 현재 앱 화면의 근거로 사용하지 않는다. 이 자료만으로 데이터가 채워진 모든 화면의 시각 품질·접근성을 평가하지 않았다.

따라서 리비전 디자인 작업에는 실제 또는 명시적인 평가용 콘텐츠가 채워진 동일 샘플을 사용하고, 모바일·웹·다크·빈 상태·장문을 함께 검증해야 한다.

## 후속 구현의 필수 검증 사례

1. DB 쓰기 실패가 성공으로 처리되지 않고, 재시도 상한 이후 명확한 실패로 남는다.
2. 같은 회차의 오디오 생성·업로드 실패 또는 생략이 이미 발행된 오디오를 제거하지 않는다.
3. 동일 기사 재사용과 회차 재생성 후에도 이전 회차의 이슈·출처를 조회할 수 있다.
4. 두 작업이 같은 회차를 동시에 처리해도 한 발행본만 선택되고 이전 작업이 새 결과를 덮어쓰지 않는다.
5. 중간 기사·모델·프롬프트 변경 시 영향을 받는 단계의 캐시가 갱신된다.
6. 읽기 카드와 오디오 구간이 같은 회차 버전·이슈를 가리킨다.
7. 발행 전·오디오 실패·오래된 회차·네트워크 오류가 서로 구분되어 표시된다.
8. 웹 직접 접근·공유, Android/iOS 백그라운드 재생, 인증 복귀와 사용자 저장 데이터 격리가 동작한다.

이 검증은 리비전 구현의 완료 기준이며 이번 정적 검토에서 통과했다고 주장하는 테스트 결과가 아니다.
