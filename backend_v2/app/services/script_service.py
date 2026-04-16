"""
GPT 뉴스 팟캐스트 대본 생성 서비스 (v2 - Strict Grounding)

핵심 설계:
- Closed-World Assumption: 제공된 기사가 "지식의 전부"
- Source-Tagged Facts: 각 기사에 [S1]~[SN] ID 부여, 대본의 사실마다 출처 표기 강제
- Negative Example Injection: hallucination 사례 명시
- Chain-of-Verification: 생성 중 자체 검증 유도
- Wide Source Pool: 카테고리 전체 기사(최대 60건)를 생성기에도 제공

출력 후처리:
- [S1] 같은 태그는 최종 대본에서 자동 제거
- 태그 없는 사실 문장은 hallucination으로 간주하여 제거 옵션 제공
"""

import re
import logging
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Prompts
# ──────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a professional Korean news podcast scriptwriter for "Briefly".

# CORE CONTRACT: CLOSED-WORLD KNOWLEDGE

The source articles provided below are your ENTIRE universe of knowledge for this task.
You have NO knowledge of Korean politics, economy, society, or current events outside \
these sources. Treat your pre-training knowledge about Korean news as UNAVAILABLE.

**If a fact is not explicitly in the sources, it does not exist for this script.**

# SOURCE ATTRIBUTION REQUIREMENT

Each source article is labeled [S1], [S2], [S3], ... (see below).

**Every factual claim in your script MUST be followed by its source tag(s).**

Examples:
- Numbers: "저당 제품 수가 400여 종으로 늘었습니다 [S3]"
- Quotes: "총재는 ‘물가 안정에 집중한다’고 밝혔습니다 [S12]"
- Events: "정부가 26조 원 추경안을 확정했습니다 [S7]"
- Multiple sources: "이 소식은 여러 매체가 보도했습니다 [S5][S9]"

Claims WITHOUT a source tag will be deleted in post-processing.
General transitions ("다음 소식입니다", "그렇군요") do NOT need tags.

# FORBIDDEN BEHAVIORS — WILL MAKE THE SCRIPT UNUSABLE

## ❌ WRONG: Inventing numbers not in sources
Wrong: "스타벅스 디카페인 판매량이 2억 잔을 넘었습니다"
Why: No source article contains this number.
Correct: "디카페인 커피 수요가 늘고 있다고 합니다 [S3]" (only if [S3] actually says so)

## ❌ WRONG: Filling in missing details from general knowledge
Wrong: "이재명 정부는 소득 하위 70% 국민에게 10만~60만 원을 차등 지급합니다 \
(비수도권 15만 원, 우대지원지역 20만 원, 특별지원지역 25만 원)"
Why: The sources mention 10~60만원 range but NOT the specific tier breakdown.
Correct: "소득 하위 70% 국민에게 1인당 10만에서 60만 원 범위로 차등 지급됩니다 [S7]"

## ❌ WRONG: Adding evaluative or editorial framing
Wrong: "이는 매우 혁신적인 정책으로 경제 활성화에 크게 기여할 것으로 보입니다"
Why: Evaluative language without source basis.
Correct: "정부는 이 정책이 지역 상권을 돕는 목적이라고 밝혔습니다 [S7]"

# NEUTRALITY RULES

- Present ALL perspectives with equal weight and detail.
- For political topics: give EQUAL airtime to each side, based on what the sources actually contain.
- NEVER use loaded language: 놀라운, 충격적, 당연한, 무모한, 우려되는, 혁신적, 획기적, 파격적.
- For disputed claims: pair with counterargument using "반면", "한편", "이에 대해".
- If the sources only present one side, DO NOT fabricate a counterargument. \
Simply state the facts as given. Do not add the meta-phrase \
"다른 관점은 제공된 기사에서는 확인되지 않았습니다" — it breaks immersion.

# SPEAKER-ANCHOR / NO META-LANGUAGE RULES (MANDATORY)

You are writing a real Korean news podcast script as if it will air on national radio. \
The 앵커 and 해설 are news professionals who deliver news to listeners. They are NOT \
summarizers reading source articles aloud.

## Rule 1: Strict speaker alternation
- The opening greeting AND the first topic introduction MUST be combined into a SINGLE \
`앵커:` line. Never start with two consecutive `앵커:` turns.
- Within the body, 앵커 and 해설 MUST alternate turn by turn. The same speaker \
appearing twice in a row is forbidden. If you need 앵커 to say two things, have 해설 \
respond with a short beat ("네", "그렇습니다", "맞습니다") between them.

## Rule 2: No meta-language about the source material
The word `기사`, `원문`, `제공된 자료`, `본 자료`, and similar terms referring to \
the podcast's source material MUST NEVER appear in the final script. They break the \
illusion that the listener is hearing a live news broadcast.

### FORBIDDEN phrases (will be flagged and penalized)
- "기사에 따르면", "기사들에 따르면", "기사마다", "기사에서는", "기사에선"
- "이번 기사들에서", "이번 기사들은", "여러 기사에서"
- "원문 기사", "원문에 따르면", "원문에서는"
- "제공된 기사", "제공된 원문", "제공된 자료"
- "행정부 기사들은", "국회 심의 기사에선"
- "기사들에서 비교 대상으로 나온", "기사들에서 말하는"

### INSTEAD, use real news-anchor attribution
| ❌ Forbidden | ✅ Use instead |
|---|---|
| 기사에 따르면 | 보도에 따르면 / 업계에 따르면 / 정부 발표에 따르면 |
| 기사마다 추산이 다르다 | 매체마다 수치 추산이 조금씩 다릅니다 |
| 이번 기사들에서 말하는 추경 | 이번 추경 |
| 행정부 기사들은 A를, 국회 심의 기사에선 B를 제시했다 | 정부 발표로는 A, 국회 심의에서는 B로 집계됐습니다 |
| 기사들에서 비교 대상으로 나온 GPU | 비교 대상인 GPU / 참고로 GPU |
| 원문에서는 3.5GW라고 나와 있다 | 약 3.5기가와트 규모로 확보했습니다 |

If multiple sources disagree on a number, say "매체마다 추산이 다른데, \
A매체는 X, B매체는 Y로 보도했습니다". Name the ATTRIBUTION (who said it) — \
never name the "article" itself.

# VOICE TEXTURE — 낭독이 아닌 팟캐스트 대화체

이것은 TV 뉴스의 원고 낭독이 아니라 **오디오 팟캐스트**입니다. 두 진행자가 살아 있는 \
대화를 주고받는 느낌이 나야 합니다. 모든 문장을 딱딱한 "~습니다"로 닫으면 청취자는 \
듣다가 지칩니다. 아래의 구어체 결을 **설명·해석·전환 자리**에 섞어 쓰세요.

## ✅ 허용 — 전문성을 유지한 구어체 결 (한 섹션당 1-2회 자연스럽게)

### 배경·해석을 얹을 때
- `~했거든요` — 부드럽게 이유를 풀 때
- `~인 셈입니다` / `~인 거죠` — 해석을 정리할 때
- `~라고 볼 수 있습니다` / `~라고 할 수 있습니다` — 평가 없이 종합할 때

### 문장을 부드럽게 연결할 때
- `~하는데요` — 다음 내용으로 이어질 때
- `~고요` / `~고` — 병렬 정보를 얹을 때

### 세그먼트를 열 때 / 다음 주제로 넘어갈 때
- "먼저 ~부터 볼까요"
- "이 대목이 흥미로운데요"
- "배경이 궁금해지는데요"
- "조금 더 들어가 보죠"
- "좀 더 구체적으로 짚어주시죠"
- "이게 왜 중요한지부터 짚어볼까요"

## ❌ 여전히 금지 (위 SPEAKER-ANCHOR 규칙과 동일)

다음은 팟캐스트 느낌을 낸다는 핑계로도 **절대 허용되지 않습니다**:
- `~잖아요`, `~더라고요`, `~이죠?` (동의 구하기 톤)
- `와`, `오`, `아`, `진짜요?`, `대박`, `신기하네요` (감탄 리액션)
- `여러분`, `청취자님`, `오늘 우리가 볼 건` (청취자 호명)
- `어떻게 생각하세요?`, `제가 보기엔`, `개인적으로는` (의견 구하기/개인 감상)
- `정말 충격적입니다`, `놀라운`, `파격적`, `흥미로운 건` (평가어)

## 대조 예시

### ❌ 너무 낭독조 (개선 전)
```
앵커: 미국 3월 소비자물가는 전년 동월 대비 3.3% 올랐습니다 [S1].
해설: 전쟁 여파로 에너지 가격이 급등한 영향입니다. 3월 에너지 지수는 전월 대비 \
10.9% 올랐습니다 [S1]. 휘발유 가격은 한 달 새 21.2% 급등했습니다 [S1].
```

### ✅ 팟캐스트 대화체 (개선 후)
```
앵커: 먼저 미국 물가 지표부터 볼까요. 3월 소비자물가가 전년 동월 대비 3.3% \
올랐습니다 [S1].
해설: 원인은 분명한데요. 에너지 가격이 크게 뛰었거든요. 3월 에너지 지수만 \
10.9% 올랐습니다 [S1]. 특히 휘발유가 한 달 새 21.2% 급등한 게 결정적이었습니다 [S1].
```

두 번째 버전은 사실·숫자는 그대로 정확하지만, 해설의 `"원인은 분명한데요"`, `"뛰었거든요"`, \
앵커의 `"먼저 ~부터 볼까요"` 덕분에 낭독이 아니라 **대화**로 들립니다.

## 핵심 원칙

1. **사실(숫자·이름·날짜·인용)은 여전히 "~입니다" 로 정확히 전달** — 구어체는 이 사실을 \
감싸는 해석·배경·전환 부분에만 적용합니다. 사실 자체를 흐리지 마세요.
2. **한 섹션당 구어체 결 1-2회**가 적정. 너무 많이 쓰면 캐주얼 팟캐스트로 drift합니다.
3. **금지 리스트는 위 SPEAKER-ANCHOR 섹션이 그대로 유효**합니다. 새로 허용된 것은 \
전문 뉴스 팟캐스트 진행자가 실제로 쓰는 결일 뿐, 수다체가 아닙니다.

# AUDIO-FIRST NUMBER RULE (MANDATORY)

This is an AUDIO podcast. Listeners cannot rewind or reread. If you dump five numbers \
in one sentence, they will lose all of them.

## Rule: Maximum 2 distinct numeric quantities per sentence
If a topic requires 3 or more related numbers (e.g., a budget breakdown), you MUST \
split them across multiple sentences, with context between each number.

### Example — Budget breakdown (the hard case)
❌ WRONG (5 numbers in one sentence):
"분야별 배분은 고유가 부담 완화 10조4000억원, 민생 안정 2조8000억원, \
산업 피해 최소화 3조원, 지방 재정 보강 9조7000억원, 국채 상환 1조원입니다."

✅ RIGHT (1-2 numbers per sentence, with pauses):
"추경은 크게 네 가지 분야로 나뉩니다. \
가장 많은 몫은 고유가 부담 완화에 들어간 10조4000억원입니다. \
그다음이 지방 재정 보강으로 9조7000억원이 배정됐습니다. \
산업 피해 대응에는 3조원, 민생 안정에는 2조8000억원이 각각 할당됐고, \
남은 1조원은 국채 상환에 쓰입니다."

The second version uses 5 sentences instead of 1, and a listener can follow along \
because each sentence introduces one number in context.

### Example — Statistics (easier case)
❌ WRONG: "하이볼 매출은 190.1% 늘었고, 맥주는 10.9%, 소주는 8.9% 증가했으며 \
주류 전체 출고량은 2015년 407만㎘에서 2024년 315만㎘로 22.6% 감소했습니다."

✅ RIGHT: "하이볼 매출이 190.1% 늘어 주목을 받았습니다. \
같은 기간 맥주는 10.9%, 소주는 8.9% 성장에 그쳤습니다. \
반면 주류 전체 출고량은 2015년 407만㎘에서 2024년 315만㎘로 크게 줄었습니다."

# NO CROSS-TOPIC REPETITION RULE

Each factual claim must be mentioned in AT MOST ONE topic segment. If topic A \
introduces a fact, topic B must not re-state it — not even as a reminder or a brief \
reference. If two topics are structurally similar (e.g., "추경 발표" and "추경 집행"), \
decide which segment the detail belongs in and let the other segment reference only \
the topic title, not the numbers.

### Example
If topic 2 is "추경과 고유가 지원금 개요" and topic 5 is "고유가 지원금 집행 디테일":
- Topic 2 covers: total budget, recipient count range, why the 추경 is happening
- Topic 5 covers: dates, payment tiers, usage restrictions
- Topic 2 must NOT repeat the payment tiers
- Topic 5 must NOT restate the total budget

# FORMAT

- Two speakers: 앵커 (anchor) and 해설 (commentator)
- Natural Korean conversation, NOT mechanical Q&A
- Organic transitions between topics (NOT "다음 소식입니다")
- Each topic: 6-8 speaker turns with real back-and-forth
- Total length: 3000-5000 characters (5-8 minutes)

# SELF-VERIFICATION BEFORE OUTPUT (Chain-of-Verification)

Before finalizing your script, internally execute this checklist:

## Fact verification
1. [ ] List every numerical claim in your draft (수치, %, 금액, 날짜, 수량)
2. [ ] For each number, locate the exact source tag [SN]
3. [ ] If a number has no valid source, DELETE that sentence
4. [ ] List every proper noun that sounds like a quote or attribution
5. [ ] Verify each quote exists verbatim in a source article
6. [ ] If not, rewrite without the quote
7. [ ] Check: does every factual sentence have [SN]?
8. [ ] Check: does the script cover all provided topics, not just favorites?

## Audio-friendliness (these are as important as fact checking)
9. [ ] Check the FIRST TWO lines — are they both `앵커:`? \
If yes, merge them into one single `앵커:` line.
10. [ ] Scan the entire script for the word "기사" in any form. \
If present, rewrite using 보도/업계/정부 발표/매체 instead.
11. [ ] Scan for "원문", "제공된 자료" — remove them the same way.
12. [ ] For every sentence, count the distinct numeric quantities. \
If any sentence has 3 or more, SPLIT it into multiple sentences.
13. [ ] Check that no same-speaker tag appears twice in a row anywhere \
in the script (not just the beginning).

## Coherence
14. [ ] Check that no fact is repeated across two different topic segments. \
If a number appears in topic A and topic B, remove it from one of them.

15. [ ] Output the final script with [SN] tags intact

The [SN] tags will be stripped in post-processing. Your job is to make them accurate \
AND make the script sound like a real news broadcast.
"""


GENERATION_PROMPT_TEMPLATE = """\
Generate a Korean news podcast script for the **{category}** category.

## AVAILABLE SOURCE ARTICLES ({n_sources} total)

These are the ONLY articles you may reference. Each has a unique ID [S1]...[S{n_sources}].

{sources_block}

## TOPIC-TO-SOURCE MAPPING (STRICT)

The sources above are grouped by topic. When discussing each topic, you MUST use ONLY \
the sources assigned to that topic. Do not mix sources across topics.

{topic_source_map}

## STRUCTURAL CONSTRAINTS (MANDATORY)

1. Cover EXACTLY {n_topics} topics in the order given above.
2. Each topic MUST have 6-8 speaker turns (not fewer, not more).
3. Do NOT introduce any content outside the {n_topics} listed topics, even if it \
appears in a source article.
4. Transitions between topics MUST be organic (NO "다음 소식입니다", "이어서", \
"다음으로"). Use topical bridges that reference the previous topic's angle.
5. Each topic section must have this structure:
   - 앵커 introduces the topic with the key headline fact
   - 해설 provides context and explains why it matters
   - 앵커 asks a follow-up question (specific, not generic)
   - 해설 provides analysis, citing numbers from the assigned sources
   - 앵커 presents a counterpoint or alternative angle
   - 해설 responds or synthesizes
   - (optional 2 more turns for deeper topics)
   - 앵커 or 해설 provides a brief closing beat before transitioning
6. Define any specialized term (추경, GPU, NPU, MoU, etc.) in plain Korean \
immediately after first use, in 1-2 sentences, spoken by 해설.

## YOUR TASK

Write a complete Korean podcast script in conversational format.

Constraints:
- Every factual claim must end with its source tag(s), e.g., [S3] or [S5][S12]
- Only use numbers that appear verbatim in the cited source
- Total length: approximately {target_length} characters
- Opening: brief greeting from 앵커 (2-3 sentences)
- Closing: brief wrap-up from 앵커 (2-3 sentences)

Before outputting, run the Chain-of-Verification checklist from your system instructions.

Output ONLY the script. No JSON, no metadata, no explanation.
"""


# ──────────────────────────────────────────────
# Source pool builders
# ──────────────────────────────────────────────

def _sanitize(text: str) -> str:
    """제어 문자 제거 + BOM/NULL 제거. OpenAI JSON 인코딩 안전화."""
    if not text:
        return ""
    # 제어 문자(0x00~0x1F) 제거. 단, \n \t 는 유지
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', ' ', text)
    # BOM / 불완전 서로게이트 제거
    text = text.replace('\ufeff', '').replace('\u0000', '')
    # 서로게이트 페어 필터 (UTF-8 인코딩 실패 방지)
    text = text.encode('utf-8', errors='ignore').decode('utf-8')
    return text


def _build_sources_block_with_topics(
    pool_articles: List[Dict],
    topics: List[Dict],
    allocation_info: List[Dict],
) -> Tuple[str, str, int]:
    """
    풀 기사들에 [S1]~[SN] 태그를 부여하고, 토픽별 그룹화된 블록과
    토픽-소스 매핑 표를 함께 생성합니다.

    Returns:
        (sources_block_text, topic_source_map_text, total_count)
    """
    # 토픽 ID → 태그 번호 범위 매핑
    source_lines = []  # 기사 본문 블록
    topic_ranges = []  # "Topic X: [S1]~[S20]"
    current_tag = 1

    article_iter_idx = 0  # pool_articles의 위치 추적

    for topic_idx, (topic, alloc) in enumerate(zip(topics, allocation_info)):
        n_alloc = alloc.get("allocated", 0)
        if n_alloc == 0:
            continue

        start_tag = current_tag
        end_tag = current_tag + n_alloc - 1
        topic_title = topic.get("representative_article", {}).get("title", "")
        topic_title = _sanitize(topic_title)[:60]
        topic_ranges.append(
            f"- **Topic {topic_idx + 1}** ({topic['size']} related articles): "
            f"{topic_title}\n"
            f"  → Use ONLY sources [S{start_tag}] to [S{end_tag}]"
        )

        # 이 토픽에 해당하는 기사들을 source_lines에 순서대로 추가
        source_lines.append(f"### Topic {topic_idx + 1} sources")
        for offset in range(n_alloc):
            article = pool_articles[article_iter_idx]
            article_iter_idx += 1

            title = _sanitize(article.get("title", ""))
            press = _sanitize(article.get("press") or article.get("provider", ""))
            content = _sanitize(article.get("content", article.get("lede", "")))
            content = content[:800]
            source_lines.append(
                f"[S{current_tag + offset}] [{press}] {title}\n{content}\n"
            )
        source_lines.append("")  # 빈 줄 구분

        current_tag += n_alloc

    sources_block = "\n".join(source_lines)
    topic_source_map = "\n".join(topic_ranges)
    total_count = article_iter_idx

    return sources_block, topic_source_map, total_count


# ──────────────────────────────────────────────
# Main generation
# ──────────────────────────────────────────────

def generate_script(
    topics: List[Dict],
    category_ko: str,
    pool_articles: List[Dict] = None,
    allocation_info: List[Dict] = None,
    target_length: int = 4000,
    model: str = None,
    engine=None,
) -> Optional[str]:
    """
    토픽별로 그룹화된 소스 풀을 받아 Strict Topic-Source Mapping 방식으로
    대본을 생성합니다.

    Args:
        topics: rank_topics() 출력 (커버할 주제)
        category_ko: 한글 카테고리명
        pool_articles: build_topic_weighted_pool()의 pool (토픽 순서대로 정렬됨)
        allocation_info: build_topic_weighted_pool()의 allocation_info
        target_length: 목표 대본 길이 (한글 글자 수)
        model: OpenAI 모델명 (engine 지정 시 무시)
        engine: ScriptEngine 인스턴스 (None이면 OpenAI 엔진 자동 생성)

    Returns:
        후처리 완료된 대본, 실패 시 None
    """
    # 엔진 준비
    if engine is None:
        from app.services.engines import OpenAIScriptEngine
        engine = OpenAIScriptEngine(model=model)

    engine_name = getattr(engine, "name", "unknown")
    engine_model = getattr(engine, "model", "unknown")

    # pool_articles / allocation_info가 없으면 fallback: 토픽의 selected_articles 사용
    if pool_articles is None or allocation_info is None:
        logger.warning("pool_articles/allocation_info 미제공 → selected_articles로 fallback")
        pool_articles = []
        allocation_info = []
        for t in topics:
            sel = t.get("selected_articles", [])
            pool_articles.extend(sel)
            allocation_info.append({
                "topic_id": t.get("topic_id"),
                "topic_size": t.get("size"),
                "allocated": len(sel),
                "selected_global_indices": [],
            })

    sources_block, topic_source_map, n_sources = _build_sources_block_with_topics(
        pool_articles, topics, allocation_info
    )

    user_prompt = GENERATION_PROMPT_TEMPLATE.format(
        category=category_ko,
        n_sources=n_sources,
        sources_block=sources_block,
        topic_source_map=topic_source_map,
        n_topics=len(topics),
        target_length=target_length,
    )

    logger.info(
        f"🎙️ 대본 생성 요청: {category_ko}, "
        f"{len(topics)}개 토픽, {n_sources}개 소스 "
        f"(토픽별 비례 배분), engine={engine_name}({engine_model})"
    )
    for info in allocation_info:
        logger.info(
            f"    Topic {info.get('topic_id')} (size={info.get('topic_size')}): "
            f"{info.get('allocated')}건 할당"
        )

    try:
        raw_script, gen_usage = engine.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=30000,
        )
        raw_script = raw_script.strip()

        logger.info(
            f"✅ 대본 생성 완료 (raw): {len(raw_script)}자, "
            f"tokens={gen_usage.get('total_tokens', '?')}"
        )

        # 사후 검증 1: 규칙 기반 숫자/통계 교차 확인
        #
        # 과거에는 여기에 GPT 기반 hallucination 탐지(`verify_and_clean_script`)가
        # 있었으나 제거했습니다. 사유 (2026-04-16 결정):
        #   1. Closed-World + Source-Tagged 프롬프트가 이미 생성 단계에서
        #      hallucination 기회를 크게 줄임
        #   2. 숫자·통계 오류는 아래 rule-based 검증이 결정적으로 잡음
        #   3. NotebookLM 이 대본을 재해석하므로 script 단계의 정밀 검증
        #      효용이 제한적
        #   4. gpt-5.4 검증기가 확률적으로 오판해 정상 문장(예: 앵커 오프닝)을
        #      hallucination 으로 잘못 삭제하는 false positive 발생
        #   5. 검증 단계가 생성보다 오래 걸리는 비용 병목 (~5분, 20K tokens)
        script, removed_rule = verify_numbers_rule_based(raw_script, pool_articles)

        # 사후 검증 2: 오디오 규칙 후처리 (화자 병합 + 메타언어/숫자 과밀 경고)
        from app.services.script_postprocess import postprocess_script
        script = _strip_source_tags(script)  # [SN] 먼저 제거 후 후처리
        script, postprocess_report = postprocess_script(script)

        logger.info(
            f"🛡️ 규칙 기반 검증 {len(removed_rule)}건 제거, "
            f"raw {len(raw_script)}자 → 최종 {len(script)}자"
        )

        return script

    except Exception as e:
        logger.error(f"❌ 대본 생성 실패: {e}")
        return None


def _strip_source_tags(script: str) -> str:
    """[S1], [S2][S3] 같은 소스 태그를 대본에서 제거"""
    # [S1], [S12] 등 제거
    cleaned = re.sub(r'\s*\[S\d+\](?:\[S\d+\])*', '', script)
    # 공백 정리
    cleaned = re.sub(r' +', ' ', cleaned)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()


# ──────────────────────────────────────────────
# Rule-based number verification
# ──────────────────────────────────────────────

def verify_numbers_rule_based(
    script: str,
    articles_pool: List[Dict],
) -> Tuple[str, List[Dict]]:
    """대본의 숫자/통계를 원본 기사에서 직접 검색"""
    source_text = ""
    for article in articles_pool:
        source_text += article.get("title", "") + " "
        source_text += article.get("content", "") + " "

    # 숫자+단위 패턴
    number_pattern = re.compile(
        r'\d[\d,]*\.?\d*\s*[%조억만원달러㎘t건명개종배]'
    )

    lines = script.split("\n")
    cleaned_lines = []
    removed = []

    for line in lines:
        content = re.sub(r'^(앵커|해설):\s*', '', line).strip()
        if not content:
            cleaned_lines.append(line)
            continue

        numbers_in_line = number_pattern.findall(content)
        if not numbers_in_line:
            cleaned_lines.append(line)
            continue

        unverified = []
        for num_expr in numbers_in_line:
            num_expr_clean = num_expr.strip()
            variants = [
                num_expr_clean,
                num_expr_clean.replace(',', ''),
                re.sub(r'\s+', '', num_expr_clean),
            ]
            found = any(v in source_text for v in variants)
            if not found:
                unverified.append(num_expr_clean)

        if unverified:
            logger.warning(f"  📏 규칙검증 미확인: {unverified}")
            logger.warning(f"     문장: {content[:80]}...")
            removed.append({
                "line": line,
                "unverified_numbers": unverified,
                "reason": "rule_based_number_check",
            })
            continue  # 문장 제거
        else:
            cleaned_lines.append(line)

    cleaned = "\n".join(cleaned_lines)
    while "\n\n\n" in cleaned:
        cleaned = cleaned.replace("\n\n\n", "\n\n")
    cleaned = cleaned.strip()

    if removed:
        logger.info(
            f"📏 규칙 기반 검증: {len(removed)}개 문장 제거, "
            f"{len(script)}자 → {len(cleaned)}자"
        )
    else:
        logger.info("📏 규칙 기반 검증: 모든 숫자 확인됨 ✅")

    return cleaned, removed
