# app/tasks/generate_headlines.py

"""
오늘의 브리핑 헤드라인 생성 태스크

클러스터링 결과를 기반으로 카테고리별 상위 6개 헤드라인을 추출하고,
GPT를 사용하여 헤드라인과 요약을 생성합니다.
"""

import logging
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any

from app.utils.date import get_today_kst
from app.utils.dynamo import (
    get_news_by_category_and_date,
    save_headlines,
)
from app.services.openai_service import (
    cluster_articles_with_metadata,
    generate_headline_summary,
)
from app.constants.category_map import CATEGORY_MAP

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def generate_headlines_for_category(category_ko: str, date: str) -> Dict[str, Any]:
    """
    단일 카테고리의 헤드라인 생성

    Args:
        category_ko: 한글 카테고리명 (정치, 경제 등)
        date: 날짜 (YYYY-MM-DD)

    Returns:
        dict: {
            "category": str,
            "status": "success" | "failed" | "skipped",
            "headlines_count": int,
            "elapsed_time": float,
            "reason": str (실패 시)
        }
    """
    category_en = CATEGORY_MAP[category_ko]["api_name"]
    start_time = time.time()

    try:
        logger.info(f"\n{'='*50}")
        logger.info(f"📰 [{category_en.upper()}] 헤드라인 생성 시작")
        logger.info(f"{'='*50}")

        # 1. 해당 카테고리의 오늘 기사 불러오기
        articles = get_news_by_category_and_date(category_en, date)
        logger.info(f"  [1단계] DB에서 {len(articles)}개 기사 로드")

        if len(articles) < 5:
            logger.warning(f"  ⚠️ 기사 부족 ({len(articles)}개) → 스킵")
            return {
                "category": category_en,
                "status": "skipped",
                "reason": "insufficient_articles",
                "elapsed_time": time.time() - start_time
            }

        # 2. 클러스터링 수행 (메타데이터 포함)
        logger.info(f"  [2단계] 클러스터링 수행 중...")

        # 기사를 클러스터링에 적합한 형태로 변환
        articles_for_clustering = []
        for article in articles:
            # 클러스터링에 사용할 텍스트: title + hilight/content
            text_for_embedding = (
                article.get("title", "") + " " +
                (article.get("hilight", "") or article.get("content", "")[:500])
            )
            articles_for_clustering.append({
                "id": article.get("news_id"),
                "title": article.get("title", ""),
                "hilight": article.get("hilight", ""),
                "content": article.get("content", ""),
                "text_for_embedding": text_for_embedding,
                "provider_link_page": article.get("provider_link_page", ""),
                "images": article.get("images", ""),
                "provider": article.get("provider", ""),
                "published_at": article.get("published_at", "")
            })

        # 클러스터링 실행
        # threshold=0.7 선택 근거 (2025-12-02 실험 결과):
        # - G-Eval Coherence 1위 (4.65/5.0): 같은 사건 기사를 가장 잘 묶음
        # - G-Eval Separation 1위 (4.92/5.0): 다른 이슈와 명확히 구분
        # - Giant Cluster 45%: 과도한 병합 방지
        # - 참고: backend/test/results/geval_results_2025-11-30.json
        representative_articles, cluster_metadata = cluster_articles_with_metadata(
            articles_for_clustering,
            threshold=0.7
        )

        logger.info(f"  - 클러스터 개수: {len(cluster_metadata)}개")
        logger.info(f"  - 상위 6개 클러스터 크기: {[c['size'] for c in cluster_metadata[:6]]}")

        # 3. 상위 6개 클러스터에 대해 헤드라인/요약 생성
        logger.info(f"  [3단계] GPT로 헤드라인/요약 생성 중...")

        top_clusters = cluster_metadata[:6]  # 상위 6개만
        headlines = []

        for idx, cluster in enumerate(top_clusters):
            cluster_articles = cluster.get("member_articles", [])
            representative = cluster.get("representative_article", {})

            # GPT로 헤드라인/요약 생성
            result = generate_headline_summary(cluster_articles)

            headline_item = {
                "headline_id": str(uuid.uuid4()),
                "title": result.get("headline", representative.get("title", "")[:30]),
                "summary": result.get("summary", "관련 뉴스를 확인해보세요."),
                "cluster_size": cluster.get("size", 1),
                "representative_news_id": cluster.get("representative_id", ""),
                "news_ids": cluster.get("member_ids", [])
            }

            headlines.append(headline_item)
            logger.info(f"    #{idx+1}: {headline_item['title'][:25]}... (크기: {headline_item['cluster_size']})")

        # 4. DynamoDB에 저장
        logger.info(f"  [4단계] DynamoDB 저장 중...")
        save_headlines(category_en, date, headlines)

        elapsed_time = time.time() - start_time
        logger.info(f"\n✅ [{category_en.upper()}] 헤드라인 생성 완료")
        logger.info(f"  - 생성된 헤드라인: {len(headlines)}개")
        logger.info(f"  - 소요시간: {elapsed_time:.1f}초")

        return {
            "category": category_en,
            "status": "success",
            "headlines_count": len(headlines),
            "elapsed_time": elapsed_time
        }

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.exception(f"❌ [{category_en.upper()}] 헤드라인 생성 실패: {e}")
        return {
            "category": category_en,
            "status": "failed",
            "reason": str(e),
            "elapsed_time": elapsed_time
        }


def generate_all_headlines():
    """
    모든 카테고리의 헤드라인 생성 (순차 처리)

    Returns:
        list: 각 카테고리별 처리 결과
    """
    date = get_today_kst()
    all_categories = list(CATEGORY_MAP.keys())
    total_start_time = time.time()

    logger.info(f"\n{'='*70}")
    logger.info(f"🎯 오늘의 브리핑 헤드라인 생성 시작")
    logger.info(f"{'='*70}")
    logger.info(f"날짜: {date}")
    logger.info(f"카테고리: {len(all_categories)}개")

    results = []
    for category_ko in all_categories:
        result = generate_headlines_for_category(category_ko, date)
        results.append(result)

    # 결과 요약
    total_elapsed_time = time.time() - total_start_time
    success_count = sum(1 for r in results if r["status"] == "success")
    failed_count = sum(1 for r in results if r["status"] == "failed")
    skipped_count = sum(1 for r in results if r["status"] == "skipped")

    logger.info(f"\n{'='*70}")
    logger.info(f"✅ 헤드라인 생성 완료")
    logger.info(f"{'='*70}")
    logger.info(f"총 소요시간: {total_elapsed_time:.1f}초")
    logger.info(f"결과: 성공 {success_count}개, 실패 {failed_count}개, 스킵 {skipped_count}개")

    return results
