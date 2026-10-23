# Briefly / Softpress

2026-10-23 사용자 선택: Round 04의 **02 Softpress**. [브랜드 시트](../brand.html).

## 표기와 형태

- 이름은 **Briefly**: 대문자 B + 소문자 riefly. 화면의 워드마크는 축약하지 않는다. 앱 아이콘도 전체 이름을 한 줄로 유지한다.
- 가로 워드마크는 선택한 Fraunces 기반 경로, 글자 간격, fl 연결을 그대로 사용한다. 비교 화면의 외부 캔버스 여백만 정리했다.
- 앱 아이콘은 **1번 Briefly 한 줄 확정**. [확정 아이콘](../app-icons.html). 글자의 실제 채움 면적 중심을 세로 50/100에 배치해 y 꼬리에 따른 시각적 치우침을 보정했다.
- 블루 #244BEB, 흰색 #FFFFFF, 검정 #000000. 워드마크를 늘리거나 회전하거나 별도 심벌을 덧붙이지 않는다.
- 워드마크 주변에 전체 높이의 ¼ 이상 여백을 둔다. UI 헤더 권장 너비는 122–132px, 최소 권장 너비는 110px이다.
- 앱 아이콘은 48px 이상에서 전체 철자 판독을 확인한다. 16px 파비콘에서는 일곱 글자 판독을 보장하지 않는다.

## 자산

| 파일 | 용도 |
|---|---|
| `logo.svg`, `logo-black.svg`, `logo-white.svg` | 블루·검정·반전 워드마크 |
| `logo-current.svg` | 인라인 SVG에서 currentColor로 제어 |
| `logo*-1600.png` | 투명 배경 1600px 워드마크 |
| `app-icon.svg`, `app-icon-black.svg` | 둥근 모서리 미리보기용 앱 아이콘 |
| `app-icon-{48,64,128,180,192,512,1024}.png` | 크기별 미리보기 |
| `app-icon-square.svg`, `app-icon-square-{180,192,512,1024}.png` | 플랫폼 마스크 적용 전, 불투명 사각 원본 |
| `stacked-mark.svg` | 이전 두 줄 탐색 이력. 현재 사용하지 않음 |
| `symbol.svg` | 기존 경로 호환용. 새 전체 이름 앱 아이콘과 동일 |
| `licenses/Fraunces-OFL.txt` | 원본 폰트 라이선스 |

모든 SVG 글자는 윤곽선이며 폰트 설치가 필요 없다. Fraunces 원본을 새 독점 서체로 주장하지 않는다. UI 글꼴은 기존 Pretendard를 유지한다.

## 재생성

`python ../build_logo.py` → `node ../render_brand.cjs`. Python은 fontTools, Node는 sharp가 필요하다. 번들 sharp 경로는 `BRIEFLY_SHARP_PATH`로 지정할 수 있다. 사용자가 고른 원본은 `../logo-exploration/round-04/assets/02-softpress-*.svg`에 보존한다.

현재 적용 범위는 로컬 브랜드 가이드·반응형 HTML 프로토타입이다. Flutter 배포 아이콘과 실제 스토어 자산 반영은 제품 구현 단계에서 수행한다.

## 앱 아이콘 추가 비교

2026-10-23 사용자 제안에 따라 `app-icon-full-name*.svg/png`, `app-icon-b-dot*.svg/png`를 추가했다. 전체 이름은 승인된 워드마크를 그대로 사용하고, B와 마침표도 같은 Fraunces 축 설정에서 추출했다. 각 후보는 32/48/64/128/256/1024px와 사각 1024px 원본을 제공한다. `build_app_icon_options.py`와 `render_app_icon_options.cjs`로 재생성한다.

최종 선택: **full-name**. `app-icon.svg`, `app-icon-square.svg`, `symbol.svg`와 모든 기본 PNG를 한 줄·세로 중앙 정렬 버전으로 교체했다. `build_logo.py`가 기본 아이콘의 원본이며 후보 생성기는 이 결과를 복사하므로 재생성해도 정렬이 유지된다.
