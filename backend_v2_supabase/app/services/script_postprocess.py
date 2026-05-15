"""
대본 후처리 서비스

LLM이 SYSTEM_PROMPT 규칙을 100% 지키지 못하는 경우를 대비한 규칙 기반 안전망.

구성:
  1. 자동 수정 (확정적): 첫 두 줄 앵커 중복 병합, 연속 같은 화자 간섭 해소
  2. 경고 탐지 (로그만): 메타언어, 숫자 과밀, 기타 잠재 이슈

자동 수정은 규칙이 명확하고 손실 가능성이 없는 경우에만 적용. 메타언어 치환은
맥락 손상 위험이 있어 경고만 남기고, 다음 실험 반복 시 프롬프트 피드백으로 활용.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Tuple

logger = logging.getLogger(__name__)


# 메타언어 탐지용 정규식 (raw match)
META_PATTERNS = [
    (r'기사(?:들)?\s*(?:에\s*따르면|마다|에서는?|에선)', "기사 참조"),
    (r'이번\s*기사(?:들)?', "이번 기사"),
    (r'원문\s*기사', "원문 기사"),
    (r'원문(?:\s*에\s*따르면|\s*에서는|에서)', "원문 참조"),
    (r'제공된\s*기사', "제공된 기사"),
    (r'제공된\s*원문', "제공된 원문"),
    (r'제공된\s*자료', "제공된 자료"),
    (r'본\s*자료', "본 자료"),
    (r'[가-힣]+\s*기사(?:들)?(?:은|는|을|를|이|가)\s', "기사를 주어로 사용"),
]

# 숫자 + 단위 패턴 (기존 규칙 검증과 동일)
NUMBER_PATTERN = re.compile(
    r'\d[\d,]*\.?\d*\s*[%조억만원달러㎘t건명개종배%]'
)

# 문장 분리 (마침표, 물음표, 느낌표)
SENTENCE_SPLIT = re.compile(r'(?<=[.!?])\s+')

# 화자 태그
SPEAKER_PATTERN = re.compile(r'^(앵커|해설):\s*')


@dataclass
class PostprocessReport:
    """후처리 결과 리포트"""
    fixes_applied: List[dict] = field(default_factory=list)
    warnings: List[dict] = field(default_factory=list)

    @property
    def summary(self) -> str:
        return (
            f"자동 수정 {len(self.fixes_applied)}건, "
            f"경고 {len(self.warnings)}건"
        )

    def to_dict(self) -> dict:
        return {
            "fixes_applied": self.fixes_applied,
            "warnings": self.warnings,
            "fix_count": len(self.fixes_applied),
            "warning_count": len(self.warnings),
        }

    def log_summary(self):
        """logger 로 요약 출력"""
        if self.fixes_applied:
            logger.info(f"🔧 자동 수정 {len(self.fixes_applied)}건")
            for fix in self.fixes_applied:
                logger.info(f"    • {fix['type']}: {fix.get('note', '')}")

        if self.warnings:
            logger.warning(f"⚠️  후처리 경고 {len(self.warnings)}건")

            by_type = {}
            for w in self.warnings:
                by_type.setdefault(w["type"], []).append(w)

            for warn_type, items in by_type.items():
                logger.warning(f"    [{warn_type}] {len(items)}건")
                # 처음 3건만 샘플 출력
                for item in items[:3]:
                    snippet = item.get("match") or item.get("sentence", "")
                    line_no = item.get("line_no", "?")
                    logger.warning(f"      line {line_no}: {snippet[:80]}")
                if len(items) > 3:
                    logger.warning(f"      ... +{len(items) - 3}건 더")

        if not self.fixes_applied and not self.warnings:
            logger.info("✅ 후처리 통과: 문제 없음")


# ──────────────────────────────────────────────
# 자동 수정기
# ──────────────────────────────────────────────

def _merge_leading_duplicate_speaker(
    lines: List[str], report: PostprocessReport
) -> List[str]:
    """
    대본의 첫 두 줄이 연속으로 같은 화자(보통 '앵커:')인 경우 병합.

    예시:
      ["앵커: 안녕하세요, Briefly입니다.",
       "앵커: 오늘도 경제 뉴스를 짚어보겠습니다."]
      → ["앵커: 안녕하세요, Briefly입니다. 오늘도 경제 뉴스를 짚어보겠습니다."]
    """
    if len(lines) < 2:
        return lines

    # 빈 줄 스킵하고 처음 두 개의 non-empty 화자 줄 찾기
    first_idx = None
    second_idx = None
    for i, line in enumerate(lines):
        if SPEAKER_PATTERN.match(line.strip()):
            if first_idx is None:
                first_idx = i
            else:
                second_idx = i
                break

    if first_idx is None or second_idx is None:
        return lines

    first_line = lines[first_idx].strip()
    second_line = lines[second_idx].strip()

    first_match = SPEAKER_PATTERN.match(first_line)
    second_match = SPEAKER_PATTERN.match(second_line)
    if not first_match or not second_match:
        return lines

    first_speaker = first_match.group(1)
    second_speaker = second_match.group(1)

    if first_speaker != second_speaker:
        return lines

    # 같은 화자가 연속 → 병합
    first_content = first_line[first_match.end():]
    second_content = second_line[second_match.end():]

    merged = f"{first_speaker}: {first_content} {second_content}".strip()
    merged = re.sub(r"\s+", " ", merged)

    new_lines = lines.copy()
    new_lines[first_idx] = merged
    new_lines[second_idx] = ""  # 빈 줄로 치환 (원본 line number 유지)

    report.fixes_applied.append({
        "type": "speaker_merge_leading",
        "note": f"line {first_idx+1}, {second_idx+1} 병합 ({first_speaker})",
        "first_line": first_idx + 1,
        "second_line": second_idx + 1,
    })

    return new_lines


# ──────────────────────────────────────────────
# 경고 탐지기
# ──────────────────────────────────────────────

def _detect_meta_language(lines: List[str], report: PostprocessReport):
    """메타언어 사용 탐지 (자동 치환 없음, 경고만)"""
    for i, line in enumerate(lines):
        for pattern, label in META_PATTERNS:
            for match in re.finditer(pattern, line):
                # 화자 태그 뒤의 내용만 컨텍스트로 노출
                content = SPEAKER_PATTERN.sub("", line).strip()
                report.warnings.append({
                    "type": "meta_language",
                    "subtype": label,
                    "line_no": i + 1,
                    "match": match.group(),
                    "sentence": content[:120],
                })


def _detect_number_overload(lines: List[str], report: PostprocessReport):
    """
    한 문장에 3개 이상의 숫자+단위가 나오는 경우 탐지.
    화자 태그를 제거한 후 문장 단위로 분리해서 체크.
    """
    for i, line in enumerate(lines):
        content = SPEAKER_PATTERN.sub("", line).strip()
        if not content:
            continue

        # 문장별로 분리 후 각 문장에서 숫자 카운트
        sentences = SENTENCE_SPLIT.split(content)
        for sent in sentences:
            if not sent.strip():
                continue

            numbers = NUMBER_PATTERN.findall(sent)
            if len(numbers) >= 3:
                report.warnings.append({
                    "type": "number_overload",
                    "line_no": i + 1,
                    "count": len(numbers),
                    "numbers": numbers,
                    "sentence": sent.strip()[:150],
                })


def _detect_consecutive_same_speaker(
    lines: List[str], report: PostprocessReport
):
    """
    본문 전체에서 연속 같은 화자 탐지 (leading 중복은 자동 수정됐을 수 있음).
    자동 병합은 위험할 수 있으니 경고만.
    """
    last_speaker = None
    last_line_no = None

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue

        match = SPEAKER_PATTERN.match(stripped)
        if not match:
            continue

        current_speaker = match.group(1)

        if last_speaker is not None and current_speaker == last_speaker:
            report.warnings.append({
                "type": "consecutive_same_speaker",
                "line_no": i + 1,
                "speaker": current_speaker,
                "previous_line_no": last_line_no + 1,
                "sentence": stripped[:120],
            })

        last_speaker = current_speaker
        last_line_no = i


# ──────────────────────────────────────────────
# 공개 API
# ──────────────────────────────────────────────

def postprocess_script(script: str) -> Tuple[str, PostprocessReport]:
    """
    대본을 후처리하여 (1) 자동 수정을 적용하고 (2) 경고를 탐지합니다.

    Args:
        script: 검증/정제 완료 후의 대본 텍스트

    Returns:
        (cleaned_script, report)
            cleaned_script: 자동 수정 반영된 대본
            report: PostprocessReport (수정/경고 상세)
    """
    report = PostprocessReport()

    if not script or not script.strip():
        return script, report

    lines = script.split("\n")

    # 1. 자동 수정: 첫 두 줄 화자 중복 병합
    lines = _merge_leading_duplicate_speaker(lines, report)

    # 2. 경고 탐지
    _detect_meta_language(lines, report)
    _detect_number_overload(lines, report)
    _detect_consecutive_same_speaker(lines, report)

    # 빈 줄 정리 (자동 수정 과정에서 빈 줄이 추가됐을 수 있음)
    cleaned_lines = []
    prev_empty = False
    for line in lines:
        if not line.strip():
            if prev_empty:
                continue
            prev_empty = True
            cleaned_lines.append("")
        else:
            prev_empty = False
            cleaned_lines.append(line)

    cleaned = "\n".join(cleaned_lines).strip()
    report.log_summary()

    return cleaned, report
