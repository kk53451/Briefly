# 오늘의 브리핑 (Headlines Feature)

AI가 선정한 오늘의 주요 이슈를 보여주는 기능입니다.

## 개요

매일 수집되는 뉴스 기사들을 클러스터링하여 주요 이슈를 추출하고, GPT를 활용해 친근한 한국어 헤드라인과 요약을 생성합니다.

**핵심 특징:**
- 카테고리별 상위 6개 클러스터 추출 (총 48개)
- 전체 카테고리에서 cluster_size 기준 상위 6개 표시
- GPT 4o-mini로 헤드라인/요약 생성 (~요, ~해요 체)
- 대표 기사의 이미지, 링크 포함

## 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                    Daily Pipeline (6 AM KST)                     │
├─────────────────────────────────────────────────────────────────┤
│  1. 뉴스 수집 (collect_news.py)                                  │
│     └─ 8개 카테고리 × 70개 = 560개 기사                          │
│                              ↓                                   │
│  2. 주파수 생성 (generate_frequency.py)                          │
│     └─ 클러스터링 + 스크립트 + TTS                               │
│                              ↓                                   │
│  3. 헤드라인 생성 (generate_headlines.py)  ← NEW                 │
│     └─ 클러스터 메타데이터 + GPT 요약                            │
└─────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│                      DynamoDB Headlines                          │
├─────────────────────────────────────────────────────────────────┤
│  PK: category_date (e.g., "politics#2025-11-28")                │
│  headlines: [                                                    │
│    {                                                             │
│      headline_id, title, summary, cluster_size,                 │
│      representative_news_id, news_ids, category, category_ko   │
│    }, ...                                                        │
│  ]                                                               │
└─────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│                      API: GET /api/headlines                     │
├─────────────────────────────────────────────────────────────────┤
│  Query Params:                                                   │
│    - category (optional): "politics", "economy", etc.           │
│    - date (optional): "2025-11-28" (default: today)             │
│                                                                  │
│  Response:                                                       │
│    {                                                             │
│      date: "2025-11-28",                                        │
│      category: "all",                                           │
│      headlines: [{ ... enriched with news info ... }]           │
│    }                                                             │
└─────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Mobile: TodayScreen                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────┐                    │
│  │  11월 28일 목요일                        │                    │
│  │  오늘의 브리핑                           │                    │
│  │  ℹ️ AI가 선정한 오늘의 주요 이슈          │                    │
│  │                                         │                    │
│  │  ● ○ ○ ○ ○ ○  (Page Indicator)          │                    │
│  │                                         │                    │
│  │  ┌─────────────────────────────────┐    │                    │
│  │  │ 정치  3개 기사                   │    │                    │
│  │  │                                 │    │                    │
│  │  │ BNK금융 차기 회장 후보 4명 확정  │    │                    │
│  │  │ ─────────────────────────────── │    │                    │
│  │  │ BNK금융 임원후보추천위원회가     │    │                    │
│  │  │ 차기 회장 후보군으로 빈대인,     │    │                    │
│  │  │ 방성빈, 김성주, 안감찬 등       │    │                    │
│  │  │ 4명을 확정했어요...             │    │                    │
│  │  │                                 │    │                    │
│  │  │ [이미지]                        │    │                    │
│  │  │                                 │    │                    │
│  │  │ 뉴스핌                          │    │                    │
│  │  │                                 │    │                    │
│  │  │ [    자세히 보기    ]           │    │                    │
│  │  └─────────────────────────────┘    │                    │
│  │                        ← Swipe →    │                    │
│  └─────────────────────────────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

## 상세 흐름

### 1. 헤드라인 생성 (Backend)

**파일:** `backend/app/tasks/generate_headlines.py`

```python
def generate_headlines_for_category(category_ko: str, date: str):
    # 1. 해당 카테고리의 오늘 뉴스 조회
    news_list = get_news_by_category_and_date(category_en, date)

    # 2. 클러스터링 (메타데이터 포함)
    clusters = cluster_articles_with_metadata(news_list)
    # clusters = [
    #   {
    #     "cluster_id": 0,
    #     "article_ids": ["id1", "id2", "id3"],
    #     "representative_id": "id2",  # centroid와 가장 가까운 기사
    #     "size": 3
    #   }, ...
    # ]

    # 3. 상위 6개 클러스터 선택 (size 기준)
    top_clusters = sorted(clusters, key=lambda x: x["size"], reverse=True)[:6]

    # 4. 각 클러스터에 대해 GPT 헤드라인/요약 생성
    for cluster in top_clusters:
        articles = [get_article(id) for id in cluster["article_ids"]]
        result = generate_headline_summary(articles)
        # result = {
        #   "headline": "BNK금융 차기 회장 후보 4명 확정",
        #   "summary": "BNK금융 임원후보추천위원회가 차기 회장 후보군으로..."
        # }

    # 5. DynamoDB에 저장
    save_headlines(category_en, date, headlines)
```

### 2. 클러스터링 알고리즘

**파일:** `backend/app/services/openai_service.py`

```python
def cluster_articles_with_metadata(articles: list) -> list:
    """
    Union-Find 기반 클러스터링 + 메타데이터 반환

    Returns:
        [
            {
                "cluster_id": int,
                "article_ids": [str],
                "representative_id": str,  # centroid 기준
                "size": int
            }
        ]
    """
    # 1. 임베딩 생성 (text-embedding-3-small)
    embeddings = [get_embedding(a["title"] + a["content"][:1000]) for a in articles]

    # 2. 코사인 유사도 행렬 계산
    similarity_matrix = cosine_similarity(embeddings)

    # 3. Union-Find로 85% 이상 유사한 기사 병합
    for i, j in pairs:
        if similarity_matrix[i][j] >= 0.85:
            union(i, j)

    # 4. 클러스터별 centroid 계산 및 대표 기사 선정
    for cluster in clusters:
        centroid = mean(cluster_embeddings)
        representative = argmax(similarity(article, centroid))

    return cluster_metadata
```

### 3. GPT 헤드라인/요약 생성

**파일:** `backend/app/services/openai_service.py`

```python
def generate_headline_summary(cluster_articles: list) -> dict:
    """
    클러스터 기사들을 분석하여 헤드라인과 요약 생성

    Args:
        cluster_articles: 클러스터 내 기사 목록

    Returns:
        {"headline": str, "summary": str}
    """
    prompt = f"""
    다음은 같은 이슈에 대한 여러 기사입니다:

    {articles_text}

    위 기사들을 종합하여:
    1. 헤드라인 (15자 이내, 핵심 키워드 포함)
    2. 요약 (2-3문장, ~요/~해요 체, 친근하게)

    JSON 형식으로 응답:
    {{"headline": "...", "summary": "..."}}
    """

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5
    )

    return json.loads(response.choices[0].message.content)
```

### 4. API 엔드포인트

**파일:** `backend/app/routes/headlines.py`

```python
@router.get("/")
def get_headlines(category: str = None, date: str = None):
    """
    헤드라인 조회 API

    - category 미지정: 전체 카테고리에서 상위 6개
    - category 지정: 해당 카테고리의 6개
    """
    if not date:
        date = get_today_kst()

    if category:
        # 특정 카테고리
        headlines = get_headlines_by_category_and_date(category, date)
    else:
        # 전체 카테고리에서 상위 6개 (cluster_size 기준)
        all_headlines = get_all_headlines_by_date(date)
        headlines = sorted(all_headlines, key=lambda x: x["cluster_size"], reverse=True)[:6]

    # 대표 기사 정보 추가 (enrich)
    for h in headlines:
        news = get_news_by_id(h["representative_news_id"])
        h["news"] = {
            "news_id": news["news_id"],
            "title": news["title"],
            "images": news.get("images"),
            "provider": news["provider"],
            "provider_link_page": news.get("provider_link_page"),
            "published_at": news["published_at"]
        }

    return {
        "date": date,
        "category": category or "all",
        "headlines": headlines
    }
```

### 5. 모바일 화면

**파일:** `mobile/src/screens/TodayScreen.tsx`

```tsx
export const TodayScreen: React.FC = () => {
  const [headlines, setHeadlines] = useState<HeadlineItem[]>([]);

  useEffect(() => {
    loadHeadlines();
  }, []);

  const loadHeadlines = async () => {
    const response = await apiClient.getHeadlines();
    setHeadlines(response.headlines);
  };

  return (
    <SafeAreaView>
      {/* Header */}
      <Text>오늘의 브리핑</Text>
      <Text>AI가 선정한 오늘의 주요 이슈</Text>

      {/* Page Indicator */}
      <PageIndicator count={headlines.length} current={currentIndex} />

      {/* Swipeable Cards */}
      <FlatList
        horizontal
        pagingEnabled
        data={headlines}
        renderItem={({ item }) => <HeadlineCard item={item} />}
      />
    </SafeAreaView>
  );
};
```

**파일:** `mobile/src/components/HeadlineCard.tsx`

```tsx
export const HeadlineCard: React.FC<{ item: HeadlineItem }> = ({ item }) => {
  return (
    <View style={styles.card}>
      {/* Category Badge + Article Count */}
      <Badge>{item.category_ko}</Badge>
      <Badge>{item.cluster_size}개 기사</Badge>

      {/* GPT Generated Title */}
      <Text style={styles.headline}>{item.title}</Text>

      {/* GPT Generated Summary */}
      <Text style={styles.summary}>{item.summary}</Text>

      {/* Representative Article Image */}
      {item.news?.images && <Image source={{ uri: item.news.images }} />}

      {/* Provider */}
      <Text>{item.news?.provider}</Text>

      {/* Detail Button */}
      <TouchableOpacity onPress={() => Linking.openURL(item.news?.provider_link_page)}>
        <Text>자세히 보기</Text>
      </TouchableOpacity>
    </View>
  );
};
```

## 데이터 모델

### DynamoDB: Headlines 테이블

| 속성 | 타입 | 설명 |
|------|------|------|
| `category_date` (PK) | String | `{category}#{date}` (e.g., "politics#2025-11-28") |
| `headlines` | List | 헤드라인 배열 |
| `created_at` | String | ISO 8601 형식 |

**headlines 배열 아이템:**

| 속성 | 타입 | 설명 |
|------|------|------|
| `headline_id` | String | UUID |
| `title` | String | GPT 생성 헤드라인 (15자 이내) |
| `summary` | String | GPT 생성 요약 (~요/~해요 체) |
| `cluster_size` | Number | 클러스터 내 기사 수 |
| `representative_news_id` | String | 대표 기사 ID |
| `news_ids` | List[String] | 클러스터 내 모든 기사 ID |
| `category` | String | 영문 카테고리 |
| `category_ko` | String | 한글 카테고리 |

### API Response

```json
{
  "date": "2025-11-28",
  "category": "all",
  "headlines": [
    {
      "headline_id": "bee22e20-ba50-45aa-a600-58583ea6c5c9",
      "title": "BNK금융 차기 회장 후보 4명 확정",
      "summary": "BNK금융 임원후보추천위원회가 차기 회장 후보군으로 빈대인, 방성빈, 김성주, 안감찬 등 4명을 확정했어요...",
      "cluster_size": 3,
      "representative_news_id": "04100078.20251128081953001",
      "news_ids": ["02100501.20251128064646001", "04100078.20251128081953001", "06101202.20251128013743001"],
      "category": "politics",
      "category_ko": "정치",
      "news": {
        "news_id": "04100078.20251128081953001",
        "title": "BNK금융, 회장 2차 후보군으로 빈대인·방성빈·김성주·안감찬 확정",
        "images": "https://www.bigkinds.or.kr/resources/images/...",
        "provider": "뉴스핌",
        "provider_link_page": "https://www.newspim.com/news/view/...",
        "published_at": "2025-11-28T00:00:00.000+09:00"
      }
    }
  ]
}
```

## 관련 파일

### Backend
- `app/tasks/generate_headlines.py` - 헤드라인 생성 태스크
- `app/tasks/scheduler.py` - 일일 스케줄러 (3단계 추가)
- `app/services/openai_service.py` - 클러스터링 및 GPT 호출
- `app/routes/headlines.py` - API 라우터
- `app/utils/dynamo.py` - DynamoDB 헬퍼 함수

### Mobile
- `src/screens/TodayScreen.tsx` - 오늘의 브리핑 화면
- `src/components/HeadlineCard.tsx` - 헤드라인 카드 컴포넌트
- `src/services/api.ts` - API 클라이언트
- `src/types/api.ts` - 타입 정의

## 환경 변수

```bash
# Backend (template.yaml)
DDB_HEADLINES_TABLE=Headlines
```

## 테스트

```bash
# API 테스트
curl "https://o5t9kv1ms7.execute-api.ap-northeast-2.amazonaws.com/Prod/api/headlines"

# 특정 카테고리
curl "https://o5t9kv1ms7.execute-api.ap-northeast-2.amazonaws.com/Prod/api/headlines?category=politics"

# 특정 날짜
curl "https://o5t9kv1ms7.execute-api.ap-northeast-2.amazonaws.com/Prod/api/headlines?date=2025-11-28"
```

## 향후 개선 사항

- [ ] 클러스터 내 모든 기사 목록 보기 UI
- [ ] 헤드라인 북마크 기능
- [ ] 푸시 알림 연동 (주요 이슈 알림)
- [ ] 사용자 관심 카테고리 기반 정렬
