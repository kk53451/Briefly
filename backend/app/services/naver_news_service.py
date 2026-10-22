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
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import httpx
import pytz
from bs4 import BeautifulSoup

from app.constants.category_map import CATEGORY_MAP

_KST = pytz.timezone("Asia/Seoul")

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


def _ensure_kst(dt: datetime) -> datetime:
    """naive datetime 은 KST 로 간주해 localize, tz-aware 는 KST 로 변환."""
    if dt.tzinfo is None:
        return _KST.localize(dt)
    return dt.astimezone(_KST)


def _parse_kst_datetime(value: Optional[str]) -> Optional[datetime]:
    """네이버 `data-date-time` 값을 KST tz-aware datetime 으로 파싱.

    관찰된 포맷:
      - "2025-10-15 14:30:00"        (naive, KST 로 간주)
      - "2025-10-15T14:30:00"        (naive ISO)
      - "2025-10-15T14:30:00+09:00"  (tz-aware)

    파싱 실패 시 None.
    """
    if not value:
        return None
    s = value.strip()
    if not s:
        return None
    # ISO 표기 정규화: 공백 → T
    iso_candidate = s.replace(" ", "T", 1) if " " in s else s
    try:
        dt = datetime.fromisoformat(iso_candidate.replace("Z", "+00:00"))
    except ValueError:
        return None
    return _ensure_kst(dt)


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
    # 3-b. 시간 윈도우 수집 (오전/오후 통합 브리핑용)
    # ──────────────────────────────────────────────

    def collect_category_for_window(
        self,
        category_ko: str,
        window_start: datetime,
        window_end: datetime,
        max_pages: int = 30,
        max_articles: int = 1000,
        min_content_length: int = 200,
    ) -> "tuple[List[Dict], Dict]":
        """지정된 KST 시간 윈도우 안에 발행된 기사만 수집합니다.

        윈도우가 자정을 가로지르면 (오전 브리핑의 '전날 18:00 ~ 당일 05:00' 케이스)
        네이버의 날짜별 기사 리스트를 양쪽 날짜 모두 긁은 뒤 `published_at` 기준으로
        필터링합니다.

        Args:
            category_ko: 한글 카테고리명
            window_start: 윈도우 시작 시각 (tz-aware datetime, KST 권장)
            window_end: 윈도우 끝 시각 (exclusive, tz-aware datetime)
            max_pages / max_articles / min_content_length: collect_category 와 동일

        Returns:
            (articles, stats)
              articles: published_at 이 [window_start, window_end) 범위 안인 유효 기사 리스트
              stats:    윈도우 수집/필터 통계 dict, keys:
                - window_start, window_end           (str ISO)
                - window_hours                       (float, 편의)
                - naver_date_list_keys               (List[str] e.g. ["20260418","20260419"])
                - total_collected                    (int, 필터 전 unique 건수)
                - kept                               (int, 필터 후 유지 건수)
                - dropped_outside                    (int, 범위 밖 제거)
                - missing_pub                        (int, published_at 결측/파싱실패)
        """
        start_kst = _ensure_kst(window_start)
        end_kst = _ensure_kst(window_end)
        empty_stats = {
            "window_start": start_kst.isoformat(),
            "window_end": end_kst.isoformat(),
            "window_hours": 0.0,
            "naver_date_list_keys": [],
            "total_collected": 0,
            "kept": 0,
            "dropped_outside": 0,
            "missing_pub": 0,
        }
        if end_kst <= start_kst:
            logger.warning(
                f"[{category_ko}] 잘못된 윈도우: {start_kst} ~ {end_kst}"
            )
            return [], empty_stats

        # 윈도우가 걸치는 네이버 '날짜 리스트' 수집 (중복 fetch 없이 unique)
        dates_needed = set()
        cursor = start_kst
        while cursor < end_kst:
            dates_needed.add(cursor.strftime("%Y%m%d"))
            cursor += timedelta(hours=1)
        # 윈도우 끝이 정각에 걸치는 경우에도 해당 날짜 포함 보장
        dates_needed.add((end_kst - timedelta(seconds=1)).strftime("%Y%m%d"))

        logger.info(
            f"📰 [{category_ko}] 윈도우 수집 "
            f"({start_kst:%Y-%m-%d %H:%M} ~ {end_kst:%Y-%m-%d %H:%M} KST, "
            f"{len(dates_needed)}개 네이버 날짜 리스트)"
        )

        collected: Dict[str, Dict] = {}
        for date_str in sorted(dates_needed):
            arts = self.collect_category(
                category_ko=category_ko,
                date=date_str,
                max_pages=max_pages,
                max_articles=max_articles,
                min_content_length=min_content_length,
            )
            for a in arts:
                # 같은 기사가 양쪽 날짜 리스트에 동시 노출될 수 있어 link 키로 중복 제거
                key = a.get("link") or a.get("title", "")
                if key and key not in collected:
                    collected[key] = a

        # published_at 으로 윈도우 필터링
        kept: List[Dict] = []
        dropped = 0
        missing_pub = 0
        for a in collected.values():
            pub = _parse_kst_datetime(a.get("published_at"))
            if pub is None:
                missing_pub += 1
                continue
            if start_kst <= pub < end_kst:
                kept.append(a)
            else:
                dropped += 1

        logger.info(
            f"  🔎 [{category_ko}] 윈도우 필터: "
            f"{len(kept)}건 유지 / {dropped}건 범위 밖 / "
            f"{missing_pub}건 published_at 결측 (collected {len(collected)})"
        )

        stats = {
            "window_start": start_kst.isoformat(),
            "window_end": end_kst.isoformat(),
            "window_hours": round(
                (end_kst - start_kst).total_seconds() / 3600, 2
            ),
            "naver_date_list_keys": sorted(dates_needed),
            "total_collected": len(collected),
            "kept": len(kept),
            "dropped_outside": dropped,
            "missing_pub": missing_pub,
        }
        return kept, stats

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
