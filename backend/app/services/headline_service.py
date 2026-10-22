"""
오늘의 브리핑 헤드라인 생성 서비스 (Ollama Gemma4 로컬)

Phase 2 rank_topics() 결과에서 각 토픽의 대표 기사들을 받아,
Gemma4 로컬 모델로 캐치한 헤드라인(15~25자)과 친근체 요약(80~120자)을 생성합니다.

비용: $0 (로컬 추론)
속도: ~30초/토픽, 5토픽 = ~2.5분

환경변수:
    OLLAMA_BASE_URL   (기본: http://localhost:11434)
    OLLAMA_MODEL      (기본: gemma4:e4b-it-q4_K_M)
"""

import json
import logging
import re
import time
from typing import Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "gemma4:e4b-it-q4_K_M"

HEADLINE_PROMPT_TEMPLATE = """\
다음은 같은 주제로 묶인 {count}개의 뉴스 기사 제목들입니다.

기사 제목:
{titles}

위 기사들을 대표하는 헤드라인과 요약을 작성하세요.

## headline 규칙 (가장 중요)
- **15~25자 평서문 명사형 압축**. 신문 1면 제목·뉴스 속보 헤드라인 스타일.
- **핵심 엔티티(인명·기관명·숫자·단위·핵심 동사 명사형)** 를 최대한 살려라.
- 기사 제목을 그대로 쓰지 말고 여러 기사의 공통분모를 추려 한 줄로 압축.
- **금지 — 이 중 하나라도 들어가면 실패**:
  * 의문문·수사문: "~일까?", "~일까요?", "~는?", "~인가?", "다음은?", "이유는?" ← 절대 금지
  * 경어체·구어체: "~해요", "~네요", "~입니다", "~다니" ← 절대 금지
  * 평가어·감탄: "놀라운", "충격", "주목", "눈길", "관심 집중", "화제" ← 피할 것
  * 부연어: "한편", "일단", "이제", "아직"
- 좋은 예:
  * "추경 35조 합의, 9일 국회 통과"
  * "美·이란 47년 만의 종전 협상 개시"
  * "서울 아파트값 하락, 경기 핵심지로 이동"
  * "디카페인 커피 수입 1만톤 돌파"
  * "민주당 4개 기초단체장 경선 결선행"
- 나쁜 예 (고치세요):
  * ❌ "추경, 35조 합의될까?" → ✅ "추경 35조 합의, 국회 통과 초읽기"
  * ❌ "이란 협상, 결과는?" → ✅ "美·이란 종전협상, 47년만 공식 대면"
  * ❌ "놀라운 집값 상승" → ✅ "경기 집값 6% 상승, 서울은 보합"

## summary 규칙
- 80~120자. 친근한 ~요/~해요 존댓말로 핵심 내용 요약.
- 독자가 이 토픽을 왜 봐야 하는지 알 수 있게.

반드시 아래 JSON 형식으로만 답하세요. 다른 설명 없이 JSON만:
{{"headline": "...", "summary": "..."}}"""


def _call_ollama(prompt: str, max_retries: int = 2) -> Optional[str]:
    """Ollama API 호출. thinking 토큰 대비 num_predict=2000."""
    for attempt in range(max_retries + 1):
        try:
            resp = httpx.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 2000,
                    },
                },
                timeout=180.0,
            )
            resp.raise_for_status()
            content = resp.json().get("response", "")
            if content.strip():
                return content
            logger.warning(f"  Ollama 빈 응답 (attempt {attempt + 1})")
        except Exception as e:
            logger.warning(f"  Ollama 호출 실패 (attempt {attempt + 1}): {e}")

    return None


def _parse_headline_json(text: str) -> Optional[Dict[str, str]]:
    """Gemma4 응답에서 JSON 추출. markdown fence 처리 포함."""
    if not text:
        return None

    # ```json ... ``` 블록 안의 JSON 추출
    fence_match = re.search(r"```(?:json)?\s*(\{[^`]+\})\s*```", text, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except json.JSONDecodeError:
            pass

    # 그냥 { ... } 추출
    brace_match = re.search(r"\{[^}]+\}", text)
    if brace_match:
        try:
            return json.loads(brace_match.group())
        except json.JSONDecodeError:
            pass

    return None


def generate_topic_headline(
    topic: Dict,
    max_titles: int = 8,
) -> Optional[Dict[str, str]]:
    """
    하나의 토픽에 대한 헤드라인+요약을 생성합니다.

    Args:
        topic: rank_topics() 출력의 개별 토픽 dict
               (member_titles, representative_article, size 등 포함)
        max_titles: 프롬프트에 넣을 최대 기사 제목 수

    Returns:
        {"headline": "...", "summary": "..."} 또는 None
    """
    # 토픽 멤버 기사 제목들
    titles = topic.get("member_titles", [])[:max_titles]
    if not titles:
        # fallback: 대표 기사 제목만이라도
        rep = topic.get("representative_article", {})
        if rep.get("title"):
            titles = [rep["title"]]

    if not titles:
        return None

    titles_block = "\n".join(f"- {t}" for t in titles)
    prompt = HEADLINE_PROMPT_TEMPLATE.format(
        count=topic.get("size", len(titles)),
        titles=titles_block,
    )

    raw = _call_ollama(prompt)
    parsed = _parse_headline_json(raw)

    if not parsed or "headline" not in parsed or "summary" not in parsed:
        logger.warning(
            f"  ⚠️ 토픽 '{titles[0][:30]}...' 헤드라인 파싱 실패"
        )
        # fallback: 대표 기사 제목 + lede 사용
        rep = topic.get("representative_article", {})
        return {
            "headline": rep.get("title", "")[:30],
            "summary": rep.get("lede", rep.get("content", ""))[:120],
        }

    return parsed


def generate_all_headlines(
    topics: List[Dict],
) -> List[Dict]:
    """
    모든 토픽에 대해 헤드라인+요약을 생성합니다.

    Args:
        topics: rank_topics() 출력 리스트

    Returns:
        토픽 데이터에 headline/summary가 추가된 리스트:
        [
            {
                "topic_id": 0,
                "size": 46,
                "headline": "ETF 400조 시대, 개미는 어디로?",
                "summary": "국내 ETF 시장이 400조원을 돌파했어요...",
                "representative_article": {...},
                "category": "economy",
                ...
            },
            ...
        ]
    """
    logger.info(f"📰 헤드라인 생성 시작: {len(topics)}개 토픽 (Gemma4 로컬)")
    t0 = time.time()

    results = []
    for i, topic in enumerate(topics):
        topic_t0 = time.time()
        headline_data = generate_topic_headline(topic)

        if headline_data:
            topic_with_headline = {
                **topic,
                "headline": headline_data["headline"],
                "summary": headline_data["summary"],
            }
        else:
            # 최종 fallback
            rep = topic.get("representative_article", {})
            topic_with_headline = {
                **topic,
                "headline": rep.get("title", "")[:30],
                "summary": rep.get("lede", "")[:120],
            }

        results.append(topic_with_headline)
        topic_elapsed = time.time() - topic_t0
        logger.info(
            f"  토픽 {i + 1}/{len(topics)} "
            f"({topic.get('size', 0)}건): "
            f"\"{topic_with_headline['headline'][:25]}\" "
            f"({topic_elapsed:.1f}초)"
        )

    elapsed = time.time() - t0
    logger.info(f"✅ 헤드라인 생성 완료: {len(results)}개, {elapsed:.1f}초")
    return results
