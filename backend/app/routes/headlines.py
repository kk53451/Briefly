from fastapi import APIRouter, HTTPException, Query
from app.utils.dynamo import (
    get_headlines_by_category_and_date,
    get_all_headlines_by_date,
)
from app.constants.category_map import CATEGORY_MAP
from datetime import datetime
import pytz

router = APIRouter(prefix="/api/headlines", tags=["Headlines"])


@router.get("/")
@router.get("")
def get_headlines(
    category: str = Query(None, description="카테고리 (영문: politics, economy 등). 생략 시 전체"),
    date: str = Query(None, description="날짜 (YYYY-MM-DD). 기본값은 오늘"),
    slot: str = Query(default="AM", description="브리핑 슬롯 (AM 또는 PM)"),
    limit: int = Query(default=8, ge=1, le=30, description="반환할 헤드라인 최대 수 (전체 조회 시)"),
):
    """
    오늘의 브리핑 헤드라인 조회 (v2 데이터 전용)

    - category 지정: 해당 카테고리 토픽 헤드라인 반환
    - category 미지정: 전체 카테고리에서 클러스터 크기 기준 상위 반환
    - slot=AM (오전) 또는 PM (오후)

    Response:
    {
        "date": "2026-04-17",
        "slot": "AM",
        "category": "all" | "economy" | ...,
        "headlines": [
            {
                "topic_id": 0,
                "headline": "ETF 400조 시대, 개미는 어디로?",
                "summary": "국내 ETF 시장이 400조원을 돌파했어요...",
                "cluster_size": 46,
                "representative_title": "레버리지·곱버스 몰리는...",
                "representative_image": "https://...",
                "representative_press": "한국경제",
                "keywords": ["ETF", "레버리지"]
            }
        ]
    }
    """
    kst = pytz.timezone("Asia/Seoul")
    if not date:
        date = datetime.now(kst).strftime("%Y-%m-%d")

    print(f"📰 [Headlines] 조회 - 카테고리: {category or '전체'}, 날짜: {date}, 슬롯: {slot}")

    try:
        if category:
            # 카테고리 이름 정규화 (한글 → 영문)
            valid_categories = [c["api_name"] for c in CATEGORY_MAP.values()]
            if category not in valid_categories:
                if category in CATEGORY_MAP:
                    category = CATEGORY_MAP[category]["api_name"]
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"지원하지 않는 카테고리입니다: {category}"
                    )

            item = get_headlines_by_category_and_date(category, date, slot)
            headlines = item.get("headlines", []) if item else []

            return {
                "date": date,
                "slot": slot,
                "category": category,
                "headlines": headlines,
            }

        else:
            # 전체 카테고리 — cluster_size 기준 상위 limit개만 반환
            all_headlines = get_all_headlines_by_date(date, slot)
            top_headlines = (all_headlines or [])[:limit]

            return {
                "date": date,
                "slot": slot,
                "category": "all",
                "headlines": top_headlines,
            }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [Headlines] 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"헤드라인 조회 실패: {str(e)}")
