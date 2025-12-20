# backend/test/scripts/collect_local_news.py

"""
로컬 뉴스 데이터 수집 스크립트 (필터 없음)

목적: 필터 없이 24시간치 뉴스 데이터를 로컬에 수집하여
     클러스터링 및 요약 실험을 위한 데이터셋 구축

사용법:
    cd backend
    python -m test.scripts.collect_local_news

    또는
    python test/scripts/collect_local_news.py
"""

import os
import sys
import json
import time
import re
import httpx
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

from bs4 import BeautifulSoup

# ============================================================
# 설정
# ============================================================

# 수집 기간 (24시간)
DATE_FROM = "2025-11-30"
DATE_UNTIL = "2025-12-01"

# API 설정
API_SIZE_PER_CATEGORY = 5000  # 카테고리당 API 요청량
MAX_WORKERS = 8  # 병렬 처리 스레드 수

# 저장 경로
OUTPUT_DIR = Path(__file__).parent.parent / "data"
OUTPUT_FILE = OUTPUT_DIR / f"news_raw_{DATE_FROM}.jsonl"

# BigKinds API 설정
BIGKINDS_ACCESS_KEY = os.getenv("BIGKINDS_ACCESS_KEY")
BIGKINDS_SEARCH_ENDPOINT = "https://tools.kinds.or.kr/search/news"

USER_AGENT = os.getenv(
    "USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
)

# 카테고리 매핑 (한글 -> BigKinds API명)
CATEGORIES = {
    "정치": "정치",
    "경제": "경제",
    "사회": "사회",
    "문화": "문화",
    "국제": "국제",
    "지역": "지역",
    "스포츠": "스포츠",
    "IT/과학": "IT_과학"
}

# 영문 카테고리명 매핑
CATEGORY_EN = {
    "정치": "politics",
    "경제": "economy",
    "사회": "society",
    "문화": "culture",
    "국제": "international",
    "지역": "local",
    "스포츠": "sports",
    "IT/과학": "tech"
}

# ============================================================
# 스크래핑 유틸리티 (필터 없음 버전)
# ============================================================

# 주요 언론사별 도메인/본문 selector
ARTICLE_SELECTORS = {
    "newsis.com": "div.view_text",
    "news1.kr": "div#articleBody",
    "yna.co.kr": "div#articleBody, div#articleView",
    "heraldcorp.com": "div.view_con_t",
    "biz.heraldcorp.com": "div.view_con_t",
    "kbs.co.kr": "div#cont_newstext",
    "sisajournal.com": "div.view_con",
    "asiatoday.co.kr": "div#articleBody",
    "koreaherald.com": "div.article-text",
    "sedaily.com": "div#v_article",
    "donga.com": "div.article_txt",
    "hankyung.com": "div#articletxt",
    "joongang.co.kr": "div#article_body",
    "ohmynews.com": "div#article_view",
    "pressian.com": "div.view_con_tx",
    "mt.co.kr": "div#textBody",
    "edaily.co.kr": "div.news_body",
    "mk.co.kr": "div#article_body",
    "fnnews.com": "div.articleCont",
    "busan.com": "div#news_body_area",
}

# 불필요한 영역 selector (제거용)
KNOWN_TRASH_SELECTORS = [
    ".txt-copyright", ".adrs", ".sns-box", ".relate_news", ".copy",
    ".recommend", ".app-down", ".guide", ".comment", ".news_app_banner",
    ".article-ad", "#recommend", "#comment", "#reply", ".promotion"
]


def calculate_korean_ratio(text: str) -> float:
    """텍스트 내 한글 비율 계산"""
    if not text:
        return 0.0
    kor_count = len(re.findall(r"[가-힣]", text))
    total_count = len(re.findall(r"[가-힣a-zA-Z]", text))
    if total_count == 0:
        return 0.0
    return round(kor_count / total_count, 4)


def scrape_content_raw(url: str, timeout: float = 10.0) -> str:
    """
    본문 스크래핑 (필터 없음)
    - 300자 미만, 한글 비율 체크 없이 그대로 반환
    - 스크래핑 실패 시 빈 문자열 반환
    """
    try:
        response = httpx.get(
            url,
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT}
        )
        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        # 불필요한 태그 제거
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        for selector in KNOWN_TRASH_SELECTORS:
            for tag in soup.select(selector):
                tag.decompose()

        # 도메인별 selector 사용
        domain = urlparse(url).netloc.replace("www.", "")
        selector = ARTICLE_SELECTORS.get(domain)

        if selector:
            article_tag = soup.select_one(selector)
            if article_tag:
                text = article_tag.get_text(separator="\n")
            else:
                text = soup.get_text(separator="\n")
        else:
            text = soup.get_text(separator="\n")

        # 기본 정리만 수행 (빈 줄 제거)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

    except Exception as e:
        return ""


# ============================================================
# BigKinds API 호출
# ============================================================

def fetch_bigkinds_news(category_ko: str, date_from: str, date_until: str, size: int) -> list:
    """BigKinds API로 뉴스 메타데이터 가져오기"""
    if not BIGKINDS_ACCESS_KEY:
        raise ValueError("BIGKINDS_ACCESS_KEY 환경변수가 설정되지 않았습니다.")

    bigkinds_category = CATEGORIES[category_ko]

    payload = {
        "access_key": BIGKINDS_ACCESS_KEY,
        "argument": {
            "query": "",
            "published_at": {
                "from": date_from,
                "until": date_until
            },
            "category": [bigkinds_category],
            "category_incident": [],
            "byline": "",
            "provider": [],
            "provider_subject": [],
            "sort": {"date": "desc"},
            "hilight": 200,
            "return_from": 0,
            "return_size": min(size, 10000),
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
        response = httpx.post(
            BIGKINDS_SEARCH_ENDPOINT,
            json=payload,
            headers={
                "Content-Type": "application/json; charset=UTF-8",
                "User-Agent": USER_AGENT
            },
            timeout=60.0
        )
        response.raise_for_status()
        result = response.json()
        documents = result.get("return_object", {}).get("documents", [])
        return documents

    except Exception as e:
        print(f"[ERROR] BigKinds API - {category_ko}: {e}")
        return []


# ============================================================
# 기사 처리
# ============================================================

def process_article(bk_doc: dict, category_ko: str) -> dict | None:
    """
    단일 기사 처리: 스크래핑 후 데이터 구조화
    필터 없이 스크래핑 성공한 기사만 반환
    """
    news_id = bk_doc.get("news_id")
    url = bk_doc.get("provider_link_page")

    if not news_id or not url:
        return None

    # 본문 스크래핑 (필터 없음)
    content = scrape_content_raw(url)

    # 스크래핑 실패 시 스킵
    if not content:
        return None

    # 이미지 처리
    images = bk_doc.get("images", [])
    if isinstance(images, str):
        images = [images] if images and images.strip() else []
    elif not isinstance(images, list):
        images = []
    valid_images = [img for img in images if img and img.strip() and img != "/"]

    return {
        "id": news_id,
        "category": CATEGORY_EN[category_ko],
        "title": bk_doc.get("title", ""),
        "content": content,
        "content_length": len(content),
        "korean_ratio": calculate_korean_ratio(content),
        "provider": bk_doc.get("provider", ""),
        "byline": bk_doc.get("byline", ""),
        "published_at": bk_doc.get("published_at", ""),
        "url": url,
        "images": valid_images,
        "hilight": bk_doc.get("hilight", "")
    }


def collect_category(category_ko: str) -> dict:
    """카테고리별 수집"""
    start_time = time.time()
    print(f"\n{'='*60}", flush=True)
    print(f"[{category_ko}] Collecting...", flush=True)

    # 1. API 호출
    documents = fetch_bigkinds_news(
        category_ko=category_ko,
        date_from=DATE_FROM,
        date_until=DATE_UNTIL,
        size=API_SIZE_PER_CATEGORY
    )
    print(f"   API response: {len(documents)} articles", flush=True)

    if not documents:
        return {
            "category": category_ko,
            "api_count": 0,
            "scraped_count": 0,
            "elapsed_time": time.time() - start_time
        }

    # 2. 중복 제거 (메모리 기준)
    seen_ids = set()
    seen_urls = set()
    seen_titles = set()
    unique_docs = []

    for doc in documents:
        news_id = doc.get("news_id")
        url = doc.get("provider_link_page")
        title = doc.get("title", "").strip()

        if not news_id or not url:
            continue
        if news_id in seen_ids or url in seen_urls:
            continue
        if title and title in seen_titles:
            continue

        seen_ids.add(news_id)
        seen_urls.add(url)
        if title:
            seen_titles.add(title)
        unique_docs.append(doc)

    print(f"   After dedup: {len(unique_docs)} articles", flush=True)

    # 3. 병렬 스크래핑
    results = []
    failed_count = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(process_article, doc, category_ko): doc
            for doc in unique_docs
        }

        for i, future in enumerate(as_completed(futures), 1):
            try:
                result = future.result()
                if result:
                    results.append(result)
                else:
                    failed_count += 1
            except Exception as e:
                failed_count += 1

            # 진행률 표시 (500개마다)
            if i % 500 == 0:
                print(f"   Progress: {i}/{len(unique_docs)} (success: {len(results)}, failed: {failed_count})", flush=True)

    elapsed = time.time() - start_time
    print(f"[{category_ko}] Done: {len(results)} scraped ({elapsed:.1f}s)", flush=True)

    return {
        "category": category_ko,
        "api_count": len(documents),
        "unique_count": len(unique_docs),
        "scraped_count": len(results),
        "failed_count": failed_count,
        "elapsed_time": elapsed,
        "articles": results
    }


# ============================================================
# 메인 실행
# ============================================================

def main():
    total_start = time.time()

    print("=" * 60, flush=True)
    print("Local News Data Collection (No Filter)", flush=True)
    print("=" * 60, flush=True)
    print(f"Period: {DATE_FROM} ~ {DATE_UNTIL}", flush=True)
    print(f"Categories: {len(CATEGORIES)}", flush=True)
    print(f"API request: {API_SIZE_PER_CATEGORY}/category", flush=True)
    print(f"Parallel workers: {MAX_WORKERS}", flush=True)
    print(f"Output: {OUTPUT_FILE}", flush=True)
    print("=" * 60, flush=True)

    # 출력 디렉토리 생성
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 전체 통계
    total_api = 0
    total_scraped = 0
    all_articles = []

    # 카테고리별 수집
    for category_ko in CATEGORIES.keys():
        result = collect_category(category_ko)
        total_api += result.get("api_count", 0)
        total_scraped += result.get("scraped_count", 0)

        if "articles" in result:
            all_articles.extend(result["articles"])

    # JSONL 파일로 저장
    print(f"\n{'='*60}")
    print(f"Saving to file...")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for article in all_articles:
            f.write(json.dumps(article, ensure_ascii=False) + "\n")

    total_elapsed = time.time() - total_start
    file_size_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)

    print("=" * 60)
    print("Collection Complete!")
    print("=" * 60)
    print(f"API total: {total_api:,} articles")
    print(f"Scraped: {total_scraped:,} articles")
    print(f"Success rate: {total_scraped/total_api*100:.1f}%" if total_api > 0 else "N/A")
    print(f"Total time: {total_elapsed/60:.1f} min")
    print(f"File size: {file_size_mb:.1f} MB")
    print(f"Output: {OUTPUT_FILE}")
    print("=" * 60)

    # 카테고리별 통계 요약
    print("\nCategory Statistics:")
    print("-" * 40)

    category_stats = {}
    for article in all_articles:
        cat = article["category"]
        if cat not in category_stats:
            category_stats[cat] = {"count": 0, "total_length": 0, "korean_ratios": []}
        category_stats[cat]["count"] += 1
        category_stats[cat]["total_length"] += article["content_length"]
        category_stats[cat]["korean_ratios"].append(article["korean_ratio"])

    for cat, stats in sorted(category_stats.items()):
        avg_length = stats["total_length"] / stats["count"] if stats["count"] > 0 else 0
        avg_korean = sum(stats["korean_ratios"]) / len(stats["korean_ratios"]) if stats["korean_ratios"] else 0
        print(f"  {cat:12s}: {stats['count']:,} articles (avg {avg_length:.0f} chars, korean {avg_korean:.1%})")


if __name__ == "__main__":
    main()
