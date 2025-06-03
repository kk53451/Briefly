# app/tasks/collect_news.py

import logging
from datetime import datetime
import pytz

from app.services.deepsearch_service import fetch_valid_articles_by_category
from app.utils.dynamo import save_news_card, get_news_card_by_id, get_news_card_by_content_url
from app.constants.category_map import CATEGORY_MAP

# 로그 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def collect_today_news():
    """
    ✅ 매일 오전 6시 자동 실행: 자정~06시 사이의 뉴스 수집 및 저장
    - CATEGORY_MAP에 정의된 카테고리별로 인기 뉴스 호출
    - 본문 길이 300자 이상인 기사만 저장
    - 본문은 selector 기반 추출 (fallback 포함)
    - 저장 시점에 본문도 함께 DynamoDB에 저장 (요약 및 TTS 생성을 위함)
    """

    # 한국시간 기준 오늘 날짜 범위 설정
    kst = pytz.timezone("Asia/Seoul")
    now = datetime.now(kst)
    date_str = now.strftime("%Y-%m-%d")
    start_time = f"{date_str}T00:00:00"
    end_time = f"{date_str}T06:00:00"

    # 전체 카테고리 순회
    for category_ko, config in CATEGORY_MAP.items():
        category_en = config["api_name"]
        section = config["section"]

        logger.info(f"📰 {category_ko} 뉴스 수집 시작 ({section})")

        # 뉴스 API 호출
        try:
            articles = fetch_valid_articles_by_category(
                category=category_en,
                start_time=start_time,
                end_time=end_time,
                size=60,                # 오버페치 후 필터링
                sort="popular",
                section=section,
                min_content_length=300,
                limit=30               # 최종 저장 수
            )
            logger.info(f"📥 {category_ko} 유효 기사 수: {len(articles)}")
        except Exception as e:
            logger.error(f"[{category_ko}] API 호출 실패: {e}")
            continue

        saved_count = 0

        # 기사 순회하며 저장
        for rank, article in enumerate(articles, start=1):
            news_id = article.get("id")
            if not news_id:
                logger.warning(f"[{category_ko}] ❌ ID 누락 → 스킵")
                continue

            # 중복 확인
            if get_news_card_by_id(news_id):
                logger.info(f"🚫 [ID중복] 뉴스 스킵: {news_id}")
                continue
            if get_news_card_by_content_url(article.get("content_url")):
                logger.info(f"🚫 [URL중복] 뉴스 스킵: {article.get('content_url')}")
                continue

            content = article.get("content", "")
            if not content or len(content) < 300:
                logger.warning(f"[{category_ko}] ⚠️ 본문 누락/부족 → 스킵: {news_id}")
                continue

            # 뉴스 저장 아이템 구성
            news_item = {
                "id": news_id,
                "sections": article.get("sections", []),
                "rank": rank,
                "title": article.get("title"),
                "title_ko": None,
                "summary": article.get("summary"),
                "summary_ko": None,
                "image_url": article.get("image_url"),
                "thumbnail_url": article.get("thumbnail_url") or article.get("thumbnail"),
                "content_url": article.get("content_url"),
                "publisher": article.get("publisher"),
                "author": article.get("author"),
                "published_at": article.get("published_at"),
                "companies": article.get("companies", []),
                "esg": article.get("esg", []),
                "content": content  # ✅ 본문 포함 (selector 기반)
            }

            # DynamoDB 저장
            try:
                save_news_card(category_en, news_item, date_str)
                saved_count += 1
                logger.info(f"✅ 저장 완료: {category_ko} #{rank} - {news_item['title']}")
            except Exception as e:
                logger.error(f"[저장 실패] {category_ko} #{rank}: {e}")

        logger.info(f"📊 {category_ko} 최종 저장 수: {saved_count}")
