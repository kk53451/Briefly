"""
G-Eval 대본 품질 평가 서비스

GPT-as-a-Judge 방식으로 뉴스 팟캐스트 대본의 품질을 자동 평가합니다.

평가 기준:
1. Neutrality (중립성): 정치적 편향 없이 균형잡힌 보도
2. Accuracy (정확성): 원본 기사 대비 사실 왜곡 여부
3. Readability (가독성): 자연스러운 대화체, 쉬운 설명
4. Coverage (커버리지): 주요 토픽을 빠짐없이 다루는지
5. Coherence (일관성): 토픽 간 자연스러운 전환
"""

import os
import json
import logging
from typing import Dict, List, Optional

from openai import OpenAI

logger = logging.getLogger(__name__)

EVAL_SYSTEM_PROMPT = """\
You are an expert broadcast journalism evaluator specializing in Korean news media.

You will evaluate a Korean news podcast script on multiple quality dimensions.
For each dimension, provide:
1. A score from 1-5 (1=very poor, 5=excellent)
2. A brief justification in Korean (1-2 sentences)
3. Specific issues found (if any)

Be strict and critical. A score of 5 means broadcast-ready quality.
"""

EVAL_USER_PROMPT_TEMPLATE = """\
## Task
Evaluate the following Korean news podcast script.

## Original Source Articles (for accuracy checking)
{source_articles}

## Script to Evaluate
{script}

## Evaluation Criteria

Rate each dimension from 1 to 5:

### 1. Neutrality (중립성)
- 5: Perfectly balanced, all perspectives presented equally
- 3: Minor imbalance, slightly favors one side
- 1: Clearly biased, one-sided reporting

### 2. Accuracy (정확성)
- 5: All facts match source articles, no hallucination
- 3: Mostly accurate, minor embellishments
- 1: Contains fabricated facts or misquotes

### 3. Readability (가독성)
- 5: Natural conversation, easy to understand, jargon explained
- 3: Mostly natural but some awkward phrasing
- 1: Stiff, unnatural, or overly complex language

### 4. Coverage (커버리지)
- 5: All major topics covered with appropriate depth
- 3: Some topics missing or superficially covered
- 1: Most topics missing

### 5. Coherence (일관성)
- 5: Smooth transitions, logical flow, clear structure
- 3: Some abrupt transitions
- 1: Disjointed, no clear structure

## Output Format
Respond in this exact JSON format:
```json
{{
  "neutrality": {{"score": <1-5>, "justification": "<Korean>", "issues": []}},
  "accuracy": {{"score": <1-5>, "justification": "<Korean>", "issues": []}},
  "readability": {{"score": <1-5>, "justification": "<Korean>", "issues": []}},
  "coverage": {{"score": <1-5>, "justification": "<Korean>", "issues": []}},
  "coherence": {{"score": <1-5>, "justification": "<Korean>", "issues": []}},
  "overall_score": <average of all scores, 1 decimal>,
  "summary": "<Korean, 2-3 sentence overall assessment>"
}}
```
"""


def evaluate_script(
    script: str,
    source_articles: List[Dict],
    model: str = None,
    max_sources: int = 600,  # gpt-5.4 1M 컨텍스트 — 카테고리 전체 투입
) -> Optional[Dict]:
    """
    G-Eval로 대본 품질을 평가합니다.

    Args:
        script: 평가할 팟캐스트 대본
        source_articles: 원본 기사 리스트 (카테고리 전체 권장)
        model: 평가에 사용할 모델 (기본: gpt-4o-mini)
        max_sources: 평가자에게 제공할 최대 기사 수

    Returns:
        평가 결과 딕셔너리, 실패 시 None
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY 환경변수가 없습니다.")
        return None

    client = OpenAI(api_key=api_key)
    # Judge 모델은 별도 환경변수. 기본값 gpt-5.4 (1M 컨텍스트, reasoning 지원)
    model = model or os.getenv("OPENAI_JUDGE_MODEL", "gpt-5.4")

    # 원본 기사 블록 (많이, 본문 전체 - gpt-5.4 1M 컨텍스트 활용)
    source_block = ""
    for i, article in enumerate(source_articles[:max_sources], 1):
        title = article.get("title", "")
        press = article.get("press") or article.get("provider", "")
        content = article.get("content", article.get("lede", ""))[:800]
        source_block += f"[{i}] [{press}] {title}\n{content}\n\n"

    logger.info(f"  G-Eval 소스 기사: {min(len(source_articles), max_sources)}건 제공 (judge={model})")

    user_prompt = EVAL_USER_PROMPT_TEMPLATE.format(
        source_articles=source_block,
        script=script,
    )

    logger.info(f"📊 G-Eval 평가 시작 (model={model})...")

    try:
        # gpt-5.4는 reasoning_effort 지원, temperature는 미지원
        is_reasoning = model.startswith(("gpt-5", "o1", "o3"))
        kwargs = {
            "model": model,
            "messages": [
                {"role": "system", "content": EVAL_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
        }
        if is_reasoning:
            kwargs["reasoning_effort"] = "high"
            # reasoning=high: reasoning + 출력 여유 필요
            kwargs["max_completion_tokens"] = 16000
        else:
            kwargs["temperature"] = 0.1
            kwargs["max_tokens"] = 2000

        response = client.chat.completions.create(**kwargs)

        result_text = response.choices[0].message.content.strip()
        result = json.loads(result_text)

        # overall_score 계산 (모델이 안 넣었을 경우)
        if "overall_score" not in result:
            scores = []
            for dim in ["neutrality", "accuracy", "readability", "coverage", "coherence"]:
                if dim in result and "score" in result[dim]:
                    scores.append(result[dim]["score"])
            if scores:
                result["overall_score"] = round(sum(scores) / len(scores), 1)

        logger.info(
            f"✅ G-Eval 완료: overall={result.get('overall_score', '?')}/5.0 "
            f"(tokens={response.usage.total_tokens})"
        )

        return result

    except json.JSONDecodeError as e:
        logger.error(f"❌ G-Eval JSON 파싱 실패: {e}")
        logger.debug(f"원본 응답: {result_text[:500]}")
        return None
    except Exception as e:
        logger.error(f"❌ G-Eval 실패: {e}")
        return None


def format_eval_report(eval_result: Dict) -> str:
    """평가 결과를 읽기 좋은 문자열로 포맷합니다."""
    if not eval_result:
        return "평가 결과 없음"

    lines = [
        f"Overall: {eval_result.get('overall_score', '?')}/5.0",
        "",
    ]

    for dim, label in [
        ("neutrality", "중립성"),
        ("accuracy", "정확성"),
        ("readability", "가독성"),
        ("coverage", "커버리지"),
        ("coherence", "일관성"),
    ]:
        data = eval_result.get(dim, {})
        score = data.get("score", "?")
        justification = data.get("justification", "")
        issues = data.get("issues", [])

        lines.append(f"  {label}: {score}/5 — {justification}")
        for issue in issues:
            lines.append(f"    ⚠️ {issue}")

    summary = eval_result.get("summary", "")
    if summary:
        lines.append(f"\n  종합: {summary}")

    return "\n".join(lines)
