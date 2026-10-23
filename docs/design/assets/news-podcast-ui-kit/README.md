# News & Podcast UI Kit 에셋 모음

[에셋 카탈로그 열기](index.html) · [원본 Figma](https://www.figma.com/design/D0l6pgIQRqw9YkdiHLkplv/News-Podcast-App-UI-Kit--File-?node-id=379-15944) · [CSV 목록](manifest.csv)

2026-10-23, Briefly 프로젝트에서 재사용할 수 있도록 원본 파일의 3개 콘텐츠 페이지를 정리했습니다. `index.html`은 서버나 인터넷 연결 없이 열 수 있습니다. Figma 링크만 인터넷 연결이 필요합니다.

## 포함 내용

- 아이콘 **6,239 SVG**: Linear, Bold, Bold Duotone, Broken, Line Duotone. 스타일/주제별 폴더, 원본 색상 유지.
- UI 컴포넌트 **283 PNG (@2x)**와 숨김 항목을 포함한 **290개 컴포넌트 / 42개 세트**의 변형·크기·키 정보.
- 로고 **24개**: Google·Facebook·Apple 벡터 3개 + 언론사·스포츠 등 원본 이미지 21개.
- 팟캐스트 커버 10개, 사진 20개, 아바타 3개, 이모지 12개, 일러스트 5개, 텍스처 1개.
- 라이트·다크 화면 **50 PNG (@1x)**.
- 로컬 변수 **267개**, 컬러 스타일 **6개**, 텍스트 스타일 **95개**, 효과 스타일 **15개**.

총 **6,647개 에셋 파일**입니다. 이미지 원본 70종은 Figma 이미지 해시와 SHA-1이 일치하는지 확인했습니다. 별도로 반환된 축소 이미지 22개는 원본과 내용이 겹쳐 제외했습니다.

## 사용 방법

`index.html`에서 이름·스타일·주제로 검색하고 에셋을 누르면 원본 파일, 다운로드, Figma 위치를 확인할 수 있습니다. 흰색 아이콘은 어두운 배경에서 확인하세요. 원본 아이콘은 24×24 viewBox를 사용하며, 임의로 색상을 변경하지 않았습니다.

Flutter 프로젝트에는 이미 `flutter_svg`가 있습니다. 사용할 SVG/PNG만 `flutter/assets/` 아래로 복사하고 `pubspec.yaml`의 `assets` 항목에 해당 경로를 등록하면 됩니다. SVG는 `SvgPicture.asset(...)`, PNG는 `Image.asset(...)`로 사용합니다. SVG 일부는 마스크·필터 등을 포함할 수 있으므로 실제 앱에서 렌더링을 확인하세요.

컴포넌트 PNG는 시각 자료입니다. 버튼 동작, Auto Layout, 반응형 배치가 포함된 Flutter 위젯은 아닙니다. `metadata/components.json`에 원본 컴포넌트 키와 변형 정보가 있으며, 편집 가능한 컴포넌트는 카탈로그의 Figma 링크에서 확인할 수 있습니다. 폰트 파일은 포함하지 않았습니다.

## 원본 추적과 제한

`manifest.json`/`manifest.csv`에 파일 경로, 크기, 분류, 원본 노드 ID와 Figma 링크를 기록했습니다. JSON에는 검증용 SHA-256, 이미지 원본 해시, 컴포넌트 변형 정보도 포함됩니다.

`Linear / Notes / Clipboard Heart` (`1440:55681`) 1개는 부모 프레임의 클리핑 영역 밖에 위치하여 Figma 내보내기가 실패합니다. 다른 아이콘으로 대체하지 않았고, 정확한 원본 벡터 속성을 `metadata/clipboard-heart-source.json`에 보존했습니다. 원본 아이콘 컴포넌트 6,240개 중 SVG는 6,239개입니다.

원본에서 숨김 처리된 컴포넌트 7개는 투명한 빈 PNG로 출력되어 이미지 목록에서 제외했습니다. 해당 컴포넌트의 레이어·벡터·텍스트·레이아웃 속성은 `metadata/hidden-components-source.json`에 보존했습니다. 전체 예외 8개의 기록은 `metadata/unexported.json`에 있습니다. 그림자 등 효과가 있는 PNG는 논리 크기보다 여백이 더 클 수 있으며, `manifest.json`의 `pixelWidth`/`pixelHeight`가 실제 픽셀 크기입니다.

원본 Figma 디자인은 변경하지 않았습니다. 이 모음은 원본 파일의 에셋을 정리한 것이며 별도 사용권을 부여하지 않습니다. UI 키트와 포함된 브랜드·사진의 기존 이용 조건을 따릅니다.
