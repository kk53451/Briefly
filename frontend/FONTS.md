# 📝 Briefly Mobile - Font Configuration

## 설치된 프리미엄 폰트

### ✅ 영문 폰트 (6개)

| 폰트 파일 | 용도 | 크기 |
|----------|------|------|
| **Outfit-Bold.ttf** | 헤드라인 (H1, H2, H3) | 75 KB |
| **Outfit-ExtraBold.ttf** | 강조 헤드라인 | 73 KB |
| **PlusJakartaSans-Regular.ttf** | 본문 텍스트 | 62 KB |
| **PlusJakartaSans-Medium.ttf** | 중간 굵기 텍스트 | 62 KB |
| **PlusJakartaSans-SemiBold.ttf** | 버튼, 강조 텍스트 | 62 KB |
| **JetBrainsMono-Regular.ttf** | 시간, 숫자, 메타데이터 | 264 KB |

**총 용량**: ~608 KB

### ✅ 한글 폰트 (3개)

| 폰트 파일 | 용도 | 크기 |
|----------|------|------|
| **Pretendard-Regular.ttf** | 한글 본문 | 2.6 MB |
| **Pretendard-Medium.ttf** | 한글 중간 굵기 | 2.6 MB |
| **Pretendard-Bold.ttf** | 한글 헤드라인 | 2.6 MB |

**총 용량**: ~7.8 MB

---

## 📦 전체 폰트 용량: 8.4 MB

---

## 사용 예시

### TypeScript/React Native

```tsx
import { Typography, FontFamilies } from './src/lib/theme';

// 영문 헤드라인
<Text style={Typography.h1}>Premium News</Text>

// 한글 헤드라인
<Text style={{ fontFamily: FontFamilies.koreanHeading, fontSize: 31 }}>
  브리플리 뉴스
</Text>

// 본문 텍스트 (자동으로 PlusJakartaSans 사용)
<Text style={Typography.body}>Body text content</Text>

// 시간 표시 (JetBrains Mono)
<Text style={Typography.time}>14:30</Text>
```

---

## 폰트 로드 과정

앱 시작 시 `App.tsx`에서 자동으로 모든 폰트를 로드합니다:

```typescript
const availableFonts = {
  'Outfit-Bold': require('./assets/fonts/Outfit-Bold.ttf'),
  'Outfit-ExtraBold': require('./assets/fonts/Outfit-ExtraBold.ttf'),
  'PlusJakartaSans-Regular': require('./assets/fonts/PlusJakartaSans-Regular.ttf'),
  'PlusJakartaSans-Medium': require('./assets/fonts/PlusJakartaSans-Medium.ttf'),
  'PlusJakartaSans-SemiBold': require('./assets/fonts/PlusJakartaSans-SemiBold.ttf'),
  'JetBrainsMono-Regular': require('./assets/fonts/JetBrainsMono-Regular.ttf'),
  'Pretendard-Regular': require('./assets/fonts/Pretendard-Regular.ttf'),
  'Pretendard-Medium': require('./assets/fonts/Pretendard-Medium.ttf'),
  'Pretendard-Bold': require('./assets/fonts/Pretendard-Bold.ttf'),
};

await Font.loadAsync(availableFonts);
```

---

## 라이선스

### Outfit
- **라이선스**: SIL Open Font License 1.1
- **출처**: https://github.com/Outfitio/Outfit-Fonts
- **사용 가능**: 상업적 사용 가능

### Plus Jakarta Sans
- **라이선스**: SIL Open Font License 1.1
- **출처**: https://github.com/tokotype/PlusJakartaSans
- **사용 가능**: 상업적 사용 가능

### JetBrains Mono
- **라이선스**: SIL Open Font License 1.1
- **출처**: https://github.com/JetBrains/JetBrainsMono
- **사용 가능**: 상업적 사용 가능

### Pretendard
- **라이선스**: SIL Open Font License 1.1
- **출처**: https://github.com/orioncactus/pretendard
- **사용 가능**: 상업적 사용 가능

---

## 문제 해결

### 폰트가 로드되지 않을 때

1. **캐시 클리어**:
   ```bash
   npx expo start -c
   ```

2. **폰트 파일 확인**:
   ```bash
   ls -lh assets/fonts/
   ```

3. **에러 로그 확인**:
   - Metro bundler에서 폰트 관련 에러 메시지 확인
   - `console.error('Error loading fonts:', error)` 출력 확인

### 폰트가 제대로 표시되지 않을 때

- **Android**: 앱 재시작 필요
- **iOS**: 시뮬레이터 재시작 필요
- **모두**: `npm run ios` 또는 `npm run android` 다시 실행

---

## 디자인 시스템 적용

이 폰트들은 **Premium Audio Journal meets Modern News Reader** 컨셉을 실현하기 위해 선정되었습니다:

- **Outfit**: 모던하고 깔끔한 헤드라인
- **Plus Jakarta Sans**: 가독성 높은 본문
- **JetBrains Mono**: 정확한 시간/숫자 표시
- **Pretendard**: 한글 최적화 프리미엄 폰트

---

## 성능 최적화

### 폰트 로딩 전략

1. **앱 시작 시 일괄 로드**: 모든 폰트를 한 번에 로드하여 이후 즉시 사용 가능
2. **에러 처리**: 폰트 로드 실패 시 시스템 폰트로 폴백
3. **로딩 화면**: 폰트 로드 중 ActivityIndicator 표시

### 용량 고려사항

- **초기 다운로드**: 약 8.4 MB (압축 시 더 작아짐)
- **메모리 사용**: 필요할 때만 로드
- **최적화**: 사용하지 않는 weight는 제외 가능

---

## 추가 폰트 설치 방법

1. **폰트 파일 다운로드** (.ttf 형식)
2. **assets/fonts/** 폴더에 복사
3. **App.tsx** 수정:
   ```typescript
   'YourFont-Regular': require('./assets/fonts/YourFont-Regular.ttf'),
   ```
4. **typography.ts** 수정:
   ```typescript
   customFont: 'YourFont-Regular',
   ```

---

**Last Updated**: 2024-11-21
**Version**: 1.0.0