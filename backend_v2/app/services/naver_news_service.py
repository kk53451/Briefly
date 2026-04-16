"""
Naver 뉴스 수집 서비스

Naver 내부 AJAX API + 상세페이지 스크래핑으로 뉴스를 수집합니다.
BigKinds API 대체.

수집 경로:
  1단계: news.naver.com/section/template/SECTION_ARTICLE_LIST (기사 목록)
  2단계: n.news.naver.com/mnews/article/{oid}/{aid} (기사 상세)
"""

import re
import time
import logging
from typing import List, Dict, Optional

import httpx
from bs4 import BeautifulSoup

from app.constants.category_map import CATEGORY_MAP

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Referer": "https://news.naver.com/",
}

# 기자 바이라인 + 이메일 제거 패턴
BYLINE_PATTERN = re.compile(r"\n*[\w·\s]{2,20}기자\s*\S*@\S+\s*$")
# 저작권/무단전재 문구 제거
COPYRIGHT_PATTERN = re.compile(
    r"\n*(?:ⓒ|©|무단\s*전재|재배포\s*금지|저작권|All\s*rights?\s*reserved).*$",
    re.IGNORECASE,
)


class NaverNewsService:

    def __init__(self, request_delay: float = 0.2):
        """
        Args:
            request_delay: 요청 간 대기 시간 (초). rate limit 방지.
        """
        self.request_delay = request_delay

    # ──────────────────────────────────────────────
    # 1단계: 기사 목록 수집 (커서 기반 페이지네이션)
    # ──────────────────────────────────────────────

    def fetch_article_list_pages(
        self,
        sid: str,
        max_pages: int = 30,
        date: str = None,
    ) -> List[Dict]:
        """
        여러 페이지의 기사 목록을 커서 기반 페이지네이션으로 수집합니다.

        Naver AJAX API는 `pageNo`를 무시하고 `next` 커서 파라미터로 페이지를
        넘깁니다. 각 응답 HTML 안의 `data-cursor` 속성에서 다음 커서를 추출하여
        연결합니다.
        """
        all_articles = []
        seen_links = set()
        cursor = ""
        page_no = 1

        for _ in range(max_pages):
            articles, next_cursor, next_page = self._fetch_page_with_cursor(
                sid, page_no, date, cursor
            )
            if not articles:
                break

            new_count = 0
            for a in articles:
                if a["link"] not in seen_links:
                    seen_links.add(a["link"])
                    all_articles.append(a)
                    new_count += 1

            if new_count == 0:
                break

            # 다음 페이지를 위한 커서 업데이트
            if not next_cursor:
                break
            cursor = next_cursor
            page_no = next_page

            time.sleep(self.request_delay)

        return all_articles

    def _fetch_page_with_cursor(
        self,
        sid: str,
        page_no: int,
        date: str,
        cursor: str,
    ) -> tuple:
        """커서 기반 1페이지 수집. (articles, next_cursor, next_page_no) 반환."""
        params = {
            "sid": sid,
            "sid2": "",
            "cluid": "",
            "pageNo": str(page_no),
            "date": date or "",
            "next": cursor,
            "_": str(int(time.time() * 1000)),
        }

        try:
            with httpx.Client(headers=HEADERS, timeout=15.0) as client:
                resp = client.get(
                    "https://news.naver.com/section/template/SECTION_ARTICLE_LIST",
                    params=params,
                )
                resp.raise_for_status()

            data = resp.json()
            html = data.get("renderedComponent", {}).get("SECTION_ARTICLE_LIST", "")
            if not html:
                return [], "", 0

            soup = BeautifulSoup(html, "html.parser")
            articles = []

            for item in soup.select(".sa_item"):
                title_el = item.select_one(".sa_text_strong")
                link_el = item.select_one("a.sa_text_title")
                press_el = item.select_one(".sa_text_press")
                lede_el = item.select_one(".sa_text_lede")
                time_el = item.select_one(".sa_text_datetime")
                img_el = item.select_one("img")

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
                    "time": time_el.get_text(strip=True) if time_el else "",
                    "thumbnail": thumbnail,
                })

            # 다음 페이지 커서 추출
            cursor_el = soup.select_one("[data-cursor]")
            next_cursor = cursor_el["data-cursor"] if cursor_el else ""
            next_page = int(cursor_el.get("data-page-no", 0)) if cursor_el else 0

            return articles, next_cursor, next_page

        except Exception as e:
            logger.error(f"기사 목록 API 실패 (sid={sid}, page={page_no}): {e}")
            return [], "", 0

    # ──────────────────────────────────────────────
    # 2단계: 기사 상세 페이지 스크래핑
    # ──────────────────────────────────────────────

    def fetch_article_detail(self, article_url: str) -> Optional[Dict]:
        """
        Naver 뉴스 상세 페이지에서 본문과 메타데이터를 추출합니다.

        Returns:
            {content, content_length, published_at, journalist, images, ...}
        """
        try:
            with httpx.Client(
                headers=HEADERS, timeout=10.0, follow_redirects=True
            ) as client:
                resp = client.get(article_url)
                resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")

            # 본문
            body_el = soup.select_one("#dic_area")
            if not body_el:
                return None

            # 불필요한 요소 제거
            for tag in body_el.select("script, style, .end_photo_org, .artical_ban"):
                tag.decompose()

            content = body_el.get_text(separator="\n", strip=True)

            # 후처리: 바이라인/저작권 제거
            content = BYLINE_PATTERN.sub("", content).strip()
            content = COPYRIGHT_PATTERN.sub("", content).strip()

            # 메타데이터
            date_el = soup.select_one(
                ".media_end_head_info_datestamp_time"
            )
            journalist_el = soup.select_one(".media_end_head_journalist_name")
            original_link_el = soup.select_one(".media_end_head_origin a")

            # 이미지 (data-src 우선 = lazy loading)
            images = []
            for img in body_el.select("img"):
                src = img.get("data-src") or img.get("src")
                if src and ("pstatic.net" in src or "imgnews" in src):
                    images.append(src)

            # og:image (대표 이미지 폴백)
            og_image = soup.select_one('meta[property="og:image"]')
            if og_image and og_image.get("content"):
                og_src = og_image["content"]
                if og_src not in images:
                    images.insert(0, og_src)

            return {
                "content": content,
                "content_length": len(content),
                "published_at": (
                    date_el.get("data-date-time", "") if date_el else ""
                ),
                "journalist": (
                    journalist_el.get_text(strip=True) if journalist_el else ""
                ),
                "original_link": (
                    original_link_el.get("href", "") if original_link_el else ""
                ),
                "images": images[:5],
            }

        except Exception as e:
            logger.debug(f"상세 페이지 실패: {article_url}: {e}")
            return None

    # ──────────────────────────────────────────────
    # 3단계: 카테고리 통합 수집
    # ──────────────────────────────────────────────

    def collect_category(
        self,
        category_ko: str,
        date: str = None,
        max_pages: int = 30,
        max_articles: int = 1000,
        min_content_length: int = 200,
    ) -> List[Dict]:
        """
        카테고리 하나의 뉴스를 수집합니다.

        Args:
            category_ko: 한글 카테고리명 ("경제", "정치" 등)
            date: 날짜 (YYYYMMDD). None이면 오늘.
            max_pages: 목록 페이지 최대 수
            max_articles: 최대 수집 기사 수
            min_content_length: 최소 본문 길이

        Returns:
            유효 기사 리스트
        """
        config = CATEGORY_MAP.get(category_ko)
        if not config or not config.get("naver_sid"):
            logger.warning(f"[{category_ko}] Naver sid 없음, 스킵")
            return []

        sid = config["naver_sid"]
        category_en = config["api_name"]

        logger.info(f"📰 [{category_ko}] 수집 시작 (sid={sid})")
        t0 = time.time()

        # 목록 수집
        listed = self.fetch_article_list_pages(sid, max_pages, date)
        logger.info(f"  [{category_ko}] 목록: {len(listed)}건")

        if max_articles:
            listed = listed[:max_articles]

        # 상세 페이지 스크래핑
        valid = []
        failed = 0

        for i, article in enumerate(listed):
            detail = self.fetch_article_detail(article["link"])

            if detail and detail["content_length"] >= min_content_length:
                valid.append({
                    "title": article["title"],
                    "link": article["link"],
                    "press": article["press"],
                    "lede": article["lede"],
                    "thumbnail": article["thumbnail"],
                    "category": category_en,
                    "category_ko": category_ko,
                    **detail,
                })
            else:
                failed += 1

            if (i + 1) % 50 == 0:
                logger.info(
                    f"  [{category_ko}] {i+1}/{len(listed)} "
                    f"(유효={len(valid)}, 실패={failed})"
                )

            time.sleep(self.request_delay)

        elapsed = time.time() - t0
        logger.info(
            f"✅ [{category_ko}] 완료: {len(valid)}/{len(listed)}건 유효 "
            f"({elapsed:.1f}초)"
        )

        return valid

    # ──────────────────────────────────────────────
    # 헤드라인 수집 (파이프라인 미포함, 별도 저장)
    # ──────────────────────────────────────────────

    def fetch_headlines(self, sid: str) -> List[Dict]:
        """
        네이버 뉴스 헤드라인(에디터 큐레이션) 기사를 가져옵니다.
        파이프라인에는 미포함, 수집만 합니다.
        """
        url = f"https://news.naver.com/section/{sid}"

        try:
            with httpx.Client(
                headers=HEADERS, timeout=15.0, follow_redirects=True
            ) as client:
                resp = client.get(url)
                resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")
            section = soup.select_one(
                ".section_component.as_section_headline"
            )
            if not section:
                return []

            articles = []
            for item in section.select(".sa_item"):
                title_el = item.select_one(".sa_text_strong")
                link_el = item.select_one("a.sa_text_title")
                press_el = item.select_one(".sa_text_press")
                img_el = item.select_one("img")
                cluster_el = item.select_one(".sa_text_cluster")

                if not title_el or not link_el:
                    continue

                cluster_count = 0
                if cluster_el:
                    m = re.search(r"(\d+)", cluster_el.get_text())
                    if m:
                        cluster_count = int(m.group(1))

                thumbnail = ""
                if img_el:
                    thumbnail = (
                        img_el.get("data-src") or img_el.get("src") or ""
                    )

                articles.append({
                    "title": title_el.get_text(strip=True),
                    "link": link_el.get("href", ""),
                    "press": press_el.get_text(strip=True) if press_el else "",
                    "thumbnail": thumbnail,
                    "cluster_count": cluster_count,
                    "is_headline": True,
                })

            return articles

        except Exception as e:
            logger.error(f"헤드라인 수집 실패 (sid={sid}): {e}")
            return []
