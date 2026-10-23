# Briefly BI & Design System v0.3

확정한 **02 Softpress 워드마크 + 한 줄·세로 중앙 정렬 앱 아이콘**을 기준으로 BI, 디자인 토큰, 컴포넌트 상태, 모바일 첫 화면을 정리했다.

## 결과 보기

```powershell
python docs/revision/briefly-v2/serve.py --port 8770
```

- [BI·디자인 시스템](http://127.0.0.1:8770/)
- [모바일 화면과 웹 전환](http://127.0.0.1:8770/index.html#screens)
- [반응형 제품 프로토타입](http://127.0.0.1:8770/app.html)
- [확정 로고](http://127.0.0.1:8770/brand.html), [앱 아이콘](http://127.0.0.1:8770/app-icons.html)
- [모바일 캡처](previews/v03-mobile.png), [읽기 화면](previews/v03-reading.png), [웹 캡처](previews/v03-web.png), [시스템 가이드](previews/v03-system.png)
- [브랜드·설계 기준](DESIGN.md), [로고 자산과 사용 규칙](assets/README.md)

## 이번에 정리한 경험

- 반복 로고와 안내 문구를 줄이고, 회차 → 읽기·듣기 → 이야기 목록으로 위계를 구성했다.
- 코발트 회차의 3개 구간은 실제 재생 순서와 연결된다. 전체 듣기·일시정지·이어 듣기가 플레이어와 같은 상태를 표시한다.
- 읽던 이야기를 기억하고 ‘이어서 읽기’로 연결한다. ‘읽고 다음으로’·‘다 읽었어요’로 완료한 이야기만 누적한다. 3개 모두 읽었을 때만 회차 완독이다.
- 저장·출처 왕복·현재 듣는 구간 읽기·지난 회차를 사용할 수 있다. 빈 보관함, 오디오 준비 중, 불러오기 실패와 키보드 포커스를 가이드에 정리했다.
- UI는 Pretendard, 로고는 변경 없는 Fraunces 기반 윤곽선을 사용한다. 6개 기본 색상과 간격·곡률·타입·터치 영역은 토큰으로 관리한다.

날짜는 2026-10-23의 가상 회차다. 재생은 타이머로 동작하며 실제 음원은 없다. 저장과 읽기 진행은 이 브라우저에만 보존한다. Flutter·인증·백엔드·배포를 교체한 결과가 아니다.

## 원본과 재생성

| 파일 | 역할 |
|---|---|
| `DESIGN.md` | 확정 BI, 시각 방향, 모바일 위계, 상태 규칙 |
| `tokens.json`, `build_tokens.py` | 원본 토큰과 CSS 생성 |
| `base.css` | 공통 폰트·버튼·아이콘·포커스 |
| `app.template.html`, `app.css`, `app.js` | 모바일 우선 화면, 읽기·재생·저장 상태 |
| `system.template.html`, `system.css`, `system.js` | BI 가이드, 컴포넌트 예시, 기기 미리보기 |
| `build_pages.py` | 공통 아이콘·이야기·토큰을 HTML로 생성; CSS/JS 내용 해시로 캐시 갱신 |
| `build_logo.py`, `render_brand.cjs` | 승인된 벡터와 크기별 PNG 발행 |
| `assets/` | 확정 로고, 앱 아이콘, 라이선스 |

```powershell
python docs/revision/briefly-v2/build_tokens.py
python docs/revision/briefly-v2/build_pages.py
```

로고를 재발행할 때만 `build_logo.py`와 `render_brand.cjs`를 사용한다. 로고 경로와 광학 중앙 정렬은 이번 디자인 정리에서 변경하지 않았다.

가이드의 ‘검토용 읽기 진행 초기화’로 읽기 상태를 초기화할 수 있다. 저장한 이야기는 지우지 않는다.

## 검수

브라우저에서 320px·390px 모바일과 1440px 웹 레이아웃을 검토한다. 읽기·완료·새로고침 후 이어 읽기, 출처 왕복, 저장·해제·보관함, 구간 듣기·일시정지·읽기 전환, 시스템 가이드의 모바일·웹 전환을 확인한다. 세부 결과는 `QA.md`에 기록한다.

실제 뉴스 품질, 실제 음원과 백그라운드 재생, 스크린리더·기기 검수는 제품 구현 단계에서 별도로 수행한다.
