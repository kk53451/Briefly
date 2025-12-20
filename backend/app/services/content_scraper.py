# app/services/content_scraper.py

"""
범용 웹 스크래핑 유틸리티

BigKinds API는 본문을 최대 200자까지만 제공하므로,
provider_link_page (언론사 원문 URL)에서 전체 본문을 직접 스크래핑합니다.
"""

import os
import httpx
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import trafilatura
import re

USER_AGENT = os.getenv(
    "USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
)

# 주요 언론사별 도메인/본문 selector 지정
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

# 본문 내 "한글 비율" 체크 함수 (70% 이상만 유효 본문 인정)
def is_korean_text(text: str, threshold: float = 0.7) -> bool:
    """
    텍스트 내 한글 비율 검사 (한국 뉴스 여부 판별)
    """
    kor_count = len(re.findall(r"[가-힣]", text))
    total_count = len(re.findall(r"[가-힣a-zA-Z]", text))
    if total_count == 0:
        return False
    return kor_count / total_count >= threshold

# 불필요한 안내/광고/추천/앱 영역 selector (BS4 제거용)
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

# 노이즈 탐지용 키워드 (메뉴/네비게이션/푸터에서 자주 발견)
NOISE_KEYWORDS = {
    '닫기', '로그인', '회원가입', '전체메뉴', '오피니언',
    '개인정보처리방침', '청소년보호정책', '인기기사', '최신기사',
    '댓글정책', '구독신청', '뉴스레터', '광고문의'
}

# 본문 내 반복적으로 등장하는 안내/광고/제보/저작권 텍스트 정규식 패턴
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

def is_structural_noise(content: str) -> bool:
    """
    구조적 메트릭 기반 노이즈 탐지
    - 짧은 줄(10자 미만)이 30% 이상이고
    - 평균 줄 길이가 20자 미만이면 NOISE로 판정
    """
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    if len(lines) < 5:
        return False  # 너무 짧으면 판단 불가

    short_lines = sum(1 for l in lines if len(l) < 10)
    short_ratio = short_lines / len(lines)
    avg_line_len = len(content) / len(lines)

    # 짧은 줄이 30% 이상 AND 평균 줄 길이 20자 미만 → NOISE
    if short_ratio > 0.30 and avg_line_len < 20:
        return True

    return False


def count_noise_keywords(content: str) -> int:
    """노이즈 키워드 출현 횟수 반환"""
    count = 0
    for kw in NOISE_KEYWORDS:
        count += content.count(kw)
    return count


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

# [방법1] selector + BS4 방식 본문 추출 (실패 시 전체 텍스트 fallback)
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
                print(f"⚠ selector 존재하나 해당 요소 없음: {domain} → {selector}")
                text = soup.get_text(separator="\n")
        else:
            text = soup.get_text(separator="\n")

        # 본문 내 안내·광고·패턴·빈줄 제거
        text = clean_text_noise(text)
        return text.strip()

    except httpx.TimeoutException as e:
        print(f"⏱ [타임아웃] {url} - {e}")
        return ""
    except httpx.RequestError as e:
        print(f"❌ [요청오류] {url} - {e}")
        return ""
    except httpx.HTTPStatusError as e:
        print(f"❌ [HTTP오류] {url} - {e.response.status_code}")
        return ""
    except ValueError as e:
        print(f"❌ [URL파싱오류] {url} - {e}")
        return ""
    except Exception as e:
        print(f"❌ [본문추출 예상치 못한 오류] {url} - {e}")
        return ""

# [방법2] Trafilatura + BS4 혼합 방식 (최우선 방식)
def extract_content_flexibly(url: str, timeout: float = 10.0) -> str:
    """
    [2] Trafilatura 기반 본문 추출 우선
      - 광고/앱/추천 selector/패턴 모두 제거
      - 길이/문장수/한글비율 기준 통과 시만 반환(실패 시 BS4 fallback)
      - BigKinds provider_link_page URL에서 전체 본문 추출에 사용
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
            # 길이/문장수/한글뉴스/노이즈 기준 모두 만족해야 반환
            if content and len(content) >= 300 and content.count('.') >= 5:
                content = clean_text_noise(content)
                if is_korean_text(content, threshold=0.7):  # 한글뉴스만 통과
                    # 노이즈 필터링 (구조적 + 키워드)
                    if is_structural_noise(content):
                        print(f"⚠ [구조적노이즈] {url[:50]}...")
                    elif count_noise_keywords(content) >= 3:
                        print(f"⚠ [키워드노이즈] {url[:50]}...")
                    else:
                        return content.strip()
        # Trafilatura 실패/미달시 fallback: BS4 방식
        text = extract_content_with_bs4(url)
        if text and len(text) >= 300 and text.count('.') >= 5:
            text = clean_text_noise(text)
            if is_korean_text(text, threshold=0.7):
                # 노이즈 필터링 (구조적 + 키워드)
                if is_structural_noise(text):
                    print(f"⚠ [BS4-구조적노이즈] {url[:50]}...")
                elif count_noise_keywords(text) >= 3:
                    print(f"⚠ [BS4-키워드노이즈] {url[:50]}...")
                else:
                    return text
        return ""
    except ImportError as e:
        print(f"❌ [라이브러리 누락] trafilatura 설치 필요: {e}")
        return extract_content_with_bs4(url)
    except MemoryError as e:
        print(f"❌ [메모리 부족] {url} - {e}")
        return ""
    except Exception as e:
        print(f"❌ [혼합본문추출 예상치 못한 오류] {url} - {e}")
        return ""