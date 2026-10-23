# BRIEFLY 로고 재탐색

## 선택 상태

2026-10-23 최신 요청: 로고는 **Briefly 전체 이름**으로 표현한다. 대문자 B + 소문자 riefly가 표기 기준이며, 단독 b/B 모노그램 대신 전체 이름의 타이포 로고를 사용한다. 이전 **B · Editorial + Fold**는 선호 이력으로 보존한다. **Round 04 / 02 Softpress를 사용자가 선택했다.** [확정 로고와 적용](../brand.html), [사용 규칙·파일](../assets/README.md).

앱 아이콘은 **1번 Briefly 한 줄**로 확정했다. 글자를 세로 중앙에 시각적으로 정렬했다. [확정 아이콘과 다운로드](../app-icons.html). 워드마크는 02 Softpress를 유지한다.

## 최신 — Briefly 타이포 / Round 04

- [타이포 6안 비교 화면](round-04/index.html)
- [전체 비교 보드](round-04/comparison.png)
- [폰트 출처·제작 방식·원본](round-04/README.md)

워드마크와 앱 아이콘 모두 이름 전체를 담았다. 앱 아이콘은 Bri / efly 두 줄 구성이다. 01 Editorial은 기존 세리프 취향을 이어가고, 02 Softpress는 둥글고 개성 있는 활자, 06 Typeset은 이름 전체가 정사각형 표식이 되는 방향이다.

## 이전 — logo-generator 실제 적용 / Round 03

사용자의 설치 요청에 따라 `logo-generator`를 설치하고 실제 SVG 시안 6개와 비교 화면을 제작했다. B 워드마크는 선택한 원본의 해당 영역을 그대로 표시한다.

- [인터랙티브 비교 화면](round-03/index.html)
- [6안 비교 보드](round-03/comparison.png)
- [제작 방식·원본·검수 기록](round-03/README.md)

현재 추천 비교 대상은 05 · Interleaf와 06 · Swift. 기존 Fold에 가까운 발전안은 01 · Unfold다.

## 추가 탐색 — Round 02

[새로운 심벌 6안](creative-symbols-round-02.png)

| 안 | 발상 |
|---|---|
| 01 · Paperbird | 종이를 접은 형태와 소식을 전하는 새 |
| 02 · First Light | 페이지를 넘기는 곡선과 아침빛 |
| 03 · Page / Voice | 페이지의 두 면과 목소리의 확산 |
| 04 · Lens | 두 페이지 사이에 드러나는 통찰의 여백 |
| 05 · Margin | 접힌 모서리와 발췌한 조각 |
| 06 · Unfold | 펼쳐지는 종이와 하루의 맥락 |

발상 참고: 공개 `logo-generator`의 서로 다른 6개 구조 비교, 단순한 형태, 의도적인 비대칭, 여백 지침. 생성은 기존 내장 image_gen을 사용했다. 새 스킬을 전역 설치하거나 해당 저장소의 스크립트를 실행하지 않았다. [생성 프롬프트](CREATIVE-SYMBOLS-PROMPT.txt).

이 보드는 래스터 발상 시안이며 SVG 제작·실제 소형 렌더링 검증을 완료한 자산이 아니다. 01은 전달이라는 의미가 강하고, 04는 더 추상적인 편집 브랜드 방향이다. 05는 문서 아이콘에 가까워 차별화가 약하다. 기준안 Fold와 비교한 후 최종 형태를 정한다.

### 검토한 스킬

2026-10-23 공개 스킬 페이지와 GitHub 원문을 확인했다. 설치 수는 해당 시점 페이지 표시값이며, 품질이나 창의성을 보증하지 않는다.

| 스킬 | 표시 설치 수 | 적합성 |
|---|---:|---|
| [logo-generator · op7418](https://www.skills.sh/op7418/logo-generator-skill/logo-generator) | 약 3.8K | 현재 추천. 서로 다른 6개 이상의 SVG 구조 탐색과 비교. 고급 이미지 목업 단계에는 별도 Gemini API가 필요하지만 벡터 탐색과 구분된다. |
| [ip-as-logo · s1dashu](https://www.skills.sh/s1dashu/ip-as-logo-skill/ip-as-logo) | 약 3.4K | 간결한 캐릭터형 로고에 특화. 현재 추상 페이지 방향과는 다른 선택지. |
| [SVG Logo Designer · rknall](https://www.skills.sh/rknall/claude-skills/svg-logo-designer) | 페이지 1.2K / CLI 8K | SVG 변형과 레이아웃 제작 중심. 조회 경로별 설치 수가 달라 인기 순위 판단에서 제외. |

- [logo-generator 원문](https://github.com/op7418/logo-generator-skill/blob/main/SKILL.md)
- [디자인 패턴 지침](https://github.com/op7418/logo-generator-skill/blob/main/references/design_patterns.md)
- GitHub API 조회 별 수: op7418 저장소 2,263; s1dashu 저장소 6,104; rknall 저장소 85.

## 앱 심벌 첫 3안

[B 워드마크 + 앱 심벌 3안](b-symbol-options.png)

| 안 | 모티프 | 의도 |
|---|---|---|
| 01 · Fold | 접힌 페이지 | 읽기와 편집을 연결하는 두 면의 형태 |
| 02 · Essence | 발췌한 핵심 | 원과 분리된 조각으로 압축과 선별을 표현 |
| 03 · Continuum | 이어지는 리본 | 읽기와 듣기가 이어지는 흐름 |

추천 방향은 01 · Fold. 페이지라는 의미가 명확하고 B 워드마크의 곡선과 잘 어울린다. 소형·단색 표현은 비교 보드에 포함했으며, 실제 24/32px 렌더링 검증은 심벌 선택 후 SVG 제작 시 진행한다. 보드의 `32px` 표시는 비교 레이블이며 이미지 안에서 실제 픽셀 크기를 보증하지 않는다.

생성 방식: 내장 image_gen, 기존 `logo-options.png`의 B를 참조한 새 보드 생성. [프롬프트](B-SYMBOL-PROMPT.txt). 래스터 시안이므로 최종 워드마크·심벌의 곡선과 간격은 벡터 원본 제작 시 확정한다. 현재 제품 화면과 기존 SVG는 아직 교체하지 않았다.

## 이전 6안

2026-10-23. 기존 따옴표 로고에 대한 피드백을 반영한 6개 이미지 시안. 기존 BI와 제품 화면의 로고를 교체하지 않은 방향 비교 단계다.

[최종 비교 보드](logo-options.png)

| 안 | 방향 | 비교할 특징 |
|---|---|---|
| A · Open B | 펼쳐진 페이지와 b | 읽기 서비스와 연결되는 형태, 앱 아이콘 확장 |
| B · Editorial | 세리프 워드마크 | 편집 브랜드 인상, 글자 자체의 개성 |
| C · Compact | 압축된 대문자 | 강한 존재감, 뉴스·미디어 인상 |
| D · Focus | 핵심을 감싸는 프레임 | 선별과 집중을 표현하는 추상 심벌 |
| E · Wordmark | 연결된 글자 형태 | 친근하고 독특한 워드마크, 작은 크기의 식별성 추가 검토 |
| F · Ribbon | b/f 리본 모노그램 | 읽기와 듣기의 연결을 표현, 작은 크기의 겹침 추가 검토 |

내장 image_gen으로 생성·수정했다. 그림의 로고는 방향 검토용 래스터 시안이며 최종 SVG 원본이 아니다. 선택한 안의 글자 간격, 획, 단색·반전·소형 표현은 벡터 제작 단계에서 정교화한다.

- [최초 생성 프롬프트](PROMPT.txt)
- [D/F 형태 수정 프롬프트](REFINEMENT.txt)
- 최종 저장 파일: `logo-options.png`
