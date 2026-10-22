# Briefly 데이터 서빙 전수검사 보고서

> **보존 기록 (2026-10-23 정리)**: 작성 당시의 설계·실험 문서입니다. 본문의 경로·설정·진행 상태는 당시 기준이며 현재 동작과 다를 수 있습니다.
> 현행 구조는 [루트 README](../../README.md), 이전 코드의 복구는 [DEPRECATED 안내](../DEPRECATED.md)를 참고하세요.

**작성일**: 2026-04-27
**범위**: `backend_v2_supabase` (파이프라인·DB) + `flutter` (클라이언트 화면)
**목적**: 사용자에게 노출되는 데이터의 **단위와 출처**를 명확히 정리해 구조 재점검의 기반으로 삼는다.

---

## TL;DR

- 사용자에게 서빙되는 콘텐츠는 **세 가지 단위**가 병행 중이다.
  1. **개별 기사** (`news_cards` 테이블, 1행 = 클러스터의 **대표 기사 1건**)
  2. **토픽 묶음** (`headlines.items` jsonb, 1 item = 클러스터 1개의 헤드라인+요약+키워드)
  3. **팟캐스트 회차** (`podcasts` 테이블, 1행 = AM 또는 PM 통합 브리핑)
- **Home / Search / NewsDetail**은 `news_cards`를, **Today**는 `headlines.items`를, **Podcast**는 `podcasts` + 보조로 `headlines`를 사용한다.
- 같은 클러스터의 데이터가 **`news_cards`와 `headlines.items`에 이중 저장**된다 (대표 기사 메타가 양쪽에 모두 들어있음).
- **검색은 `news_cards`의 `title / hilight / content`만 본다** — 토픽의 키워드, 헤드라인 카피, 요약, 클러스터 멤버 텍스트는 검색 대상이 아니다.
- **클러스터 멤버를 펼쳐 보는 UX는 어느 화면에도 없다.** `cluster_size`는 "관련 N건" 메타 텍스트로만 노출된다.

---

## 1. 데이터 모델 (현재 스키마)

### 1.1 `news_cards` — 카테고리 피드용 대표 기사
**마이그레이션**: `app/db/migrations/0001_init_schema.sql:8-30`, `0009_add_news_cards_hero_image.sql`

```
news_id (PK)  category  date  slot(AM|PM)  rank  cluster_size
title  hilight(lede)  content
images(목록 썸네일)  hero_image(og:image / 본문 첫 사진)
provider  byline  provider_link_page  published_at  collected_at
```

- **1 row = 1 클러스터의 대표 기사 1건.** 카테고리×slot당 `rank` 1..N으로 정렬.
- 인덱스: `(category, date, rank)`, `(date, slot, rank)`, 검색용 trigram GIN(title/hilight/content).
- 클러스터의 **나머지 멤버는 저장되지 않는다** — 멤버 정보는 `cluster_size` 정수 한 값뿐.

### 1.2 `headlines` — 오늘의 브리핑
**마이그레이션**: `0001_init_schema.sql:51-62`

```
category  date  slot  items (jsonb 배열)  headline_count
```

`items[]` 각 항목 구조 (`supabase_storage_service.py:291-302`):

```json
{
  "topic_id": 1,
  "headline": "추경 35조 합의 초읽기",       // Gemma4 생성, 15~25자
  "summary": "정부가 추가경정예산...",        // Gemma4 생성, 80~120자
  "cluster_size": 47,
  "representative_news_id": "naver_123_456",
  "representative_title": "...",
  "representative_image": "...",              // 썸네일
  "representative_hero_image": "...",         // 고해상도
  "representative_press": "조선일보",
  "keywords": ["추경", "35조", "합의"]
}
```

- **1 row = 카테고리×slot 1개**. 따라서 카테고리 8개 × AM/PM = 하루 16행.
- **검색 인덱싱이 불가능한 jsonb** — 토픽 단위 검색은 이 테이블 그대로는 어렵다.
- `representative_news_id`는 `news_cards.news_id`와 같은 키지만 외래키 제약은 없다.

### 1.3 `podcasts` — 통합 브리핑 회차
**마이그레이션**: `0005_rename_frequencies_to_podcasts.sql`, `0007/0008` (title, covered_keywords, duration_sec 추가)

```
id  date  slot(UNIQUE)  script  audio_path  title
covered_keywords (jsonb)  duration_sec  created_at
```

- **1 row = AM 또는 PM 통합 브리핑 1개.** (카테고리별 개별 팟캐스트는 폐지.)
- `covered_keywords`는 다음 회차의 **중복 토픽 제거용** 메타 — 사용자에게는 노출되지 않는다.

### 1.4 기타
- `profiles`: `auth.users` 1:1 확장. `interests` 텍스트 배열.
- `bookmarks`: 사용자별 스냅샷 비정규화 (`news_cards` FK 없음). PK = (user_id, news_id).

---

## 2. 백엔드 파이프라인 (수집 → 노출)

| 단계 | 파일 | 산출물 |
|---|---|---|
| 수집 | `services/naver_news_service.py:79~465` | Naver 카테고리 페이지 + 상세 스크랩 (BigKinds 미사용 상태). 카테고리당 ~수백 건 |
| 본문 정제 | `naver_news_service.py:40,42` | 바이라인·저작권 제거, 본문 200자 미만 컷 |
| 클러스터링 | `services/clustering_service.py:1~780` | Near-dup(>0.95) 제거 → UMAP 15d → HDBSCAN. 토픽 객체 산출 |
| 헤드라인/요약 | `services/headline_service.py:1~200` | 로컬 Ollama Gemma4 — 토픽당 `headline + summary` |
| 키워드 | `clustering_service.py:36-83, 663` | KoNLPy Okt 명사 + 한글 불용어 + 정규식 fallback. **토픽에만 부착** |
| 저장 | `services/supabase_storage_service.py:216~302` | `news_cards`(대표 기사), `headlines`(items jsonb) **양쪽에 저장** |
| 팟캐스트 | (스크립트 → NotebookLM 오디오 → Supabase Storage) | `podcasts.audio_path = "{date}/briefing_{slot}.mp3"` |

**RPC 함수**: 데이터 조회용 RPC는 **`search_news_cards` 한 개뿐** (그것도 이번 작업에서 추가). 그 외 클라이언트는 Supabase 테이블을 **직접 SELECT** 한다.

**RLS** (`0002_rls_policies.sql`): `news_cards / headlines / podcasts` 모두 anon·authenticated에 공개 SELECT. 쓰기는 service_role.

---

## 3. 화면별 서빙 데이터 매핑

| 화면 | Repository / Provider | 호출 대상 | 단위 | 표시되는 필드 |
|---|---|---|---|---|
| **HomeScreen** (`features/home/home_screen.dart`) | `news_cards_repository.dart:31~78` (`homeNewsProvider`) | `news_cards` SELECT (category/date/rank) | **개별 기사** | title, image, category, provider, `cluster_size`("관련 N건"), timeLabel |
| **TodayScreen** (`features/today/today_screen.dart`) | `headlines_repository.dart:19~54` (`todayHeadlinesProvider`) | `headlines` SELECT → `items[0]`만 파싱 | **토픽 묶음** | headline, summary, representativeImage, representativePress, keywords, clusterSize |
| **SearchScreen** (`features/search/search_screen.dart`) | `search_repository.dart:13~24` | RPC `search_news_cards(q, lim)` (= `news_cards` ILIKE) | **개별 기사** | category, provider, timeLabel, title, hilight |
| **NewsDetailScreen** (`features/news_detail/news_detail_screen.dart`) | `news_cards_repository.dart:47~54` (`newsCardByIdProvider`) | `news_cards` 단건 | **개별 기사 1건** | title, category, image, hilight(AI 요약 자리), content, clusterSize(텍스트만) |
| **PodcastScreen** (`features/frequency/podcast_screen.dart`) | `podcast_repository.dart:79~86` + `headlines_repository.dart:901` | `podcasts` 최신 + 동일 date/slot의 `headlines` 6개 | **에피소드 + 토픽 부섹션** | title, dateKo, slot, durationSec, audioPath + 토픽 헤드라인 6개 |
| **EpisodesScreen** | `podcast_repository.dart:84~86` | `podcasts` 최근 14건 | **에피소드** | dateShort, slot, title, durationLabel |
| **ProfileScreen** | `profile_repository.dart` | `profiles` 본인 행 | UserProfile | 정적 통계는 placeholder |

### 3.1 데이터 단위 비대칭

```
HomeScreen     →  news_cards    →  개별 기사 (대표 1건)
SearchScreen   →  news_cards    →  개별 기사 (대표 1건)
NewsDetail     →  news_cards    →  개별 기사 (대표 1건)
TodayScreen    →  headlines     →  토픽 묶음 (헤드라인+요약+키워드)
PodcastScreen  →  podcasts      →  에피소드
```

**Home 카드를 탭해도, Today 카드를 탭해도 결국 같은 `/news/{id}` (= `news_cards` 단건)로 이동한다.** 그러나 두 화면이 보여주는 데이터의 *단위*는 다르다 — Home은 "기사", Today는 "토픽".

---

## 4. 발견된 이슈

### 이슈 ① 검색이 클러스터 텍스트 일부만 본다
- 검색 인덱스 대상: `news_cards.title / hilight / content` — 즉 **대표 기사의 텍스트만**.
- 사용자가 클러스터 내 **다른 기사**의 제목/본문에만 등장하는 단어로 검색하면 그 토픽이 매칭되지 않는다.
- **토픽의 keywords는 `headlines.items` jsonb에만 있어 검색 대상이 아니다.**
- Gemma4가 만든 `headline` / `summary` 카피도 검색되지 않는다 — 사용자가 평소 보던 헤드라인 문구로 검색하면 매칭률이 떨어진다.

### 이슈 ② 토픽 ↔ 기사 단위가 화면마다 섞인다
- Today에서는 "토픽 1개"로 보던 묶음을 Home에서는 "기사 1건"으로 보고, 검색 결과에서는 다시 "기사 1건"으로 본다.
- 같은 콘텐츠를 보는 멘탈모델이 화면마다 달라진다.
- `cluster_size="관련 N건"` 메타가 모든 화면에 노출되지만 **그 N건을 펼쳐서 보는 화면은 없다.**

### 이슈 ③ 같은 토픽이 두 테이블에 중복 저장
- `news_cards`(대표 기사)와 `headlines.items[*]`(토픽 묶음)에 같은 `representative_news_id`·`representative_title`·`representative_image`·`representative_hero_image`가 각각 들어간다.
- 외래키 제약 없음 → 한쪽이 틀어지면 화면이 깨질 수 있다 (예: Today 토픽의 `representative_news_id`가 `news_cards`에 없으면 NewsDetail 진입 시 404).

### 이슈 ④ 클러스터 멤버 미저장
- 파이프라인에서는 `member_indices`, `selected_articles`를 갖고 있지만 (`clustering_service.py:644~664`) DB에 저장하지 않는다.
- 결과적으로 **"이 토픽 관련 기사 N건"의 N건을 사용자가 절대 볼 수 없다.** clusterSize 텍스트는 약속만 있고 실체가 없다.

### 이슈 ⑤ 키워드는 만들지만 일부 화면에서만 쓴다
- `headlines.items[].keywords`는 Today에서만 칩으로 표시.
- `news_cards`에는 keywords 컬럼 자체가 없음 → Home/Search/NewsDetail에서 키워드를 활용할 방법이 없다.

### 이슈 ⑥ Slot 정책이 화면마다 다른지 명확하지 않다
- `news_cards`는 `slot`이 PK 일부.
- `homeNewsProvider`가 어떤 slot을 보여주는지는 추가 점검 필요 — 시간대별 자동 선택인지, 모든 slot 합치기인지, 최신만인지 정책 통일 여부 확인 필요.

### 이슈 ⑦ 검색에 시간/카테고리 필터가 없다
- `search_news_cards(q, lim)`는 전체 기간·전체 카테고리 ILIKE.
- 카드 목록이 쌓일수록 옛날 기사가 상위에 노출될 가능성 (현재 `published_at desc nulls last`로 일부 완화).

---

## 5. 재점검 시 검토할 질문

1. **단위 정책**: 사용자에게 보여줄 콘텐츠의 1차 단위를 **토픽**으로 정할 것인가, **기사**로 정할 것인가?
   - 토픽 우선 → `news_cards`를 **`topic_cards`**로 의미를 명확화하고, 멤버 기사는 별도 테이블로 분리.
   - 기사 우선 → 클러스터링 결과를 풀어서 멤버 기사를 모두 저장하고 토픽은 그룹핑 메타로만 사용.

2. **클러스터 멤버 저장 여부**: 멤버를 노출할 계획이라면 `topic_members` 또는 `news_cards.cluster_id`를 도입해 펼쳐보기 UX를 제공할지.

3. **검색 대상 확장**: `news_cards`에 `keywords text[]`, `headline text`, `summary text` 컬럼을 추가해 RPC ILIKE 대상을 확장할지. 또는 `headlines.items` 정규화 테이블(`headline_topics`)을 분리해 토픽 키워드 GIN 인덱스를 걸지.

4. **테이블 책임 재정의**: 현재 `news_cards`와 `headlines`는 같은 토픽을 다른 모양으로 두 번 저장한다.
   - A안: `headlines`를 view로 만들고 `news_cards` + `topic_meta` 정규화.
   - B안: `news_cards`를 폐기하고 `topics` + `topic_articles`로 정규화.

5. **NewsDetail의 정체성**: 단일 기사 상세인지, 토픽 디테일인지. 현재는 단일 기사인데 헤더에는 cluster_size가 나온다 — 둘 중 하나로 정리.

6. **검색 디폴트 범위**: 최근 N일·카테고리 필터·랭킹 가중치(키워드 일치 가산점) 정책.

---

## 부록 — 핵심 파일 인덱스

**Backend**
- `backend_v2_supabase/app/db/migrations/0001_init_schema.sql` — news_cards/headlines/frequencies 스키마
- `backend_v2_supabase/app/db/migrations/0002_rls_policies.sql` — RLS
- `backend_v2_supabase/app/db/migrations/0005~0009_*.sql` — frequencies→podcasts 리네이밍, hero_image, title, covered_keywords, duration_sec
- `backend_v2_supabase/app/services/clustering_service.py:644~664` — 토픽 객체 구조
- `backend_v2_supabase/app/services/supabase_storage_service.py:216~302` — news_cards/headlines 저장 로직
- `backend_v2_supabase/app/services/headline_service.py:1~200` — Gemma4 헤드라인/요약 생성
- Supabase RPC: `search_news_cards(q text, lim int)` (이번 세션에 추가)

**Flutter**
- `flutter/lib/features/home/home_screen.dart` + `data/news_cards_repository.dart`
- `flutter/lib/features/today/today_screen.dart` + `data/headlines_repository.dart`
- `flutter/lib/features/search/search_screen.dart` + `data/search_repository.dart`
- `flutter/lib/features/news_detail/news_detail_screen.dart` (`newsCardByIdProvider`)
- `flutter/lib/features/frequency/podcast_screen.dart` + `episodes_screen.dart` + `data/podcast_repository.dart`
- `flutter/lib/shared/models/news_card.dart`, `headline_topic.dart`, `episode.dart`
