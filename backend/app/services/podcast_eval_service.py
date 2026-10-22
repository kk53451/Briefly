"""
팟캐스트 오디오 전사본 품질 평가 서비스

faster-whisper로 전사된 팟캐스트 텍스트를 GPT-as-a-Judge로 평가합니다.
대본(script) 평가와 달리, 실제 음성으로 생성된 결과물의 품질을 측정합니다.

평가 차원:
1. Source Fidelity (소스 충실도): 원본 기사 내용이 팟캐스트에 정확히 반영되었는가
2. Conversational Flow (대화 흐름): 두 화자 간 대화가 자연스럽고 매끄러운가
3. Completeness (완결성): 주요 토픽을 빠짐없이 다루고, 논리적으로 완결되는가
4. Listenability (청취 적합성): 실제로 귀로 들었을 때 이해하기 쉬운 구조인가
5. Neutrality (중립성): 정치적/사회적 편향 없이 균형잡힌 보도인가
6. Engagement (몰입도): 청취자의 관심을 끌고 유지할 수 있는 내용인가
"""

import os
import json
import logging
from typing import Dict, List, Optional

from openai import OpenAI

logger = logging.getLogger(__name__)

PODCAST_EVAL_SYSTEM_PROMPT = """\
You are a senior broadcast quality assurance specialist at a major Korean media company.

You have 20+ years of experience evaluating radio and podcast programs. \
Your standards are high — you evaluate as if this podcast will air on a national \
broadcast network tomorrow morning.

You will compare a podcast transcript against the original source articles \
and a reference script (if provided) to assess broadcast readiness.

Be critical but fair. Consider that this is an AI-generated podcast — \
evaluate it against the standard of professional human-produced news podcasts.
"""

PODCAST_EVAL_USER_PROMPT = """\
## Original Source Articles
{source_articles}

## Reference Script (GPT-generated, what was intended)
{reference_script}

## Actual Podcast Transcript (what was actually spoken)
{transcript}

## Evaluation Criteria

Rate each dimension from 1 to 5. Be strict — 5 means broadcast-ready for national radio.

### 1. Source Fidelity (소스 충실도)
How accurately does the podcast reflect the original source articles?
- 5: All key facts from sources are present and accurately stated
- 4: Most facts accurate, 1-2 minor omissions
- 3: Several facts missing or slightly distorted
- 2: Significant omissions or inaccuracies
- 1: Podcast content barely relates to source articles

### 2. Conversational Flow (대화 흐름)
How natural and smooth is the conversation between speakers?
- 5: Indistinguishable from professional human broadcasters
- 4: Very natural with minor awkward moments
- 3: Generally okay but some stiff or formulaic exchanges
- 2: Noticeably robotic or unnatural
- 1: Feels like two separate monologues

### 3. Completeness (완결성)
Does the podcast cover all major topics with proper opening and closing?
- 5: All topics covered with appropriate depth, clear structure
- 4: Most topics covered, minor gaps
- 3: Some topics superficial or missing
- 2: Major topics missing
- 1: Incomplete or abruptly ends

### 4. Listenability (청취 적합성)
Would a commuter easily understand this while driving or walking?
- 5: Crystal clear, perfect pacing, easy to follow by ear
- 4: Very clear, occasional complex sentence
- 3: Mostly clear but some parts require concentration
- 2: Difficult to follow aurally
- 1: Confusing structure, impossible to follow by ear

### 5. Neutrality (중립성)
Is the reporting balanced and free from bias?
- 5: Perfectly balanced, multiple perspectives presented equally
- 4: Mostly balanced, slight leaning detectable
- 3: Noticeable but not egregious bias
- 2: Clearly favors one perspective
- 1: Propaganda-level bias

### 6. Engagement (몰입도)
Would listeners stay tuned or skip to the next podcast?
- 5: Compelling, would recommend to others
- 4: Interesting, would listen again
- 3: Adequate but forgettable
- 2: Boring, likely to skip
- 1: Would turn off immediately

### 7. Script Adherence (대본 반영도) — Only if reference script provided
How closely does the podcast follow the reference script's content and structure?
- 5: Faithfully follows script content while adding natural conversation
- 4: Mostly follows, with minor deviations that improve quality
- 3: Follows loosely, significant additions or omissions
- 2: Barely resembles the script
- 1: Completely ignores the script
- N/A: No reference script provided

## Output Format
Respond in this exact JSON format:
```json
{{
  "source_fidelity": {{"score": <1-5>, "justification": "<Korean, 2-3 sentences>"}},
  "conversational_flow": {{"score": <1-5>, "justification": "<Korean>"}},
  "completeness": {{"score": <1-5>, "justification": "<Korean>"}},
  "listenability": {{"score": <1-5>, "justification": "<Korean>"}},
  "neutrality": {{"score": <1-5>, "justification": "<Korean>"}},
  "engagement": {{"score": <1-5>, "justification": "<Korean>"}},
  "script_adherence": {{"score": <1-5 or null>, "justification": "<Korean or N/A>"}},
  "overall_score": <weighted average, 1 decimal>,
  "strengths": ["<Korean, top 2-3 strengths>"],
  "weaknesses": ["<Korean, top 2-3 weaknesses>"],
  "broadcast_ready": <true/false>,
  "summary": "<Korean, 3-4 sentence overall assessment>"
}}
```
"""


def evaluate_podcast_transcript(
    transcript: str,
    source_articles: List[Dict],
    reference_script: str = None,
    model: str = None,
    max_sources: int = 60,
) -> Optional[Dict]:
    """
    팟캐스트 전사본을 평가합니다.

    Args:
        transcript: 전사된 팟캐스트 텍스트
        source_articles: 원본 기사 리스트 (카테고리 전체)
        reference_script: GPT가 생성한 참조 대본 (방식 B/C에서 사용)
        model: 평가 모델
        max_sources: 평가자에게 제공할 최대 기사 수

    Returns:
        평가 결과 딕셔너리
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY 환경변수가 없습니다.")
        return None

    client = OpenAI(api_key=api_key)
    # Judge 모델: gpt-5.4 기본 (1M 컨텍스트, reasoning 지원)
    model = model or os.getenv("OPENAI_JUDGE_MODEL", "gpt-5.4")

    # 소스 기사 블록 (gpt-5.4의 1M 컨텍스트 활용 - 본문도 더 넓게)
    source_block = ""
    for i, article in enumerate(source_articles[:max_sources], 1):
        title = article.get("title", "")
        press = article.get("press") or article.get("provider", "")
        content = article.get("content", article.get("lede", ""))
        content = content[:800]
        source_block += f"[{i}] [{press}] {title}\n{content}\n\n"

    logger.info(f"  평가용 소스 기사: {min(len(source_articles), max_sources)}건 제공 (judge={model})")

    # 참조 대본
    ref_script_block = reference_script if reference_script else "(참조 대본 없음 — Script Adherence는 N/A로 평가)"

    user_prompt = PODCAST_EVAL_USER_PROMPT.format(
        source_articles=source_block,
        reference_script=ref_script_block,
        transcript=transcript,
    )

    logger.info(f"📊 팟캐스트 전사본 평가 시작 (model={model})...")

    try:
        # gpt-5.4/o1/o3는 reasoning 모델 — 파라미터가 다름
        is_reasoning = model.startswith(("gpt-5", "o1", "o3"))
        kwargs = {
            "model": model,
            "messages": [
                {"role": "system", "content": PODCAST_EVAL_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
        }
        if is_reasoning:
            kwargs["reasoning_effort"] = "high"
            # reasoning=high: reasoning + JSON 출력 여유 필요
            kwargs["max_completion_tokens"] = 20000
        else:
            kwargs["temperature"] = 0.1
            kwargs["max_tokens"] = 3000

        response = client.chat.completions.create(**kwargs)

        result = json.loads(response.choices[0].message.content.strip())

        # overall_score 계산
        if "overall_score" not in result:
            scores = []
            for dim in ["source_fidelity", "conversational_flow", "completeness",
                        "listenability", "neutrality", "engagement"]:
                if dim in result and isinstance(result[dim], dict):
                    s = result[dim].get("score")
                    if s is not None:
                        scores.append(s)
            if scores:
                result["overall_score"] = round(sum(scores) / len(scores), 1)

        logger.info(
            f"✅ 팟캐스트 평가 완료: overall={result.get('overall_score', '?')}/5.0 "
            f"(broadcast_ready={result.get('broadcast_ready', '?')})"
        )

        return result

    except json.JSONDecodeError as e:
        logger.error(f"❌ 평가 JSON 파싱 실패: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ 팟캐스트 평가 실패: {e}")
        return None


def format_podcast_eval_report(eval_result: Dict, method: str = "") -> str:
    """평가 결과를 읽기 좋은 문자열로 포맷합니다."""
    if not eval_result:
        return "평가 결과 없음"

    header = f"방식 {method} " if method else ""
    lines = [
        f"{header}Overall: {eval_result.get('overall_score', '?')}/5.0"
        f"  {'✅ 방송 가능' if eval_result.get('broadcast_ready') else '❌ 개선 필요'}",
        "",
    ]

    dims = [
        ("source_fidelity", "소스 충실도"),
        ("conversational_flow", "대화 흐름"),
        ("completeness", "완결성"),
        ("listenability", "청취 적합성"),
        ("neutrality", "중립성"),
        ("engagement", "몰입도"),
        ("script_adherence", "대본 반영도"),
    ]

    for dim, label in dims:
        data = eval_result.get(dim, {})
        if not isinstance(data, dict):
            continue
        score = data.get("score")
        if score is None:
            continue
        justification = data.get("justification", "")
        lines.append(f"  {label}: {score}/5 — {justification}")

    strengths = eval_result.get("strengths", [])
    if strengths:
        lines.append(f"\n  강점:")
        for s in strengths:
            lines.append(f"    ✅ {s}")

    weaknesses = eval_result.get("weaknesses", [])
    if weaknesses:
        lines.append(f"  약점:")
        for w in weaknesses:
            lines.append(f"    ⚠️ {w}")

    summary = eval_result.get("summary", "")
    if summary:
        lines.append(f"\n  종합: {summary}")

    return "\n".join(lines)
