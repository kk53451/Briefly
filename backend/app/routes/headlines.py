from fastapi import APIRouter, HTTPException, Query
from app.utils.dynamo import (
    get_headlines_by_category_and_date,
    get_all_headlines_by_date,
    get_news_card_by_id
)
from app.constants.category_map import CATEGORY_MAP
from datetime import datetime
import pytz

router = APIRouter(prefix="/api/headlines", tags=["Headlines"])


@router.get("/")
@router.get("")
def get_headlines(
    category: str = Query(None, description="카테고리 (영문: politics, economy 등). 생략 시 전체"),
    date: str = Query(None, description="날짜 (YYYY-MM-DD). 기본값은 오늘")
):
    """
    오늘의 브리핑 헤드라인 조회

    - category 지정: 해당 카테고리의 상위 6개 헤드라인 반환
    - category 미지정: 전체 카테고리에서 클러스터 크기 기준 상위 6개 반환
    - 각 헤드라인은 GPT 생성 제목, 요약, 대표 기사 정보 포함

    Response:
    {
        "date": "2024-01-15",
        "category": "all" | "politics" | ...,
        "headlines": [
            {
                "headline_id": "...",
                "title": "14년만에 애플이 삼성 추월?",
                "summary": "애플이 올해 삼성전자를 제치고...",
                "cluster_size": 12,
                "representative_news_id": "NEWS_001",
                "category": "tech",
                "category_ko": "IT/과학",
                "news": { ... }  # 대표 기사 상세 정보
            },
            ...
        ]
    }
    """
    kst = pytz.timezone("Asia/Seoul")
    if not date:
        date = datetime.now(kst).strftime("%Y-%m-%d")

    print(f"📰 [Headlines] 조회 요청 - 카테고리: {category or '전체'}, 날짜: {date}")

    try:
        if category:
            # 특정 카테고리 헤드라인 조회
            # 영문 카테고리인지 확인
            valid_categories = [c["api_name"] for c in CATEGORY_MAP.values()]
            if category not in valid_categories:
                # 한글 카테고리일 수도 있음
                if category in CATEGORY_MAP:
                    category = CATEGORY_MAP[category]["api_name"]
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"지원하지 않는 카테고리입니다: {category}"
                    )

            item = get_headlines_by_category_and_date(category, date)
            if not item or not item.get("headlines"):
                return {
                    "date": date,
                    "category": category,
                    "headlines": []
                }

            headlines = item.get("headlines", [])[:6]

            # 대표 기사 정보 추가
            enriched_headlines = _enrich_headlines_with_news(headlines)

            return {
                "date": date,
                "category": category,
                "headlines": enriched_headlines
            }

        else:
            # 전체 카테고리에서 상위 6개
            all_headlines = get_all_headlines_by_date(date)

            if not all_headlines:
                return {
                    "date": date,
                    "category": "all",
                    "headlines": []
                }

            # 상위 6개만 선택
            top_headlines = all_headlines[:6]

            # 대표 기사 정보 추가
            enriched_headlines = _enrich_headlines_with_news(top_headlines)

            print(f"✅ [Headlines] 전체 상위 {len(enriched_headlines)}개 반환")

            return {
                "date": date,
                "category": "all",
                "headlines": enriched_headlines
            }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [Headlines] 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"헤드라인 조회 실패: {str(e)}")


def _enrich_headlines_with_news(headlines: list) -> list:
    """
    헤드라인에 대표 기사 상세 정보 추가
    """
    enriched = []
    for headline in headlines:
        news_id = headline.get("representative_news_id")
        if news_id:
            try:
                news = get_news_card_by_id(news_id)
                if news:
                    headline["news"] = {
                        "news_id": news.get("news_id"),
                        "title": news.get("title"),
                        "images": news.get("images"),
                        "provider": news.get("provider"),
                        "provider_link_page": news.get("provider_link_page"),
                        "published_at": news.get("published_at")
                    }
            except Exception as e:
                print(f"⚠️ 대표 기사 조회 실패 (news_id: {news_id}): {e}")

        enriched.append(headline)

    return enriched
