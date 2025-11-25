# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Briefly** is an AI-powered news podcast platform that automatically collects, summarizes, and converts daily news into personalized audio podcasts. The system runs fully automated with a serverless architecture on AWS.

**Core Technology Stack:**
- **Mobile App**: React Native Expo SDK 54 (TypeScript, React Navigation v7)
- **Backend**: FastAPI, Python 3.12, AWS Lambda (SAM)
- **AI Services**: OpenAI GPT-4o-mini, ElevenLabs TTS
- **Data**: DynamoDB (4 tables), S3 (audio storage)
- **Scheduler**: AWS EventBridge (daily 6 AM KST)

## Development Commands

### Mobile App (React Native Expo SDK 54)
```bash
cd mobile

# Install dependencies
npm install

# Start development server
npx expo start

# Run on specific platforms (requires native build)
npx expo run:ios      # iOS (requires Mac + Xcode)
npx expo run:android  # Android (requires Android Studio)
npm run web           # Web browser

# Clear cache and restart
npx expo start -c

# Build for production (EAS Build)
eas build --platform ios
eas build --platform android
```

**Note:** This project uses native Kakao SDK (`@react-native-kakao`), so Expo Go is not supported. You must use development builds (`expo run:android` / `expo run:ios`).

### Backend (FastAPI)
```bash
cd backend

# Local development
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000    # Start local server
# API docs: http://localhost:8000/docs

# Testing
cd test
python run_all_tests.py                      # Run all tests
$env:PYTHONIOENCODING='utf-8'; python test_frequency_unit.py  # Single test (Windows)

# AWS SAM deployment
sam build                # Build Lambda functions
sam deploy --guided     # First deployment (interactive)
sam deploy              # Subsequent deployments
sam logs -n BrieflyApi --stack-name briefly-backend  # View CloudWatch logs
```

## Architecture & Key Concepts

### Automated Daily Pipeline (6 AM KST)
The system runs automatically via EventBridge → Lambda (`DailyBrieflyTask`):

1. **News Collection** (`app/tasks/collect_news.py`)
   - BigKinds API: 60 articles requested → 30 selected per category
   - Total: 8 categories × 30 articles = 240 articles/day
   - Parallel processing using `ThreadPoolExecutor` (max_workers=5)
   - Content scraping: 300+ chars, 70%+ Korean text validation
   - Deduplication: ID, URL, title (memory + DB check)

2. **Dual Clustering Strategy** (`app/services/openai_service.py`)
   - **1st clustering**: Physical deduplication of original articles (80% threshold)
   - **2nd clustering**: Semantic deduplication of GPT summaries (75% threshold)
   - Reduces 240 articles → 5-10 core groups per category
   - Saves 50% on token costs

3. **Podcast Script Generation** (`app/services/openai_service.py`)
   - Few-shot learning with category-specific examples
   - Progressive temperature adjustment (0.3 → 0.5 → 0.7) for quality
   - Category-specific tone and style (politics: balanced, economy: approachable, etc.)
   - Target length: 1,800-2,200 characters (4-5 min audio)

4. **TTS Conversion** (`app/services/tts_service.py`)
   - ElevenLabs `eleven_multilingual_v2` model
   - Voice settings: stability=0.5, similarity_boost=0.8
   - Auto-upload to S3 with presigned URLs (7-day expiry)

### Database Structure (DynamoDB)

**NewsCards Table**
- PK: `news_id`
- GSI: `category_date` (for querying by category+date)
- Stores: title, content, images (string URL), provider, byline, published_at, hilight, rank, etc.

**Frequencies Table**
- PK: `frequency_id` (format: `{category}#{date}`)
- Stores: script, audio_url, category, date, created_at
- Shared by all users (one podcast per category per day)

**Users Table**
- PK: `user_id` (format: `kakao_{kakao_id}`)
- Stores: nickname, profile_image, interests[], onboarding_completed, created_at

**Bookmarks Table**
- Composite PK: `user_id` (HASH) + `news_id` (RANGE)
- Stores: bookmark_date

### Mobile App Architecture (React Native Expo SDK 54)

**Navigation Structure** (`mobile/src/navigation/`)
```
RootNavigator (Stack)
├── Onboarding - 카테고리 선택 (onboarding 미완료 시)
└── Main (Bottom Tabs) - 메인 앱
    ├── Home - 언론사별 최신 뉴스
    ├── Today - 카테고리별 뉴스
    ├── Podcast - 팟캐스트 플레이어
    └── Profile - 프로필 및 설정
    + Login (Stack) - 로그인 화면 (필요시)
```

**Screen-to-API Mapping**

| Screen | Component | Backend API | Description |
|--------|-----------|-------------|-------------|
| Home | `HomeScreen` | `GET /api/news/home` | 언론사별로 그룹핑된 최신 뉴스 |
| Today | `TodayScreen` | `GET /api/news/today` | 카테고리별로 그룹핑된 뉴스 |
| Podcast | `PodcastScreen` | `GET /api/frequencies` | 오늘의 팟캐스트 목록 |
| Profile | `ProfileScreen` | `GET /api/user/profile` | 사용자 프로필 및 북마크 정보 |
| Onboarding | `OnboardingScreen` | `POST /api/user/onboarding` | 초기 카테고리 설정 |
| Login | `LoginScreen` | `POST /api/auth/kakao/token` | 카카오 네이티브 로그인 |

**Technology Stack**
- **State Management**: React Context (AuthContext, ThemeContext, AudioPlayerContext)
- **Storage**: expo-secure-store (JWT), AsyncStorage (cache)
- **Navigation**: React Navigation v7 (Stack + Bottom Tabs)
- **UI Framework**: Custom StyleSheet (no external UI library)
- **Styling**: Custom theme system (`src/constants/theme.ts`)
- **Audio**: expo-av with AudioPlayerContext
- **Auth**: `@react-native-kakao/user` (Native Kakao SDK)

**API Client** (`mobile/src/services/api.ts`)
- Axios-based HTTP client
- JWT token management via expo-secure-store
- Auto token injection via request interceptor
- Automatic logout on 401 responses

### Authentication Flow (Mobile - Native Kakao SDK)

1. User taps "카카오로 시작하기" button
2. App calls `@react-native-kakao/user` native SDK
3. Kakao native login UI appears (or browser if app not installed)
4. User authorizes → Kakao SDK returns access token
5. App sends Kakao access token to backend: `POST /api/auth/kakao/token`
6. Backend validates with Kakao, creates/gets user, returns JWT
7. Store JWT in expo-secure-store
8. Navigate to OnboardingScreen (if first login) or MainNavigator

**Native Kakao SDK Configuration (`app.json`):**
```json
{
  "plugins": [
    ["@react-native-kakao/core", {
      "nativeAppKey": "YOUR_KAKAO_NATIVE_APP_KEY",
      "android": { "redirectUri": "kakao{APP_KEY}://oauth" },
      "ios": { "redirectUri": "kakao{APP_KEY}://oauth" }
    }]
  ]
}
```

**Token Usage:**
- All protected endpoints require `Authorization: Bearer {token}` header
- Token validation via `get_current_user()` dependency in FastAPI
- Token contains: `{"sub": "kakao_{id}", "exp": timestamp}`
- Auto-check on app launch via `AuthContext.checkAuth()`

## Important Implementation Details

### Token Optimization
To minimize OpenAI costs, the codebase implements strict token limits:
- Article content: 1,500 char limit when collecting
- Clustering embeddings: 1,000 char limit
- Group summaries: 800 char per article
- Final script: 2,000 max_tokens

**When modifying GPT calls**, maintain these limits to avoid cost overruns.

### Category Mapping
Categories have both Korean and English names:
```python
# app/constants/category_map.py
CATEGORY_MAP = {
    "정치": {"api_name": "politics", "bigkinds_name": "정치"},
    "경제": {"api_name": "economy", "bigkinds_name": "경제"},
    "사회": {"api_name": "society", "bigkinds_name": "사회"},
    "문화": {"api_name": "culture", "bigkinds_name": "문화"},
    "국제": {"api_name": "international", "bigkinds_name": "국제"},
    "지역": {"api_name": "local", "bigkinds_name": "지역"},
    "스포츠": {"api_name": "sports", "bigkinds_name": "스포츠"},
    "IT/과학": {"api_name": "tech", "bigkinds_name": "IT_과학"}
}
```
Always use Korean names in frontend UI, English names for API/database.

### Timezone Handling
All dates must use KST (Korea Standard Time):
```python
# app/utils/date.py
def get_today_kst() -> str:
    kst = pytz.timezone("Asia/Seoul")
    return datetime.now(kst).strftime("%Y-%m-%d")
```
DynamoDB stores dates as strings in `YYYY-MM-DD` format.

### Error Handling Philosophy
The codebase uses extensive error handling with fallbacks:
- API failures: Return original text instead of failing
- Clustering failures: Skip clustering, use all articles
- TTS failures: Save script without audio URL
- **Never throw unhandled exceptions** in Lambda functions (they're expensive)

### Memory Constraints
Lambda functions have 1024MB memory for clustering operations:
- Batch processing is used to avoid OOM
- Embeddings are generated one-by-one, not in bulk
- If adding new features, monitor CloudWatch memory metrics

## Project File Structure

```
Briefly/
├── backend/                    # FastAPI Lambda backend
│   ├── app/
│   │   ├── main.py            # FastAPI app entry point
│   │   ├── routes/            # API endpoints
│   │   ├── services/          # Business logic (OpenAI, TTS, BigKinds)
│   │   ├── tasks/             # Scheduled tasks (news collection)
│   │   ├── utils/             # Utilities (DynamoDB, date, etc.)
│   │   └── constants/         # Category mapping, prompts
│   ├── template.yaml.example  # SAM template
│   ├── requirements.txt       # Python dependencies
│   └── test/                  # Unit tests
│
└── mobile/                    # React Native Expo SDK 54 app
    ├── index.ts              # App entry point
    ├── app.json              # Expo configuration
    ├── package.json          # Dependencies
    ├── android/              # Native Android project
    ├── src/
    │   ├── navigation/       # Navigation structure
    │   │   ├── RootNavigator.tsx    # Auth flow handling
    │   │   └── MainNavigator.tsx    # Bottom tab navigation
    │   ├── screens/          # Screen components
    │   │   ├── LoginScreen.tsx
    │   │   ├── OnboardingScreen.tsx
    │   │   ├── HomeScreen.tsx
    │   │   ├── TodayScreen.tsx
    │   │   ├── PodcastScreen.tsx
    │   │   └── ProfileScreen.tsx
    │   ├── components/       # Reusable components
    │   │   ├── ErrorView.tsx
    │   │   └── NewsImage.tsx
    │   ├── contexts/         # React Context providers
    │   │   ├── AuthContext.tsx
    │   │   ├── ThemeContext.tsx
    │   │   └── AudioPlayerContext.tsx
    │   ├── services/
    │   │   └── api.ts        # API client (Axios)
    │   ├── constants/        # Theme & categories
    │   │   ├── theme.ts
    │   │   ├── categories.ts
    │   │   └── commonStyles.ts
    │   ├── types/            # TypeScript type definitions
    │   │   ├── api.ts
    │   │   └── navigation.ts
    │   └── utils/
    │       └── logger.ts
    └── assets/               # Static assets (icons, splash)
```

## Environment Variables

**Mobile App** (`.env` or `process.env`):
```bash
# Backend API URL
EXPO_PUBLIC_API_URL=http://localhost:8000  # Local development
# EXPO_PUBLIC_API_URL=https://xxxxx.execute-api.ap-northeast-2.amazonaws.com  # Production

# For Android emulator, use: http://10.0.2.2:8000
```

**Kakao SDK Configuration** (`app.json`):
```json
{
  "plugins": [
    ["@react-native-kakao/core", {
      "nativeAppKey": "your_kakao_native_app_key"
    }]
  ]
}
```

**Backend** (`backend/template.yaml`):
```bash
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o-mini
ELEVENLABS_API_KEY=sk_...
ELEVENLABS_VOICE_ID=TX3LPaxmHKxFdv7VOQHJ
BIGKINDS_ACCESS_KEY=...
KAKAO_CLIENT_ID=...
DDB_NEWS_TABLE=NewsCards
DDB_FREQ_TABLE=Frequencies
DDB_USERS_TABLE=Users
DDB_BOOKMARKS_TABLE=Bookmarks
S3_BUCKET=briefly-news-audio
```

⚠️ **SECURITY WARNING:** The `template.yaml` should not have hardcoded API keys. Before deploying to production:
1. Move all secrets to AWS Secrets Manager or Parameter Store
2. Update Lambda environment variables to reference secrets
3. Rotate all exposed keys immediately

## Common Development Patterns

### Adding a New Backend API Route
1. Create route file in `backend/app/routes/{name}.py`
2. Define router: `router = APIRouter(prefix="/api/{name}", tags=["{Name}"])`
3. Add authentication with `Depends(get_current_user)` for protected routes
4. Register in `backend/app/main.py`: `app.include_router({name}.router)`
5. Update mobile API service in `mobile/src/services/api.ts`

### Adding a New Mobile Screen
1. Create screen file in `mobile/src/screens/{Name}Screen.tsx`
2. Define navigation types in `src/types/navigation.ts`
3. Add route to `MainNavigator.tsx` or `RootNavigator.tsx`
4. Import types from `src/types/`
5. Use API client from `src/services/api.ts`
6. Use theme from `src/contexts/ThemeContext.tsx`

**Example Screen Structure:**
```typescript
// mobile/src/screens/ExampleScreen.tsx
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTheme } from '../contexts/ThemeContext';

export const ExampleScreen: React.FC = () => {
  const { colors, spacing } = useTheme();

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
      <Text style={[styles.title, { color: colors.text }]}>
        Example Screen
      </Text>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
  },
});
```

### Adding a New Reusable Component
1. Create component in `mobile/src/components/{Name}.tsx`
2. Use TypeScript for prop types
3. Apply theme colors via `useTheme()` hook
4. Export from component file

### Adding a New DynamoDB Table
1. Define in `backend/template.yaml` under `Resources`
2. Add environment variable for table name
3. Create utility functions in `backend/app/utils/dynamo.py`
4. Update IAM policies if needed (`Policies` section)

### Modifying GPT Prompts
When updating prompts in `openai_service.py`:
- Keep Few-shot examples consistent with desired output format
- Test with multiple temperature values (0.3, 0.5, 0.7)
- Validate output length is within 1,800-2,200 char range
- Check that TTS-optimized formatting is preserved (natural breathing points, no overly long sentences)

## Testing Strategy

**Unit Tests** (`backend/test/`):
- `test_frequency_unit.py` - Core podcast generation logic
- `test_clustering.py` - Dual clustering algorithm
- `test_tts_service.py` - ElevenLabs integration

**Current Coverage:** 100% of core business logic (6/6 tests passing)

**When adding features:**
- Write unit tests for all new service functions
- Test error handling paths (API failures, rate limits)
- Use mocking for external API calls (OpenAI, ElevenLabs, BigKinds)

## Debugging Tips

**CloudWatch Logs:**
```bash
sam logs -n BrieflyApi --stack-name briefly-backend --tail
sam logs -n DailyBrieflyTask --stack-name briefly-backend --tail
```

**Local Testing of Scheduler:**
```python
# backend/test/test_scheduler_local.py
from app.tasks.scheduler import lambda_handler
lambda_handler({}, None)  # Simulate EventBridge trigger
```

**Common Issues:**

1. **"Rate Limit Error" from OpenAI**
   - Check `openai_service.py` retry logic
   - Consider adding exponential backoff
   - Monitor daily token usage in OpenAI dashboard

2. **"Table does not exist" in DynamoDB**
   - Verify table names in environment variables
   - Check AWS region configuration
   - Ensure SAM deployment completed successfully

3. **"Missing audio_url" in Frequencies**
   - Check S3 bucket permissions
   - Verify ElevenLabs API key is valid
   - Review `tts_service.py` error logs

4. **Kakao Login fails**
   - Ensure `nativeAppKey` in `app.json` matches Kakao Developer Console
   - For Android: Check `kakao{APP_KEY}://oauth` is registered in Kakao console
   - For iOS: Check URL scheme is properly configured
   - Rebuild the app after changing `app.json` plugins

## Performance Considerations

**Optimization Strategies in Use:**
- Parallel news collection across 8 categories (ThreadPoolExecutor with max_workers=5)
- Overfetching strategy: Request 60 articles, select best 30 per category
- Clustering threshold tuning (80% for physical, 75% for semantic)
- Token limits on all GPT inputs to minimize costs
- S3 presigned URLs instead of CloudFront (simpler architecture)
- DynamoDB GSI for efficient category+date queries

**Future Optimization Opportunities:**
- Implement Redis cache for frequently accessed news
- Add CloudFront CDN for S3 audio files
- Batch DynamoDB writes using `batch_write_item`
- Implement connection pooling for external APIs

## Project-Specific Conventions

**Naming Conventions:**
- Python: `snake_case` for functions/variables, `PascalCase` for classes
- TypeScript: `camelCase` for variables, `PascalCase` for components/types
- Database keys: `{entity}_{attribute}` (e.g., `news_id`, `user_id`)
- API routes: `/api/{resource}` pattern

**File Organization:**
- Backend services: One class/module per external API
  - `bigkinds_service.py` - BigKinds API 뉴스 수집
  - `content_scraper.py` - 원문 본문 추출 (Selector 기반)
  - `openai_service.py` - GPT 요약 및 클러스터링
  - `tts_service.py` - ElevenLabs TTS 음성 변환
- Mobile app: Flat screen organization
  - `screens/` - All screens in one folder (e.g., `HomeScreen.tsx`)
  - `components/` - Reusable components
  - `contexts/` - React Context providers
  - `services/api.ts` - Single API client
- Types: Shared types in `types/` directory

**Logging:**
- Use emoji prefixes for visibility: ✅ (success), ⚠️ (warning), ❌ (error)
- Include context: category, user_id, article count, etc.
- Log entry/exit of major operations with elapsed time

**Git Workflow:**
- Current branch: `frontend_v2` (mobile app development)
- Main branch: `master`
- Commit messages: Use Korean for consistency with README
- No force pushes to master

## Key Dependencies (Mobile)

**Core:**
- `expo` ~54.0.23 - Expo SDK
- `react-native` 0.81.5 - React Native
- `react` 19.1.0 - React

**Navigation:**
- `@react-navigation/native` ^7.x - Navigation core
- `@react-navigation/bottom-tabs` ^7.x - Bottom tabs
- `@react-navigation/stack` ^7.x - Stack navigator

**Auth:**
- `@react-native-kakao/core` ^2.x - Kakao SDK core
- `@react-native-kakao/user` ^2.x - Kakao user login

**Audio:**
- `expo-av` ^16.x - Audio playback

**Storage:**
- `expo-secure-store` ~15.x - Secure token storage
- `@react-native-async-storage/async-storage` ^2.x - General storage

**Note:** This project requires native builds (Expo Go not supported due to native Kakao SDK).
