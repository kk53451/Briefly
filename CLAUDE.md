# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Briefly** is an AI-powered news podcast platform that automatically collects, summarizes, and converts daily news into personalized audio podcasts. The system runs fully automated with a serverless architecture on AWS.

**Core Technology Stack:**
- Frontend: Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui
- Backend: FastAPI, Python 3.12, AWS Lambda (SAM)
- AI Services: OpenAI GPT-4o-mini, ElevenLabs TTS
- Data: DynamoDB (4 tables), S3 (audio storage)
- Scheduler: AWS EventBridge (daily 6 AM KST)

## Development Commands

### Frontend (Next.js)
```bash
cd frontend
npm install              # Install dependencies
npm run dev             # Start dev server (http://localhost:3000)
npm run build           # Production build
npm run lint            # Run ESLint
```

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
   - BigKinds API: 200 articles requested → 70 selected per category
   - Total: 8 categories × 70 articles = 560 articles/day
   - Parallel processing using `ThreadPoolExecutor` (max_workers=6)
   - Content scraping: 300+ chars, 70%+ Korean text validation
   - Deduplication: ID, URL, title (memory + DB check)

2. **Union-Find 2-Pass Clustering Strategy** (`app/services/openai_service.py`)
   - **Pass 1 - Union-Find Deduplication**: Physical deduplication using Union-Find algorithm (85% threshold)
     - All-pairs comparison (O(n²/2)) to discover indirect connections (A→B, B→C → A-B-C merged)
     - Path compression for efficiency
     - Groups similar articles into clusters, longest article becomes representative
   - **Pass 2 - Hybrid Outlier Filtering**: Centroid + Isolation based filtering (AND condition)
     - **Centroid-based**: Measures distance from category center (threshold < 0.30)
     - **Isolation-based**: Measures max similarity with other articles (threshold < 0.25)
     - **AND condition**: Article removed only if BOTH thresholds are violated
     - Keeps legitimate unique articles, removes only true ads/spam
     - **Performance optimized**: Similarity matrix caching to avoid redundant calculations
   - **Cosine similarity**: OpenAI text-embedding-3-small based embeddings
   - Reduces 70 articles → 50-57 articles per category
   - Saves 50% on token costs
   - Execution time: ~8-9 minutes per full cycle (8 categories)

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

### Frontend Architecture

**App Router Structure** (`frontend/app/`)
- `/home` - Provider-grouped latest news (언론사별 최신 뉴스, API: GET /api/news/home)
- `/today` - Category-grouped news (카테고리별 뉴스, API: GET /api/news/today)
- `/frequency` - Personalized podcast player
- `/profile` - User settings & category preferences
- `/news/[id]` - News detail view
- `/onboarding` - Initial setup flow
- `/login/kakao/callback` - OAuth callback handler

**Key Components** (`frontend/components/`)
- `news-card.tsx` - Reusable news card with bookmark toggle
- `audio-player.tsx` - Custom audio player for podcasts
- `category-filter.tsx` - Category selection UI
- `navigation-tabs.tsx` - Bottom tab navigation

**Tab-to-API Mapping**

| Tab | Route | Backend API | Description |
|-----|-------|-------------|-------------|
| Home | `/home` | `GET /api/news/home` | 언론사별로 그룹핑된 최신 뉴스 (각 언론사당 6개, 첫 번째는 이미지 보장) |
| Today | `/today` | `GET /api/news/today` | 카테고리별로 그룹핑된 뉴스 (각 카테고리당 6개, 이미지 있는 것만) |
| Frequency | `/frequency` | `GET /api/frequency?category={category}&date={date}` | 카테고리별 팟캐스트 스크립트 및 오디오 |
| Profile | `/profile` | `GET /api/user/profile` | 사용자 프로필 및 북마크 정보 |

**API Client** (`frontend/lib/api.ts`)
- Centralized REST API calls to backend
- JWT token management via localStorage
- Base URL configuration for different environments

### Authentication Flow

1. User clicks "Login with Kakao"
2. Frontend redirects to `/api/auth/kakao/login`
3. Backend redirects to Kakao OAuth page
4. User authorizes → Kakao redirects to `/api/auth/kakao/callback?code=...`
5. Backend exchanges code for Kakao access token
6. Backend fetches user info from Kakao API
7. Backend creates/updates user in DynamoDB
8. Backend generates JWT token with `user_id`
9. Frontend stores JWT in localStorage, redirects to app

**Token Usage:**
- All protected endpoints require `Authorization: Bearer {token}` header
- Token validation via `get_current_user()` dependency in FastAPI
- Token contains: `{"sub": "kakao_{id}", "exp": timestamp}`

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

## Environment Variables

**Backend** (`.env` or `template.yaml`):
```bash
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o-mini
ELEVENLABS_API_KEY=sk_...
ELEVENLABS_VOICE_ID=TX3LPaxmHKxFdv7VOQHJ
BIGKINDS_ACCESS_KEY=...
KAKAO_CLIENT_ID=...
KAKAO_REDIRECT_URI=https://your-domain.com/api/auth/kakao/callback
DDB_NEWS_TABLE=NewsCards
DDB_FREQ_TABLE=Frequencies
DDB_USERS_TABLE=Users
DDB_BOOKMARKS_TABLE=Bookmarks
S3_BUCKET=briefly-news-audio
```

**Frontend** (`.env.local`):
```bash
NEXT_PUBLIC_API_URL=https://your-api-gateway-url
NEXT_PUBLIC_KAKAO_CLIENT_ID=...
```

⚠️ **SECURITY WARNING:** The `template.yaml` currently has hardcoded API keys. Before deploying to production:
1. Move all secrets to AWS Secrets Manager or Parameter Store
2. Update Lambda environment variables to reference secrets
3. Rotate all exposed keys immediately

## Common Development Patterns

### Adding a New API Route
1. Create route file in `backend/app/routes/{name}.py`
2. Define router: `router = APIRouter(prefix="/api/{name}", tags=["{Name}"])`
3. Add authentication with `Depends(get_current_user)` for protected routes
4. Register in `backend/app/main.py`: `app.include_router({name}.router)`
5. Update frontend API client in `frontend/lib/api.ts`

### Adding a New DynamoDB Table
1. Define in `backend/template.yaml` under `Resources`
2. Add environment variable for table name
3. Create utility functions in `backend/app/utils/dynamo.py`
4. Update IAM policies if needed (`Policies` section)

### Adding a New Frontend Page
1. Create `frontend/app/{route}/page.tsx`
2. Use server components by default, add `'use client'` only when needed
3. Import types from `frontend/types/`
4. Use API client from `frontend/lib/api.ts`
5. Add navigation link in `frontend/components/navigation-tabs.tsx` if needed

### Modifying GPT Prompts
When updating prompts in `openai_service.py`:
- Keep Few-shot examples consistent with desired output format
- Test with multiple temperature values (0.3, 0.5, 0.7)
- Validate output length is within 1,800-2,200 char range
- Check that TTS-optimized formatting is preserved (natural breathing points, no overly long sentences)

## Testing Strategy

**Unit Tests** (`backend/test/`):
- `test_frequency_unit.py` - Core podcast generation logic
- `test_clustering.py` - Union-Find 2-Pass clustering algorithm (deduplication + hybrid filtering)
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

4. **Kakao Login fails with "Invalid redirect_uri"**
   - Ensure `KAKAO_REDIRECT_URI` exactly matches Kakao Developer Console setting
   - Check for trailing slashes (should not have one)
   - Verify client ID matches the configured app

## Performance Considerations

**Optimization Strategies in Use:**
- Parallel news collection across 8 categories (ThreadPoolExecutor with max_workers=5)
- Overfetching strategy: Request 200 articles, select best 70 per category
- Union-Find 2-Pass clustering: deduplication (85%) + hybrid filtering (centroid+isolation)
- Similarity matrix caching to prevent redundant cosine similarity calculations
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
- Frontend components: Separate UI primitives from business logic
- Types: Shared types in `types/` directory, mirror backend models

**Logging:**
- Use emoji prefixes for visibility: ✅ (success), ⚠️ (warning), ❌ (error)
- Include context: category, user_id, article count, etc.
- Log entry/exit of major operations with elapsed time

**Git Workflow:**
- Current branch: `master` (main branch)
- Commit messages: Use Korean for consistency with README
- No force pushes to master
