# app/services/bigkinds_service.py

import os
import httpx
from typing import List, Literal
from datetime import datetime, timedelta
import logging

# content_scraper.py의 본문 추출 함수 사용
from app.services.content_scraper import (
    extract_content_flexibly,
    is_korean_text
)
from app.utils.dynamo import get_news_card_by_id, get_news_card_by_content_url
from app.constants.category_map import CATEGORY_MAP

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 환경 변수에서 BigKinds API 키 로드
BIGKINDS_ACCESS_KEY = os.getenv("BIGKINDS_ACCESS_KEY")
BIGKINDS_BASE_URL = "https://tools.kinds.or.kr"
BIGKINDS_SEARCH_ENDPOINT = f"{BIGKINDS_BASE_URL}/search/news"

USER_AGENT = os.getenv(
    "USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
)

def fetch_bigkinds_news(
    category_ko: str,
    date_from: str,
    date_until: str,
    size: int = 30,
    sort_by: Literal["date", "relation"] = "relation",  # 기본값: 정확도 순
    sort_order: Literal["asc", "desc"] = "desc"
) -> List[dict]:
    """
    BigKinds API로 뉴스 검색

    Args:
        category_ko (str): 한글 카테고리명 (예: "정치", "경제")
        date_from (str): 검색 시작일 (YYYY-MM-DD)
        date_until (str): 검색 종료일 (YYYY-MM-DD)
        size (int): 가져올 뉴스 개수 (기본 30, 최대 10,000)
        sort_by (str): 정렬 기준 ("date" 또는 "relation")
        sort_order (str): 정렬 순서 ("asc" 또는 "desc")

    Returns:
        List[dict]: BigKinds API 응답 (documents 배열)
    """
    if not BIGKINDS_ACCESS_KEY:
        raise ValueError("BIGKINDS_ACCESS_KEY 환경변수가 설정되지 않았습니다.")

    # 카테고리 정보 가져오기
    category_info = CATEGORY_MAP.get(category_ko)
    if not category_info:
        raise ValueError(f"지원하지 않는 카테고리: {category_ko}")

    bigkinds_category = category_info["bigkinds_name"]

    # BigKinds API 요청 페이로드
    payload = {
        "access_key": BIGKINDS_ACCESS_KEY,
        "argument": {
            "query": "",  # 빈 문자열 = 카테고리 내 모든 기사
            "published_at": {
                "from": date_from,
                "until": date_until
            },
            "category": [bigkinds_category],
            "category_incident": [],
            "byline": "",
            "provider": [],
            "provider_subject": [],
            "sort": {sort_by: sort_order},
            "hilight": 200,
            "return_from": 0,
            "return_size": min(size, 10000),  # 최대 10,000개 제한
            "fields": [
                "news_id",
                "title",
                "content",
                "published_at",
                "provider",
                "category",
                "byline",
                "images",
                "provider_link_page",
                "provider_news_id"
            ]
        }
    }

    try:
        logger.info(f"📡 [BigKinds API] 요청 시작 - 카테고리: {bigkinds_category}, 기간: {date_from}~{date_until}, 개수: {size}")

        response = httpx.post(
            BIGKINDS_SEARCH_ENDPOINT,
            json=payload,
            headers={
                "Content-Type": "application/json; charset=UTF-8",
                "User-Agent": USER_AGENT
            },
            timeout=30.0
        )
        response.raise_for_status()

        result = response.json()
        documents = result.get("return_object", {}).get("documents", [])

        logger.info(f"✅ [BigKinds API] 응답 성공 - 반환: {len(documents)}건")

        return documents

    except httpx.TimeoutException as e:
        logger.error(f"❌ [BigKinds API] 타임아웃: {e}")
        raise Exception(f"BigKinds API 타임아웃: {e}")
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ [BigKinds API] HTTP 오류 {e.response.status_code}: {e.response.text}")
        raise Exception(f"BigKinds API HTTP 오류: {e.response.status_code}")
    except Exception as e:
        logger.error(f"❌ [BigKinds API] 예상치 못한 오류: {e}")
        raise Exception(f"BigKinds API 오류: {e}")


def map_bigkinds_to_article(bk_doc: dict, category_en: str, rank: int = 1) -> dict:
    """
    BigKinds 응답 데이터를 article 형식으로 변환 (BigKinds 필드명 기준)

    Args:
        bk_doc (dict): BigKinds API의 단일 document
        category_en (str): 영문 카테고리명 (예: "politics")
        rank (int): 순위 (enumerate에서 계산된 값)

    Returns:
        dict: BigKinds 필드명을 사용하는 article 형식
    """
    # 이미지 처리: 배열 그대로 저장 (유효한 이미지만 필터링)
    images = bk_doc.get("images", [])
    # "/" 및 빈 문자열 제거
    valid_images = [img for img in images if img and img.strip() and img != "/"]

    return {
        "id": bk_doc.get("news_id"),
        "title": bk_doc.get("title"),
        "provider_link_page": bk_doc.get("provider_link_page"),
        "provider": bk_doc.get("provider"),
        "byline": bk_doc.get("byline", ""),
        "published_at": bk_doc.get("published_at"),
        "images": valid_images,  # 배열로 저장
        "hilight": bk_doc.get("hilight"),
        "rank": rank,
    }


def fetch_valid_articles_by_category(
    category: str,
    start_time: str,
    end_time: str,
    size: int = 60,
    limit: int = 30,
    sort: Literal["popular", "traffic"] = "popular",
    min_content_length: int = 300,
    max_try: int = 5
) -> List[dict]:
    """
    BigKinds API로 카테고리별 뉴스 중 본문이 유효한 기사만 필터링하여 반환

    Args:
        category (str): 영문 카테고리명 (예: "politics")
        start_time (str): 검색 시작 시간 (YYYY-MM-DDTHH:MM:SS)
        end_time (str): 검색 종료 시간 (YYYY-MM-DDTHH:MM:SS)
        size (int): 오버페치할 기사 수 (기본 60)
        limit (int): 최종 반환할 기사 수 (기본 30)
        sort (str): 정렬 기준 (레거시 파라미터, 현재는 무시됨)
        min_content_length (int): 최소 본문 길이 (기본 300자)
        max_try (int): 최대 재시도 횟수 (레거시 파라미터)

    Returns:
        List[dict]: 본문이 포함된 유효한 기사 리스트
    """
    # 영문 카테고리 → 한글 카테고리 변환
    from app.constants.category_map import REVERSE_CATEGORY_MAP
    category_ko = REVERSE_CATEGORY_MAP.get(category)

    if not category_ko:
        raise ValueError(f"지원하지 않는 영문 카테고리: {category}")

    # 시간 포맷 변환: YYYY-MM-DDTHH:MM:SS → YYYY-MM-DD
    # BigKinds API의 until은 해당 날짜를 제외하므로 +1일 필요
    date_from = start_time.split("T")[0]
    date_obj = datetime.strptime(date_from, "%Y-%m-%d")
    date_until = (date_obj + timedelta(days=1)).strftime("%Y-%m-%d")

    # 중복 방지용 Set
    seen_ids = set()
    seen_urls = set()
    seen_titles = set()
    results = []

    # BigKinds API는 페이지네이션이 return_from/return_size로 처리됨
    # 여기서는 단순하게 size개를 한 번에 가져온 후 필터링
    try:
        documents = fetch_bigkinds_news(
            category_ko=category_ko,
            date_from=date_from,
            date_until=date_until,
            size=size,
            sort_by="relation",  # 정확도 순 (관련도 높은 순)
            sort_order="desc"
        )

        category_en = CATEGORY_MAP[category_ko]["api_name"]

        for rank, bk_doc in enumerate(documents, start=1):
            # 기사 매핑
            article = map_bigkinds_to_article(bk_doc, category_en, rank)

            news_id = article.get("id")
            article_url = article.get("provider_link_page")
            title = article.get("title", "").strip()

            # 1. 메모리 기준 중복 필터
            if not article_url or not news_id:
                continue
            if news_id in seen_ids or article_url in seen_urls:
                continue
            if title and title in seen_titles:
                continue

            # 2. DB 기준 중복 필터
            if get_news_card_by_id(news_id):
                continue
            if get_news_card_by_content_url(article_url):
                continue

            seen_ids.add(news_id)
            seen_urls.add(article_url)
            if title:
                seen_titles.add(title)

            # 3. 본문 추출 및 유효성 필터 (content_scraper.py의 함수 사용)
            content = extract_content_flexibly(article_url)
            if not content or len(content) < min_content_length:
                logger.warning(f"⚠️ [본문 부족] {news_id} - 길이: {len(content) if content else 0}자")
                continue
            if not is_korean_text(content, threshold=0.7):
                logger.warning(f"⚠️ [한글 비율 미달] {news_id}")
                continue

            article["content"] = content
            results.append(article)

            # 10개마다 진행 상황 표시
            if len(results) % 10 == 0:
                logger.info(f"  └─ [{category_ko}] {len(results)}개 수집 중...")

            if len(results) >= limit:
                break

        logger.info(f"📊 [{category_ko}] API 수집 완료: {len(results)}/{len(documents)}건 유효")
        return results[:limit]

    except Exception as e:
        logger.error(f"❌ [fetch_valid_articles_by_category] {category_ko} 오류: {e}")
        raise