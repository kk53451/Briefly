# app/tasks/collect_news.py

import logging
from datetime import datetime
import pytz
import concurrent.futures
import time

from app.services.deepsearch_service import fetch_valid_articles_by_category
from app.utils.dynamo import save_news_card, get_news_card_by_id, get_news_card_by_content_url
from app.constants.category_map import CATEGORY_MAP

# 로그 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def collect_category_news(category_ko: str, config: dict, start_time: str, end_time: str, date_str: str) -> dict:
    """
    단일 카테고리 뉴스 수집 함수 (병렬 처리용)
    """
    category_en = config["api_name"]
    section = config["section"]
    collection_start_time = time.time()
    
    try:
        logger.info(f"[{category_ko}] 뉴스 수집 시작 ({section})")

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
            logger.info(f"[{category_ko}] 유효 기사 수: {len(articles)}")
        except Exception as e:
            logger.error(f" [{category_ko}] API 호출 실패: {e}")
            return {
                "category": category_ko,
                "status": "failed",
                "reason": f"api_error: {str(e)}",
                "saved_count": 0,
                "elapsed_time": time.time() - collection_start_time
            }

        saved_count = 0

        # 기사 순회하며 저장
        for rank, article in enumerate(articles, start=1):
            news_id = article.get("id")
            if not news_id:
                logger.warning(f" [{category_ko}] ID 누락 → 스킵")
                continue

            # 중복 확인
            if get_news_card_by_id(news_id):
                logger.info(f"🚫 [{category_ko}] [ID중복] 뉴스 스킵: {news_id}")
                continue
            if get_news_card_by_content_url(article.get("content_url")):
                logger.info(f"🚫 [{category_ko}] [URL중복] 뉴스 스킵: {article.get('content_url')}")
                continue

            content = article.get("content", "")
            if not content or len(content) < 300:
                logger.warning(f" [{category_ko}] 본문 누락/부족 → 스킵: {news_id}")
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
                "content": content  #  본문 포함 (selector 기반)
            }

            # DynamoDB 저장
            try:
                save_news_card(category_en, news_item, date_str)
                saved_count += 1
                logger.info(f" [{category_ko}] 저장 완료 #{rank} - {news_item['title']}")
            except Exception as e:
                logger.error(f" [{category_ko}] 저장 실패 #{rank}: {e}")

        elapsed_time = time.time() - collection_start_time
        logger.info(f" [{category_ko}] 최종 저장 수: {saved_count} (소요시간: {elapsed_time:.1f}초)")
        
        return {
            "category": category_ko,
            "status": "success",
            "saved_count": saved_count,
            "elapsed_time": elapsed_time
        }
        
    except Exception as e:
        elapsed_time = time.time() - collection_start_time
        logger.exception(f" [{category_ko}] 예상치 못한 오류 (소요시간: {elapsed_time:.1f}초): {str(e)}")
        return {
            "category": category_ko,
            "status": "failed",
            "reason": f"exception: {str(e)}",
            "saved_count": 0,
            "elapsed_time": elapsed_time
        }

def collect_today_news():
    """
     매일 오전 6시 자동 실행: 자정~06시 사이의 뉴스 수집 및 저장 (병렬 처리)
    - CATEGORY_MAP에 정의된 카테고리별로 인기 뉴스 호출
    - 본문 길이 300자 이상인 기사만 저장
    - 본문은 selector 기반 추출 (fallback 포함)
    - 저장 시점에 본문도 함께 DynamoDB에 저장 (요약 및 TTS 생성을 위함)
    """
    total_start_time = time.time()

    # 한국시간 기준 오늘 날짜 범위 설정
    kst = pytz.timezone("Asia/Seoul")
    now = datetime.now(kst)
    date_str = now.strftime("%Y-%m-%d")
    start_time = f"{date_str}T00:00:00"
    end_time = f"{date_str}T06:00:00"

    logger.info(f" 병렬 뉴스 수집 시작: {len(CATEGORY_MAP)}개 카테고리 동시 처리")
    logger.info(f" 수집 범위: {start_time} ~ {end_time}")
    logger.info(f" 카테고리 목록: {list(CATEGORY_MAP.keys())}")

    # 병렬 처리: ThreadPoolExecutor 사용
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:  # 6개 카테고리 모두 동시 처리
        # 각 카테고리를 병렬로 처리하는 Future 객체 생성
        future_to_category = {
            executor.submit(collect_category_news, category_ko, config, start_time, end_time, date_str): category_ko 
            for category_ko, config in CATEGORY_MAP.items()
        }
        
        # 완료된 순서대로 결과 수집
        for future in concurrent.futures.as_completed(future_to_category):
            category_ko = future_to_category[future]
            try:
                result = future.result()
                results.append(result)
                
                if result["status"] == "success":
                    logger.info(f" [{result['category']}] 뉴스 수집 완료 - 저장: {result['saved_count']}개, 소요시간: {result['elapsed_time']:.1f}초")
                else:
                    logger.warning(f" [{result['category']}] 뉴스 수집 실패 - 사유: {result['reason']}")
                    
            except Exception as exc:
                logger.exception(f" [{category_ko}] 예상치 못한 오류: {exc}")
                results.append({
                    "category": category_ko, 
                    "status": "failed", 
                    "reason": f"executor_exception: {str(exc)}",
                    "saved_count": 0
                })

    # 전체 결과 요약
    total_elapsed_time = time.time() - total_start_time
    success_count = sum(1 for r in results if r["status"] == "success")
    failed_count = sum(1 for r in results if r["status"] == "failed")
    total_saved = sum(r["saved_count"] for r in results)
    
    logger.info(f" 병렬 뉴스 수집 완료!")
    logger.info(f" 총 소요시간: {total_elapsed_time:.1f}초")
    logger.info(f" 결과 요약: 성공 {success_count}개, 실패 {failed_count}개")
    logger.info(f"💾 총 저장된 뉴스: {total_saved}개")
    
    # 각 카테고리별 상세 결과 로그
    for result in results:
        status_emoji = {"success": "", "failed": ""}.get(result["status"], "❓") 
        logger.info(f"{status_emoji} {result['category']}: {result['saved_count']}개 저장")
        if "reason" in result:
            logger.info(f"   └─ 사유: {result['reason']}")

    return results
