import os
import httpx
from typing import List, Literal
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import trafilatura
import re

from app.utils.dynamo import get_news_by_category_and_date, get_news_card_by_id, get_news_card_by_content_url
from app.constants.category_map import CATEGORY_MAP

#  환경 변수에서 API 키 및 기본 설정 로드
DEEPSEARCH_API_KEY = os.getenv("DEEPSEARCH_API_KEY")
DEEPSEARCH_BASE_URL = "https://api-v2.deepsearch.com/v1"
USER_AGENT = os.getenv(
    "USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
)
HEADERS = {
    "Authorization": f"Bearer {DEEPSEARCH_API_KEY}",
    "Content-Type": "application/json",
    "User-Agent": USER_AGENT
}

#  주요 언론사별 도메인/본문 selector 지정
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

#  본문 내 "한글 비율" 체크 함수 (70% 이상만 유효 본문 인정)
def is_korean_text(text: str, threshold: float = 0.7) -> bool:
    """
    텍스트 내 한글 비율 검사 (한국 뉴스 여부 판별)
    """
    kor_count = len(re.findall(r"[가-힣]", text))
    total_count = len(re.findall(r"[가-힣a-zA-Z]", text))
    if total_count == 0:
        return False
    return kor_count / total_count >= threshold

#  불필요한 안내/광고/추천/앱 영역 selector (BS4 제거용)
KNOWN_TRASH_SELECTORS = [
    ".txt-copyright", ".adrs", ".sns-box", ".relate_news", ".copy",
    ".recommend", ".app-down", ".guide", ".comment", ".news_app_banner",
    ".article-ad", "#recommend", "#comment", "#reply", ".promotion"
]

UNWANTED_KEYWORDS = [
    "이 기사의 댓글 정책을 결정합니다",
    "앱 다운", "빠르고 정확한 연합뉴스", "이 기사를 추천합니다",
    "글자 크기 변경하기", "네이버 AI 뉴스 알고리즘",
    "프리미엄콘텐츠", "본 기사와 무관한 광고", "해당 언론사에서 선정하며",
    "사고로 해발", "기사 추천은", "모두에게 보여주고 싶은 기사라면",
    "텍스트 음성 변환 서비스 사용하기", "글자로 지은 집7", "이 콘텐츠의 저작권은",
    "섹션 정보는", "댓글 정책", "해당 언론사", "관련 업계에 따르면",
    "인용된 모든 콘텐츠는", "당신의 의견을 남겨주세요", "클릭! 기사는 어떠셨나요?"
]

#  본문 내 반복적으로 등장하는 안내/광고/제보/저작권 텍스트 정규식 패턴
REMOVE_TEXT_PATTERNS = [
    # 기자 이름 + 이메일
    r"^[가-힣]{2,4}\s?기자\s?[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    r"^[가-힣]{2,4}\s?기자$",
    r"^[가-힣]{2,4}\s?\([^)]+@[^\s)]+\)$",

    # 저작권 안내
    r"^Copyright.*", r"^무단[^\n]{0,20}전재.*", r"^재배포 금지.*",

    # 제보 안내
    r"^\[카카오톡\].*", r"^\[메일\].*", r"^\[전화\].*",
]
REMOVE_TEXT_PATTERNS_COMPILED = [re.compile(pat) for pat in REMOVE_TEXT_PATTERNS]

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_PATTERN = re.compile(r"\d{2,3}-\d{3,4}-\d{4}")

def clean_text_noise(text: str) -> str:
    """
    뉴스 본문에서 불필요한 안내/광고/기자정보/저작권 텍스트 제거
    """
    if not isinstance(text, str):
        return ""

    cleaned_lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # 1. 줄 전체 제거 패턴 (기자, 저작권, 제보 등)
        if any(pat.match(line) for pat in REMOVE_TEXT_PATTERNS_COMPILED):
            continue

        # 2. 이메일, 전화번호 포함 여부 (줄 내부 검색)
        if EMAIL_PATTERN.search(line) or PHONE_PATTERN.search(line):
            continue

        # 3. 일반 광고/안내 키워드 포함 여부 (in 연산자 기반)
        if any(kw in line for kw in UNWANTED_KEYWORDS):
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)

#  [방법1] selector + BS4 방식 본문 추출 (실패 시 전체 텍스트 fallback)
def extract_content_with_bs4(url: str, timeout: float = 10.0) -> str:
    """
    [1] BeautifulSoup 기반 기사 본문 추출
      - 기사 도메인별 selector 우선
      - 없으면 전체 텍스트
      - 광고/앱/댓글/추천 selector 영역 및 패턴 모두 제거
      - 한글 인코딩 깨짐 방지(encoding 지정)
      - 최종 clean_text_noise()로 정제
    """
    try:
        response = httpx.get(
            url,
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT}
        )
        # 한글 뉴스 인코딩 깨짐 방지(utf-8/CP949 등)
        # response.encoding = response.apparent_encoding or 'utf-8' 
        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        # 광고/불필요 태그 삭제
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        for selector in KNOWN_TRASH_SELECTORS:
            for tag in soup.select(selector):
                tag.decompose()

        # 도메인별 기사 selector → 없으면 전체 텍스트
        domain = urlparse(url).netloc.replace("www.", "")
        selector = ARTICLE_SELECTORS.get(domain)

        if selector:
            article_tag = soup.select_one(selector)
            if article_tag:
                text = article_tag.get_text(separator="\n")
            else:
                print(f" selector 존재하나 해당 요소 없음: {domain} → {selector}")                
                text = soup.get_text(separator="\n")
        else:
            text = soup.get_text(separator="\n")

        # 본문 내 안내·광고·패턴·빈줄 제거
        text = clean_text_noise(text)
        return text.strip()

    except httpx.TimeoutException as e:
        print(f" [타임아웃] {url} - {e}")
        return ""
    except httpx.RequestError as e:
        print(f" [요청오류] {url} - {e}")
        return ""
    except httpx.HTTPStatusError as e:
        print(f" [HTTP오류] {url} - {e.response.status_code}")
        return ""
    except ValueError as e:
        print(f" [URL파싱오류] {url} - {e}")
        return ""
    except Exception as e:
        print(f" [본문추출 예상치 못한 오류] {url} - {e}")
        return ""

#  [방법2] Trafilatura + BS4 혼합 방식 (최우선 방식)
def extract_content_flexibly(url: str, timeout: float = 10.0) -> str:
    """
    [2] Trafilatura 기반 본문 추출 우선
      - 광고/앱/추천 selector/패턴 모두 제거
      - 길이/문장수/한글비율 기준 통과 시만 반환(실패 시 BS4 fallback)
      - *실제 모든 뉴스 추출 함수에서 이 함수로 통일*
    """
    try:
        # Trafilatura로 원본 HTML fetch
        html = trafilatura.fetch_url(url)
        if html:
            soup = BeautifulSoup(html, "html.parser")
            for selector in KNOWN_TRASH_SELECTORS:
                for tag in soup.select(selector):
                    tag.decompose()
            content = trafilatura.extract(str(soup))
            # 길이/문장수/한글뉴스 기준 모두 만족해야 반환
            if content and len(content) >= 300 and content.count('.') >= 5:
                content = clean_text_noise(content)
                if is_korean_text(content, threshold=0.7):  # 한글뉴스만 통과
                    return content.strip()
        # Trafilatura 실패/미달시 fallback: BS4 방식
        text = extract_content_with_bs4(url)
        if text and len(text) >= 300 and text.count('.') >= 5:
            text = clean_text_noise(text)
            if is_korean_text(text, threshold=0.7):
                return text
        return ""
    except ImportError as e:
        print(f" [라이브러리 누락] trafilatura 설치 필요: {e}")
        return extract_content_with_bs4(url)
    except MemoryError as e:
        print(f" [메모리 부족] {url} - {e}")
        return ""
    except Exception as e:
        print(f" [혼합본문추출 예상치 못한 오류] {url} - {e}")
        return ""

async def fetch_top_articles(
    category: str,
    size: int = 30,
    section: Literal["domestic", "international"] = "domestic"
) -> List[dict]:
    """
    (테스트용) 특정 카테고리의 인기 기사 리스트 조회

    Args:
        category (str): 카테고리 영문명 (예: "politics")
        size (int): 기사 수 (기본 30)
        section (str): 국내 or 해외 기사 구분

    Returns:
        List[dict]: 기사 목록 (딥서치 응답 그대로)
    """
    url = (
        f"{DEEPSEARCH_BASE_URL}/articles/{category}"
        if section == "domestic"
        else f"{DEEPSEARCH_BASE_URL}/global-articles/{category}"
    )

    params = {"sort": "popular", "page_size": size}

    async with httpx.AsyncClient(headers=HEADERS) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json().get("data", [])

def fetch_valid_articles_by_category(
    category: str,
    start_time: str,
    end_time: str,
    size: int = 60,
    limit: int = 30,
    sort: Literal["popular", "traffic"] = "popular",
    section: Literal["domestic", "international"] = "domestic",
    min_content_length: int = 300,
    max_try: int = 5
) -> List[dict]:
    """
     [뉴스 수집용] 카테고리별 뉴스 중 본문이 유효한 기사만 필터링하여 반환
    - 딥서치 API로 기사 리스트 조회 후 각 기사에 대해 extract_content_flexibly로 본문 추출
    - 메모리 + DB 기반 중복 필터링 
    - 한글 뉴스만 선별
    """
    seen_ids = set()
    seen_urls = set()
    seen_titles = set()
    results = []
    page = 1

    while len(results) < limit and page <= max_try:
        url = (
            f"{DEEPSEARCH_BASE_URL}/articles/{category}"
            if section == "domestic"
            else f"{DEEPSEARCH_BASE_URL}/global-articles/{category}"
        )
        params = {
            "date_from": start_time,
            "date_to": end_time,
            "sort": sort,
            "page_size": size,
            "page": page
        }
        response = httpx.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        all_articles = response.json().get("data", [])
        if not all_articles:
            break

        for article in all_articles:
            news_id = article.get("id")
            article_url = article.get("content_url")
            title = article.get("title", "").strip()

            # 1. 메모리 기준 중복 필터
            if not article_url or not news_id:
                continue
            if news_id in seen_ids or article_url in seen_urls:
                continue
            if title and title in seen_titles:
                continue

            # 2. DB 기준 중복 필터 (운영 환경에서 활성화 권장)
            if get_news_card_by_id(news_id):
                continue
            if get_news_card_by_content_url(article_url):
                continue

            seen_ids.add(news_id)
            seen_urls.add(article_url)
            if title:
                seen_titles.add(title)

            # 3. 본문 추출 및 유효성 필터
            content = extract_content_flexibly(article_url)
            if not content or len(content) < min_content_length:
                continue
            if not is_korean_text(content, threshold=0.7):
                continue

            article["content"] = content
            results.append(article)
            if len(results) >= limit:
                break
        page += 1

    return results[:limit]

def fetch_detailed_articles(category: str, date: str, limit: int = 30) -> List[dict]:
    """
    저장된 뉴스 중 content 필드가 비어 있는 기사에 대해 본문을 재추출하여 채워주는 함수

    Args:
        category (str): 카테고리 영문명
        date (str): 날짜 (YYYY-MM-DD)
        limit (int): 최대 기사 수

    Returns:
        List[dict]: 본문이 보완된 뉴스 리스트
    """
    all_items = get_news_by_category_and_date(category, date)
    results = []

    for item in all_items:
        if "content" in item and item["content"]:
            results.append(item)
            continue

        content_url = item.get("content_url")
        if not content_url:
            continue

        # 개선된 본문 추출 함수 사용
        content = extract_content_flexibly(content_url)
        if content and len(content) >= 300:
            item["content"] = content
            results.append(item)

        if len(results) >= limit:
            break

    return results
