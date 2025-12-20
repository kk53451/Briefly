#!/usr/bin/env python
"""
로컬 팟캐스트 생성 스크립트

podcastfy를 사용하여 대화형 팟캐스트를 생성하고 AWS에 업로드합니다.
Lambda에서 실행할 수 없는 podcastfy를 로컬에서 실행합니다.

사용법:
    python run_local.py                    # 모든 카테고리 처리
    python run_local.py --category economy # 특정 카테고리만 처리
    python run_local.py --test             # 테스트 모드 (짧은 콘텐츠)
"""

import os
import sys
import argparse
import logging
from datetime import datetime

# 환경변수 설정 (dotenv 사용)
from dotenv import load_dotenv
load_dotenv()

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.date import get_today_kst
from app.utils.dynamo import (
    get_news_by_category_and_date,
    get_frequency_by_category_and_date,
    save_frequency_summary,
)
from app.utils.s3 import upload_audio_to_s3_presigned
from app.services.podcast_service import PodcastService
from app.services.content_scraper import extract_content_flexibly
from app.constants.category_map import CATEGORY_MAP

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def process_category(category_ko: str, date: str, test_mode: bool = False) -> dict:
    """
    단일 카테고리 팟캐스트 생성
    """
    category_en = CATEGORY_MAP[category_ko]["api_name"]
    freq_id = f"{category_en}#{date}"

    logger.info(f"\n{'='*60}")
    logger.info(f"🎙️ [{category_en.upper()}] 팟캐스트 생성 시작")
    logger.info(f"{'='*60}")

    # 이미 생성된 경우 스킵
    existing = get_frequency_by_category_and_date(category_en, date)
    if existing and not test_mode:
        logger.info(f"⏭️ 이미 생성됨 → 스킵")
        return {"category": category_en, "status": "skipped", "reason": "already_exists"}

    # 뉴스 가져오기
    logger.info(f"[1] 뉴스 조회 중...")
    articles = get_news_by_category_and_date(category_en, date)
    logger.info(f"    - 조회된 기사: {len(articles)}개")

    if len(articles) < 3:
        logger.warning(f"❌ 기사 부족 ({len(articles)}개)")
        return {"category": category_en, "status": "failed", "reason": "insufficient_articles"}

    # 본문 수집 (테스트 모드면 3개만)
    max_articles = 3 if test_mode else 20
    contents = []

    for article in articles[:max_articles * 2]:  # 여유있게 조회
        if len(contents) >= max_articles:
            break

        content = article.get("content", "").strip()
        if len(content) < 200:
            url = article.get("provider_link_page")
            if url:
                try:
                    content = extract_content_flexibly(url)
                except:
                    continue

        if content and len(content) >= 200:
            # 토큰 절약을 위해 1000자로 제한
            contents.append(content[:1000])

    logger.info(f"    - 유효 본문: {len(contents)}개")

    if len(contents) < 3:
        logger.warning(f"❌ 유효 본문 부족")
        return {"category": category_en, "status": "failed", "reason": "insufficient_content"}

    # Podcastfy로 팟캐스트 생성
    logger.info(f"[2] 팟캐스트 생성 중... (약 2-3분 소요)")
    news_content = "\n\n---\n\n".join(contents)

    try:
        podcast_service = PodcastService()
        audio_file = podcast_service.generate_news_podcast(news_content, category_en)
        logger.info(f"    ✅ 오디오 생성 완료: {audio_file}")
    except Exception as e:
        logger.error(f"❌ 팟캐스트 생성 실패: {e}")
        return {"category": category_en, "status": "failed", "reason": str(e)}

    # S3 업로드
    logger.info(f"[3] S3 업로드 중...")
    try:
        with open(audio_file, 'rb') as f:
            audio_bytes = f.read()

        audio_url = upload_audio_to_s3_presigned(
            file_bytes=audio_bytes,
            user_id="shared",
            category=category_en,
            date=date,
            expires_in_seconds=604800  # 7일
        )
        logger.info(f"    ✅ S3 업로드 완료")
    except Exception as e:
        logger.error(f"❌ S3 업로드 실패: {e}")
        return {"category": category_en, "status": "failed", "reason": str(e)}

    # DynamoDB 저장
    logger.info(f"[4] DynamoDB 저장 중...")
    try:
        item = {
            "frequency_id": freq_id,
            "category": category_en,
            "date": date,
            "script": f"[대화형 팟캐스트] {len(contents)}개 기사 기반",
            "audio_url": audio_url,
            "format": "conversation",
            "created_at": datetime.utcnow().isoformat()
        }
        save_frequency_summary(item)
        logger.info(f"    ✅ 저장 완료: {freq_id}")
    except Exception as e:
        logger.error(f"❌ DynamoDB 저장 실패: {e}")
        return {"category": category_en, "status": "failed", "reason": str(e)}

    logger.info(f"\n✅ [{category_en.upper()}] 완료!")
    return {
        "category": category_en,
        "status": "success",
        "audio_url": audio_url
    }


def main():
    parser = argparse.ArgumentParser(description='로컬 팟캐스트 생성')
    parser.add_argument('--category', '-c', type=str, help='특정 카테고리만 처리 (예: economy, politics)')
    parser.add_argument('--date', '-d', type=str, help='날짜 지정 (예: 2025-12-03)')
    parser.add_argument('--test', '-t', action='store_true', help='테스트 모드 (적은 기사로 빠르게 테스트)')
    args = parser.parse_args()

    date = args.date or get_today_kst()
    test_mode = args.test

    logger.info(f"🚀 로컬 팟캐스트 생성 시작")
    logger.info(f"   날짜: {date}")
    logger.info(f"   테스트 모드: {test_mode}")

    # 처리할 카테고리 결정
    if args.category:
        # 영문 카테고리명을 한글로 변환
        category_ko = None
        for ko, info in CATEGORY_MAP.items():
            if info["api_name"] == args.category:
                category_ko = ko
                break

        if not category_ko:
            logger.error(f"❌ 알 수 없는 카테고리: {args.category}")
            logger.info(f"   사용 가능: {[v['api_name'] for v in CATEGORY_MAP.values()]}")
            sys.exit(1)

        categories = [category_ko]
    else:
        categories = list(CATEGORY_MAP.keys())

    logger.info(f"   카테고리: {len(categories)}개")

    # 각 카테고리 처리
    results = []
    for category_ko in categories:
        result = process_category(category_ko, date, test_mode)
        results.append(result)

    # 결과 요약
    success = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "failed")
    skipped = sum(1 for r in results if r["status"] == "skipped")

    logger.info(f"\n{'='*60}")
    logger.info(f"📊 결과 요약")
    logger.info(f"{'='*60}")
    logger.info(f"   성공: {success}개")
    logger.info(f"   실패: {failed}개")
    logger.info(f"   스킵: {skipped}개")

    for r in results:
        status_emoji = {"success": "✅", "failed": "❌", "skipped": "⏭️"}.get(r["status"], "❓")
        logger.info(f"   {status_emoji} {r['category']}: {r['status']}")


if __name__ == "__main__":
    main()
