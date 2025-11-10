# app/routes/test.py

"""
테스트 및 개발용 엔드포인트

주의: 운영 환경에서는 이 라우터를 비활성화하거나 제거해야 함
"""

from fastapi import APIRouter, Query, HTTPException
from datetime import datetime, timedelta
import pytz

from app.services.bigkinds_service import fetch_bigkinds_news
from app.tasks.collect_news import collect_category_news
from app.constants.category_map import CATEGORY_MAP, CATEGORY_KO_LIST

router = APIRouter(prefix="/api/test", tags=["Test"])


@router.get("/bigkinds/categories")
def get_bigkinds_categories():
    """
    BigKinds API에서 지원하는 카테고리 목록 조회

    Returns:
        dict: 카테고리 정보
    """
    return {
        "total_categories": len(CATEGORY_MAP),
        "categories": [
            {
                "korean_name": ko_name,
                "api_name": config["api_name"],
                "bigkinds_code": config["bigkinds_code"],
                "bigkinds_name": config["bigkinds_name"]
            }
            for ko_name, config in CATEGORY_MAP.items()
        ]
    }


@router.get("/bigkinds/fetch")
def test_bigkinds_fetch(
    category: str = Query("정치", description="한글 카테고리명"),
    size: int = Query(1, description="가져올 뉴스 개수", ge=1, le=100)
):
    """
    BigKinds API로 오늘 뉴스 가져오기 테스트 (빠른 테스트용)

    Args:
        category: 한글 카테고리명 (예: "정치", "경제", "사회", "문화", "국제", "지역", "스포츠", "IT/과학")
        size: 가져올 뉴스 개수 (1~100, 기본값 1)

    Returns:
        dict: BigKinds API 응답 및 통계
    """
    if category not in CATEGORY_MAP:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 카테고리: {category}. 지원 카테고리: {CATEGORY_KO_LIST}"
        )

    # 오늘 날짜 기준
    kst = pytz.timezone("Asia/Seoul")
    now = datetime.now(kst)
    today = now.strftime("%Y-%m-%d")
    tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        documents = fetch_bigkinds_news(
            category_ko=category,
            date_from=today,
            date_until=tomorrow,  # until은 exclusive이므로 내일 날짜 사용
            size=size,
            sort_by="relation",  # 정확도 순 (관련도 높은 순)
            sort_order="desc"
        )

        # 응답 가공
        news_list = []
        for idx, doc in enumerate(documents, start=1):
            images = doc.get("images", [])
            news_list.append({
                "rank": idx,
                "news_id": doc.get("news_id"),
                "title": doc.get("title"),
                "provider": doc.get("provider"),
                "published_at": doc.get("published_at"),
                "category": doc.get("category"),
                "byline": doc.get("byline"),
                "provider_link_page": doc.get("provider_link_page"),
                "image": images[0] if images else None,
                "content_preview": doc.get("content", "")[:100] + "..." if doc.get("content") else None,
                "images_count": len(images)
            })

        return {
            "success": True,
            "date": today,
            "category": category,
            "total_fetched": len(documents),
            "requested_size": size,
            "news": news_list
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"BigKinds API 오류: {str(e)}")


@router.get("/collect/single-category")
def test_collect_single_category(
    category: str = Query("정치", description="한글 카테고리명"),
    limit: int = Query(3, description="최종 저장할 기사 수", ge=1, le=10)
):
    """
    단일 카테고리 뉴스 수집 테스트 (본문 스크래핑 포함)

    주의: 본문 스크래핑으로 시간이 걸릴 수 있음 (기사당 3~5초)

    Args:
        category: 한글 카테고리명
        limit: 최종 저장할 기사 수 (1~10, 기본 3)

    Returns:
        dict: 수집 결과
    """
    if category not in CATEGORY_MAP:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 카테고리: {category}. 지원 카테고리: {CATEGORY_KO_LIST}"
        )

    # 오늘 날짜 기준
    kst = pytz.timezone("Asia/Seoul")
    now = datetime.now(kst)
    date_str = now.strftime("%Y-%m-%d")
    start_time = f"{date_str}T00:00:00"
    end_time = f"{date_str}T23:59:59"

    config = CATEGORY_MAP[category]

    try:
        # collect_category_news 함수 직접 호출
        result = collect_category_news(
            category_ko=category,
            config=config,
            start_time=start_time,
            end_time=end_time,
            date_str=date_str
        )

        return {
            "success": result["status"] == "success",
            "category": category,
            "date": date_str,
            "saved_count": result.get("saved_count", 0),
            "elapsed_time": result.get("elapsed_time", 0),
            "status": result["status"],
            "reason": result.get("reason"),
            "message": f"{category} 카테고리 뉴스 {result.get('saved_count', 0)}개 수집 완료"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"뉴스 수집 오류: {str(e)}")


@router.get("/collect/all-categories")
def test_collect_all_categories():
    """
    전체 카테고리 뉴스 수집 테스트

    주의:
    - 본문 스크래핑으로 시간이 매우 오래 걸림 (수 분 소요)
    - DynamoDB에 실제로 저장됨
    - 운영 환경에서는 사용 금지

    Returns:
        dict: 전체 수집 결과
    """
    from app.tasks.collect_news import collect_today_news

    try:
        results = collect_today_news()

        summary = {
            "total_categories": len(CATEGORY_MAP),
            "success_count": sum(1 for r in results if r["status"] == "success"),
            "failed_count": sum(1 for r in results if r["status"] == "failed"),
            "total_saved": sum(r["saved_count"] for r in results),
            "results": [
                {
                    "category": r["category"],
                    "status": r["status"],
                    "saved_count": r.get("saved_count", 0),
                    "elapsed_time": r.get("elapsed_time", 0),
                    "reason": r.get("reason")
                }
                for r in results
            ]
        }

        return summary

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"전체 수집 오류: {str(e)}")
