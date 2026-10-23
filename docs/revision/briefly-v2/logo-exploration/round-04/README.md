# Briefly — 타이포 로고 Round 04

2026-10-23. 사용자 요청: 다시 탐색하되 타이포를 활용하고, 로고를 단독 `b`가 아닌 **Briefly 전체 이름**으로 표현한다.

- [인터랙티브 비교](index.html)
- [6안 비교 보드](comparison.png)
- [브라우저 검수 화면](web-preview.png)
- 로컬 URL: http://127.0.0.1:8770/logo-exploration/round-04/index.html

## 표기와 방향

공식 로고 표기는 대문자 **B**와 소문자 **riefly**를 합친 `Briefly`다. 이번 워드마크·앱 아이콘 12개 모두 이름의 일곱 글자를 포함한다. 단독 b/B 모노그램은 만들지 않았다. 앱 아이콘은 `Bri` / `efly` 두 줄이다. 이전 세리프 선호는 01에 이어가고, 나머지는 다른 타이포 방향을 제시한다. 새 시안의 최종 선택은 아직 하지 않았다.

| 번호 | 방향 | 제작 방식 |
|---|---|---|
| 01 Editorial | 편집 제호 | DM Serif Display, fl 리거처, 광학 자간 |
| 02 Softpress | 둥글고 묵직한 활자 | Fraunces 850, SOFT 100, WONK 1, opsz 144, fl 리거처 |
| 03 Flow | 읽기에서 듣기로 흐르는 이름 | Instrument Serif Italic, fl 리거처, 별도 곡선 |
| 04 Edit | 핵심만 남긴 활자 | Space Grotesk 700, i 점을 마름모로 재구성 |
| 05 Headline | 압축된 제목 | Archivo Black, 가로 비례 82%, 조정한 자간 |
| 06 Typeset | 이름 전체를 담은 표식 | Pretendard 900, Bri / efly 두 줄 블록 |

사용된 활자 골격은 아래 공개 폰트를 바탕으로 한다. 완전히 새로 그린 전용 서체라고 주장하지 않는다. 리거처 선택, 광학 자간, 비례, 점과 곡선, 두 줄 구성을 통해 로고 방향을 비교한다.

## 스킬과 출력

설치된 `logo-generator`의 6방향 탐색 → SVG → 비교 화면 → 피드백 절차를 적용했다. 이번 요청은 타이포 중심이므로 심벌 패턴 대신 글자 구조와 조판을 비교한다. 워드마크 viewBox는 비례를 보존하는 500×160, 앱 아이콘은 스킬 기준의 100×100이다.

FontTools로 모든 글자를 경로로 변환했다. 최종 SVG에는 텍스트 노드, 외부 폰트, 래스터 이미지가 없다. PNG는 같은 SVG를 sharp로 렌더링한 파일이다. 이번 작업에 이미지 생성 API는 사용하지 않았다.

- 워드마크 SVG 6개, 앱 아이콘 SVG 6개.
- 투명 배경 워드마크 PNG 6개: 1200×384px.
- 앱 아이콘 PNG 24개: 각 48/64/128/1024px.
- `comparison.svg` / `comparison.png`: 1560×1080px 전체 보드.
- `build.py`: 글자 조판, 벡터 경로, 보드, HTML 생성 소스.
- `template.html`, `style.css`, `script.js`: 워드마크/앱 전환, 흑백/블루, 확대 및 다운로드.
- `render.cjs`: SVG에서 PNG로 내보내기.

앱 아이콘 다운로드는 블루·사각 기준이다. 전체 단어는 16px 파비콘에서 읽기 어려우므로 이번에는 48px 이상 앱 아이콘 맥락으로 비교한다. 03의 얇은 획은 01·02·05·06보다 작은 크기에서 약하다. 최종 선택 후 크기별 보정을 진행한다.

## 폰트 출처

Google Fonts 공식 저장소에서 폰트와 각 SIL Open Font License를 함께 저장했다. 원본 폰트는 수정하지 않았으며 `fonts/<family>/OFL.txt`를 보존했다.

- [DM Serif Display](https://github.com/google/fonts/tree/main/ofl/dmserifdisplay)
- [Fraunces](https://github.com/google/fonts/tree/main/ofl/fraunces)
- [Instrument Serif](https://github.com/google/fonts/tree/main/ofl/instrumentserif)
- [Space Grotesk](https://github.com/google/fonts/tree/main/ofl/spacegrotesk)
- [Archivo Black](https://github.com/google/fonts/tree/main/ofl/archivoblack)
- Pretendard는 기존 프로젝트의 `flutter/assets/fonts/PretendardVariable.ttf` 사용.

## 재생성

`python build.py` 후 `node render.cjs` 실행. Python은 FontTools가 필요하고, Node는 sharp 또는 `BRIEFLY_SHARP_PATH` 환경변수에 지정된 sharp 패키지를 사용한다.

서버는 기존 `../../serve.py --port 8770`을 사용한다.

## 검증

- 데스크톱 1440px, 모바일 390px·320px에서 카드·탐색·상세창 가로 넘침 없음.
- 워드마크/앱 아이콘, 블루/흑백 전환과 상세창 열기·Escape 닫기 확인.
- SVG 12개에 전체 이름 접근성 레이블이 있으며, 글자는 경로로 저장되어 외부 폰트 의존성 없음.
- PNG 30개 출력 크기와 주요 정적 파일 HTTP 200, JavaScript 구문 검사 통과.
- 브라우저 경고·오류 없음. 실제 비교 화면은 `web-preview.png`에 저장.
