"""
BigKinds API를 통한 대량 뉴스 수집 스크립트

지정 기간의 뉴스를 일별/카테고리별로 로컬 JSON 파일에 저장합니다.
클러스터링 실험용 대규모 데이터 확보 목적.

사용법:
    cd backend
    python test/scripts/bulk_collect_news.py --start 2026-04-11 --end 2026-04-11

    # 특정 카테고리만
    python test/scripts/bulk_collect_news.py --start 2026-04-11 --end 2026-04-11 --categories economy politics

출력:
    test/data/news_2026-04-11.json  (일별 JSON 파일)
"""

import os
import sys
import time
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")

from app.services.bigkinds_service import fetch_valid_articles_by_category
from app.constants.category_map import CATEGORY_MAP

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def collect_one_day_category(
    category_ko: str,
    category_en: str,
    date_str: str,
) -> dict:
    """단일 날짜 + 단일 카테고리 수집 → 메모리에 기사 리스트 반환"""
    start_time_str = f"{date_str}T00:00:00"
    end_time_str = f"{date_str}T23:59:59"
    t0 = time.time()

    try:
        articles = fetch_valid_articles_by_category(
            category=category_en,
            start_time=start_time_str,
            end_time=end_time_str,
            size=3000,
            sort="popular",
            min_content_length=300,
            limit=1500,
        )
    except Exception as e:
        logger.error(f"  [{date_str}][{category_ko}] API 실패: {e}")
        return {
            "date": date_str, "category": category_ko, "category_en": category_en,
            "status": "api_error", "fetched": 0, "saved": 0,
            "elapsed": time.time() - t0, "articles": [],
        }

    # 유효 기사만 필터
    valid = []
    skipped_short = 0
    for rank, article in enumerate(articles, start=1):
        news_id = article.get("id")
        if not news_id:
            continue
        content = article.get("content", "")
        if not content or len(content) < 300:
            skipped_short += 1
            continue
        valid.append({
            "news_id": news_id,
            "rank": rank,
            "title": article.get("title"),
            "images": article.get("images", []),
            "provider_link_page": article.get("provider_link_page"),
            "provider": article.get("provider"),
            "byline": article.get("byline"),
            "published_at": article.get("published_at"),
            "hilight": article.get("hilight"),
            "content": content,
            "category": category_en,
            "date": date_str,
        })

    elapsed = time.time() - t0
    logger.info(
        f"  [{date_str}][{category_ko}] "
        f"API={len(articles)}, 유효={len(valid)}, 짧음={skipped_short} "
        f"({elapsed:.1f}초)"
    )

    return {
        "date": date_str, "category": category_ko, "category_en": category_en,
        "status": "ok", "fetched": len(articles), "saved": len(valid),
        "skipped_short": skipped_short, "elapsed": elapsed,
        "articles": valid,
    }


def main():
    parser = argparse.ArgumentParser(description="BigKinds 대량 뉴스 수집")
    parser.add_argument("--start", required=True, help="시작일 (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="종료일 (YYYY-MM-DD)")
    parser.add_argument("--categories", nargs="*", help="카테고리 필터 (미지정 시 전체)")
    parser.add_argument("--workers", type=int, default=5, help="병렬 스레드 수 (기본 5)")
    args = parser.parse_args()

    # 날짜 범위 생성
    start = datetime.strptime(args.start, "%Y-%m-%d")
    end = datetime.strptime(args.end, "%Y-%m-%d")
    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)

    # 카테고리 필터
    if args.categories:
        categories = {
            k: v for k, v in CATEGORY_MAP.items()
            if v["api_name"] in args.categories or k in args.categories
        }
    else:
        categories = CATEGORY_MAP

    total_tasks = len(dates) * len(categories)

    print(f"{'='*60}")
    print(f"  BigKinds 대량 뉴스 수집 (로컬 JSON 저장)")
    print(f"  기간: {args.start} ~ {args.end} ({len(dates)}일)")
    print(f"  카테고리: {list(categories.keys())} ({len(categories)}개)")
    print(f"  총 작업: {total_tasks}개 (날짜 × 카테고리)")
    print(f"  병렬: {args.workers} threads")
    print(f"  저장: {DATA_DIR}/")
    print(f"{'='*60}\n")

    if not os.getenv("BIGKINDS_ACCESS_KEY"):
        print("BIGKINDS_ACCESS_KEY 환경변수가 없습니다. .env에 추가하세요.")
        return

    total_start = time.time()
    all_results = []

    # 날짜별 순차, 카테고리는 병렬
    for date_str in dates:
        print(f"\n{'─'*40}")
        print(f"  {date_str} 수집 시작")
        print(f"{'─'*40}")

        day_start = time.time()
        day_results = []

        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {}
            for cat_ko, config in categories.items():
                future = executor.submit(
                    collect_one_day_category,
                    cat_ko, config["api_name"], date_str,
                )
                futures[future] = cat_ko

            for future in as_completed(futures):
                result = future.result()
                day_results.append(result)

        day_elapsed = time.time() - day_start
        day_saved = sum(r["saved"] for r in day_results)
        day_fetched = sum(r["fetched"] for r in day_results)
        print(f"  {date_str} 완료: API={day_fetched}, 유효={day_saved} ({day_elapsed:.1f}초)")

        # 일별 JSON 저장
        day_articles = []
        for r in day_results:
            day_articles.extend(r.get("articles", []))

        day_file = DATA_DIR / f"news_{date_str}.json"
        import json
        with open(day_file, "w", encoding="utf-8") as f:
            json.dump({
                "date": date_str,
                "total_articles": len(day_articles),
                "categories": {r["category"]: r["saved"] for r in day_results},
                "elapsed_sec": round(day_elapsed, 1),
                "articles": day_articles,
            }, f, ensure_ascii=False, indent=2)
        print(f"  저장: {day_file} ({len(day_articles)}건, {day_file.stat().st_size/1024:.0f}KB)")

        # 메모리 정리 (articles는 파일에 저장했으니 결과에서 제거)
        for r in day_results:
            r.pop("articles", None)

        all_results.extend(day_results)

    # 최종 요약
    total_elapsed = time.time() - total_start
    total_fetched = sum(r["fetched"] for r in all_results)
    total_saved = sum(r["saved"] for r in all_results)
    total_errors = sum(1 for r in all_results if r["status"] != "ok")

    print(f"\n{'='*60}")
    print(f"  수집 완료!")
    print(f"  총 소요시간: {total_elapsed:.0f}초 ({total_elapsed/60:.1f}분)")
    print(f"  API 수집: {total_fetched}건")
    print(f"  DB 저장: {total_saved}건")
    print(f"  에러: {total_errors}건")
    print(f"{'='*60}")

    # 날짜별 요약 테이블
    print(f"\n{'날짜':<12} ", end="")
    for cat_ko in categories:
        print(f"{cat_ko:>6}", end="")
    print(f"  {'합계':>6}")
    print("─" * (12 + len(categories) * 6 + 8))

    for date_str in dates:
        print(f"{date_str:<12} ", end="")
        day_total = 0
        for cat_ko in categories:
            r = next((x for x in all_results if x["date"] == date_str and x["category"] == cat_ko), None)
            count = r["saved"] if r else 0
            day_total += count
            print(f"{count:>6}", end="")
        print(f"  {day_total:>6}")


if __name__ == "__main__":
    main()
