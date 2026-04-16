"""
Naver 뉴스 스크래핑 실험 스크립트

Naver 내부 AJAX API + 상세페이지 스크래핑으로 뉴스를 수집하고
JSON 파일로 저장합니다. BigKinds 대체 가능성 검증 목적.

사용법:
    cd backend
    python test/scripts/test_naver_scraper.py

    # 특정 카테고리만
    python test/scripts/test_naver_scraper.py --categories economy politics

    # 수집 수 제한
    python test/scripts/test_naver_scraper.py --limit 20

출력:
    test/results/naver_scrape_test_{timestamp}.json
"""

import sys
import time
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

RESULTS_DIR = Path(__file__).parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# Naver 뉴스 카테고리 ID 매핑
NAVER_CATEGORIES = {
    "politics": {"id": "100", "name": "정치"},
    "economy": {"id": "101", "name": "경제"},
    "society": {"id": "102", "name": "사회"},
    "culture": {"id": "103", "name": "생활/문화"},
    "international": {"id": "104", "name": "세계"},
    "tech": {"id": "105", "name": "IT/과학"},
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://news.naver.com/",
}


# ============================================================
# 헤드라인 뉴스 수집 (에디터 큐레이션)
# ============================================================

def fetch_headline_news(sid: str) -> List[Dict]:
    """
    네이버 뉴스 헤드라인(에디터 큐레이션) 기사를 가져옵니다.
    섹션 페이지 HTML에서 .as_section_headline 영역을 파싱합니다.
    파이프라인에는 미포함, 수집만 해둡니다.

    Args:
        sid: 카테고리 ID

    Returns:
        헤드라인 기사 리스트
    """
    url = f"https://news.naver.com/section/{sid}"

    try:
        with httpx.Client(headers=HEADERS, timeout=15.0, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # 헤드라인 영역: .as_section_headline
        headline_section = soup.select_one(".section_component.as_section_headline")
        if not headline_section:
            return []

        items = headline_section.select(".sa_item")

        articles = []
        for item in items:
            title_el = item.select_one(".sa_text_strong")
            link_el = item.select_one("a.sa_text_title")
            press_el = item.select_one(".sa_text_press")
            lede_el = item.select_one(".sa_text_lede")
            img_el = item.select_one("img")

            # 관련뉴스 클러스터 수
            cluster_el = item.select_one(".sa_text_cluster")
            cluster_count = 0
            if cluster_el:
                import re
                m = re.search(r"(\d+)", cluster_el.get_text())
                if m:
                    cluster_count = int(m.group(1))

            if not title_el or not link_el:
                continue

            thumbnail = ""
            if img_el:
                thumbnail = img_el.get("data-src") or img_el.get("src") or ""

            articles.append({
                "title": title_el.get_text(strip=True),
                "link": link_el.get("href", ""),
                "press": press_el.get_text(strip=True) if press_el else "",
                "lede": lede_el.get_text(strip=True) if lede_el else "",
                "has_image": bool(thumbnail),
                "image_url": thumbnail,
                "cluster_count": cluster_count,
                "is_headline": True,
            })

        return articles

    except Exception as e:
        logger.error(f"헤드라인 API 실패 (sid={sid}): {e}")
        return []


# ============================================================
# 1단계: 기사 목록 수집 (AJAX API)
# ============================================================

def fetch_article_list(
    sid: str,
    page: int = 1,
    date: str = None,
) -> List[Dict]:
    """
    Naver 뉴스 섹션 AJAX API로 기사 목록을 가져옵니다.

    Args:
        sid: 카테고리 ID (100=정치, 101=경제, ...)
        page: 페이지 번호
        date: 날짜 필터 (YYYYMMDD 형식, None이면 오늘)

    Returns:
        기사 리스트 [{title, link, press, lede, time, has_image}, ...]
    """
    params = {
        "sid": sid,
        "sid2": "",
        "cluid": "",
        "pageNo": str(page),
        "date": date or "",
        "next": "",
        "_": str(int(time.time() * 1000)),
    }

    url = "https://news.naver.com/section/template/SECTION_ARTICLE_LIST"

    try:
        with httpx.Client(headers=HEADERS, timeout=15.0) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()

        data = resp.json()
        html = data.get("renderedComponent", {}).get("SECTION_ARTICLE_LIST", "")

        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        items = soup.select(".sa_item")

        articles = []
        for item in items:
            title_el = item.select_one(".sa_text_strong")
            link_el = item.select_one("a.sa_text_title")
            press_el = item.select_one(".sa_text_press")
            lede_el = item.select_one(".sa_text_lede")
            time_el = item.select_one(".sa_text_datetime")
            img_el = item.select_one("img")

            if not title_el or not link_el:
                continue

            # 이미지: data-src (lazy loading) 우선, 없으면 src
            thumbnail = ""
            if img_el:
                thumbnail = img_el.get("data-src") or img_el.get("src") or ""

            articles.append({
                "title": title_el.get_text(strip=True),
                "link": link_el.get("href", ""),
                "press": press_el.get_text(strip=True) if press_el else "",
                "lede": lede_el.get_text(strip=True) if lede_el else "",
                "time": time_el.get_text(strip=True) if time_el else "",
                "has_image": bool(thumbnail),
                "image_url": thumbnail,
            })

        return articles

    except Exception as e:
        logger.error(f"기사 목록 API 실패 (sid={sid}, page={page}): {e}")
        return []


def fetch_article_list_pages(
    sid: str,
    max_pages: int = 5,
    date: str = None,
) -> List[Dict]:
    """여러 페이지의 기사 목록을 수집합니다."""
    all_articles = []
    seen_links = set()

    for page in range(1, max_pages + 1):
        articles = fetch_article_list(sid, page, date)
        if not articles:
            break

        new_count = 0
        for a in articles:
            if a["link"] not in seen_links:
                seen_links.add(a["link"])
                all_articles.append(a)
                new_count += 1

        logger.info(f"    페이지 {page}: {len(articles)}건 (신규 {new_count}건)")

        if new_count == 0:
            break  # 더 이상 새 기사 없음

        time.sleep(0.3)  # rate limit 방지

    return all_articles


# ============================================================
# 2단계: 기사 상세 페이지 스크래핑
# ============================================================

def fetch_article_detail(article_url: str) -> Optional[Dict]:
    """
    Naver 뉴스 상세 페이지에서 본문과 메타데이터를 추출합니다.

    Args:
        article_url: n.news.naver.com 기사 URL

    Returns:
        {content, journalist, published_at, category, original_link, images}
    """
    try:
        with httpx.Client(headers=HEADERS, timeout=10.0, follow_redirects=True) as client:
            resp = client.get(article_url)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # 본문 (#dic_area)
        body_el = soup.select_one("#dic_area")
        if not body_el:
            return None

        # 본문에서 불필요한 요소 제거
        for tag in body_el.select("script, style, .end_photo_org, .artical_ban"):
            tag.decompose()

        content = body_el.get_text(separator="\n", strip=True)

        # 메타데이터
        title = soup.select_one(".media_end_head_headline")
        press = soup.select_one(".media_end_head_top_logo img")
        date_el = soup.select_one(".media_end_head_info_datestamp_time")
        journalist = soup.select_one(".media_end_head_journalist_name")
        category = soup.select_one(".media_end_categorize_item")
        original_link = soup.select_one(".media_end_head_origin a")

        # 이미지 (data-src 우선 = lazy loading 대응)
        images = []
        for img in body_el.select("img"):
            src = img.get("data-src") or img.get("src")
            if src and ("pstatic.net" in src or "imgnews" in src):
                images.append(src)

        # og:image 메타태그 (대표 이미지, 본문에 없을 때 폴백)
        og_image = soup.select_one('meta[property="og:image"]')
        if og_image and og_image.get("content"):
            og_src = og_image["content"]
            if og_src not in images:
                images.insert(0, og_src)

        return {
            "content": content,
            "content_length": len(content),
            "title": title.get_text(strip=True) if title else None,
            "press": press.get("alt", "") if press else None,
            "published_at": date_el.get("data-date-time", "") if date_el else None,
            "journalist": journalist.get_text(strip=True) if journalist else None,
            "category": category.get_text(strip=True) if category else None,
            "original_link": original_link.get("href", "") if original_link else None,
            "images": images[:3],
        }

    except Exception as e:
        logger.debug(f"상세 페이지 실패: {article_url}: {e}")
        return None


# ============================================================
# 3단계: 통합 수집
# ============================================================

def collect_category(
    category_en: str,
    category_info: Dict,
    max_pages: int = 5,
    max_articles: int = 100,
    date: str = None,
    fetch_detail: bool = True,
) -> Dict:
    """카테고리 하나를 수집합니다."""
    sid = category_info["id"]
    category_ko = category_info["name"]

    logger.info(f"\n  [{category_ko}] 수집 시작 (sid={sid})")
    t0 = time.time()

    # 0단계: 헤드라인 수집 (파이프라인 미포함, 별도 저장)
    headlines = fetch_headline_news(sid)
    logger.info(f"  [{category_ko}] 헤드라인: {len(headlines)}건 (저장만, 파이프라인 미포함)")

    # 1단계: 기사 목록
    articles = fetch_article_list_pages(sid, max_pages, date)
    logger.info(f"  [{category_ko}] 목록 수집: {len(articles)}건")

    if max_articles:
        articles = articles[:max_articles]

    # 2단계: 상세 페이지 (선택)
    if fetch_detail:
        logger.info(f"  [{category_ko}] 상세 페이지 스크래핑 시작 ({len(articles)}건)...")
        success = 0
        failed = 0
        short = 0

        for i, article in enumerate(articles):
            detail = fetch_article_detail(article["link"])
            if detail:
                if detail["content_length"] >= 200:
                    article.update(detail)
                    success += 1
                else:
                    article["content"] = ""
                    article["content_length"] = 0
                    short += 1
            else:
                article["content"] = ""
                article["content_length"] = 0
                failed += 1

            if (i + 1) % 20 == 0:
                logger.info(f"    [{category_ko}] {i+1}/{len(articles)} 완료 "
                           f"(성공={success}, 짧음={short}, 실패={failed})")

            time.sleep(0.2)  # rate limit

        logger.info(f"  [{category_ko}] 상세 완료: 성공={success}, 짧음={short}, 실패={failed}")

    elapsed = time.time() - t0

    # 유효 기사만 필터
    valid_articles = [a for a in articles if a.get("content_length", 0) >= 200]

    logger.info(f"  [{category_ko}] 완료: {len(valid_articles)}/{len(articles)}건 유효 ({elapsed:.1f}초)")

    return {
        "category": category_en,
        "category_ko": category_ko,
        "total_listed": len(articles),
        "valid_articles": len(valid_articles),
        "headline_count": len(headlines),
        "elapsed_sec": round(elapsed, 1),
        "articles": valid_articles,
        "headlines": headlines,  # 별도 저장, 파이프라인 미포함
    }


def main():
    parser = argparse.ArgumentParser(description="Naver 뉴스 스크래핑 실험")
    parser.add_argument("--categories", nargs="*",
                       help="카테고리 필터 (예: economy politics)")
    parser.add_argument("--pages", type=int, default=3,
                       help="카테고리당 페이지 수 (기본 3, 페이지당 ~36건)")
    parser.add_argument("--limit", type=int, default=50,
                       help="카테고리당 최대 기사 수 (기본 50)")
    parser.add_argument("--date", default=None,
                       help="날짜 필터 YYYYMMDD (기본: 오늘)")
    parser.add_argument("--no-detail", action="store_true",
                       help="상세 페이지 스크래핑 생략 (목록만)")
    args = parser.parse_args()

    # 카테고리 선택
    if args.categories:
        categories = {k: v for k, v in NAVER_CATEGORIES.items() if k in args.categories}
    else:
        categories = NAVER_CATEGORIES

    print(f"{'='*60}")
    print(f"  Naver 뉴스 스크래핑 실험")
    print(f"  카테고리: {[v['name'] for v in categories.values()]}")
    print(f"  페이지: {args.pages}, 기사 제한: {args.limit}")
    print(f"  날짜: {args.date or '오늘'}")
    print(f"  상세 스크래핑: {'OFF' if args.no_detail else 'ON'}")
    print(f"{'='*60}")

    total_start = time.time()
    all_results = []

    for cat_en, cat_info in categories.items():
        result = collect_category(
            cat_en, cat_info,
            max_pages=args.pages,
            max_articles=args.limit,
            date=args.date,
            fetch_detail=not args.no_detail,
        )
        all_results.append(result)

    total_elapsed = time.time() - total_start

    # 요약
    print(f"\n{'='*60}")
    print(f"  수집 결과 요약")
    print(f"{'='*60}")
    print(f"{'카테고리':<12} {'목록':>6} {'유효':>6} {'시간':>8}")
    print(f"{'─'*40}")

    total_listed = 0
    total_valid = 0
    for r in all_results:
        print(f"{r['category_ko']:<12} {r['total_listed']:>6} {r['valid_articles']:>6} {r['elapsed_sec']:>7.1f}s")
        total_listed += r["total_listed"]
        total_valid += r["valid_articles"]

    print(f"{'─'*40}")
    print(f"{'합계':<12} {total_listed:>6} {total_valid:>6} {total_elapsed:>7.1f}s")

    # 샘플 기사 출력
    print(f"\n  === 샘플 기사 (카테고리당 2개) ===")
    for r in all_results:
        print(f"\n  [{r['category_ko']}]")
        for a in r["articles"][:2]:
            content_preview = a.get("content", "")[:80].replace("\n", " ")
            print(f"    제목: {a['title'][:50]}")
            print(f"    언론: {a['press']} | 시간: {a.get('published_at', a.get('time', ''))}")
            print(f"    본문: {content_preview}...")
            print(f"    링크: {a['link']}")
            print()

    # JSON 저장 (본문 포함)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = RESULTS_DIR / f"naver_scrape_test_{ts}.json"

    output = {
        "experiment_date": ts,
        "settings": {
            "pages": args.pages,
            "limit": args.limit,
            "date": args.date,
            "detail": not args.no_detail,
        },
        "summary": {
            "total_listed": total_listed,
            "total_valid": total_valid,
            "total_elapsed_sec": round(total_elapsed, 1),
            "categories": len(categories),
        },
        "results": [{k: v for k, v in r.items()} for r in all_results],
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n결과 저장: {output_file}")
    print(f"파일 크기: {output_file.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
