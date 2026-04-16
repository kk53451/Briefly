"""
NotebookLM 팟캐스트 생성 서비스

notebooklm-py (비공식 API)를 사용하여 뉴스 토픽에서
한국어 대화형 팟캐스트를 생성합니다.

⚠️ 비공식 API — 프로덕션 사용 시 주의사항:
- 쿠키 만료 시 수동 재로그인 필요 (notebooklm login)
- Google ToS 리스크 (개인 프로젝트 수준에서는 현실적 위험 낮음)
- Lambda 불가 → 로컬 노트북에서만 실행
"""

import asyncio
import logging
import re
import time
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# TTS-safe 숫자 전처리
# ──────────────────────────────────────────────
#
# 실측: NotebookLM 이 "3,256만 명"을 "3,256명" 으로, "1만 40톤"을 "1만 4톤" 으로
# 잘못 발음하는 체계적 오류가 있음 (4/16 실험).
#
# 원인 가설: 대본에서 숫자와 단위가 공백 없이 붙어 있으면(`3256만명`) NotebookLM
# 내부 재작성 단계에서 토큰 경계가 모호해지고, 단위(만/억/조)가 드랍될 수 있음.
#
# 대응: 대본 → NotebookLM 전달 직전에 정규식으로 토큰 경계를 명시화.
#   1) 숫자 뒤 만/억/조 뒤에 공백 삽입 (다음 토큰이 숫자든 한글이든)
#   2) 만/억/조 앞 4자리 이상 숫자에 콤마 삽입
# 이것만으로는 100% 방어가 안 되므로 v2 instructions 에도 단위 보존 규칙을
# concrete example 과 함께 명시함 (벨트+멜빵).


def _tts_safe_numbers(text: str) -> str:
    """
    한국어 복합 숫자를 TTS 친화적 형태로 변환합니다.

    예시:
        3256만명   → 3,256만 명
        5억9701만원 → 5억 9,701만 원
        1만40톤     → 1만 40톤
        26조2000억원 → 26조 2,000억 원
        2027년      → 2027년 (변환 없음 - 만/억/조 없음)
        5,732건     → 5,732건 (변환 없음)

    Args:
        text: 원본 대본 텍스트

    Returns:
        숫자 경계가 명시화된 텍스트
    """
    if not text:
        return text

    # 1단계: 숫자+(만|억|조) 뒤에 공백 삽입
    #   - 다음 토큰이 숫자인 경우: `5억9` → `5억 9`
    text = re.sub(r"(\d)(만|억|조)(\d)", r"\1\2 \3", text)
    #   - 다음 토큰이 한글인 경우: `1만원` → `1만 원`, `0만명` → `0만 명`
    text = re.sub(r"(\d)(만|억|조)([가-힣])", r"\1\2 \3", text)

    # 2단계: (만|억|조) 앞 4자리 이상 숫자에 콤마 삽입
    #   - `3256만` → `3,256만`
    #   - `9701만` → `9,701만`
    #   - 2027년 처럼 만/억/조가 뒤에 없는 숫자는 건드리지 않음
    def _add_commas(m: "re.Match") -> str:
        num, unit = m.group(1), m.group(2)
        if len(num) >= 4:
            return f"{int(num):,}{unit}"
        return m.group(0)

    text = re.sub(r"(\d+)(만|억|조)", _add_commas, text)

    return text


# ──────────────────────────────────────────────
# NotebookLM 오디오 instructions
# ──────────────────────────────────────────────
#
# 이 instructions는 NotebookLM이 최종 오디오를 생성할 때의 "샤프한 가이드" 역할을
# 합니다. 대본(script_service.py SYSTEM_PROMPT)과 별개로, NotebookLM 내부 모델이
# 소스(대본 또는 원본 기사)를 자기 식으로 재해석하기 때문에 오디오 레이어에서도
# 톤·구조·금지 표현을 직접 지시해야 합니다.
#
# v1 (실측 4/14, script_adherence 2/5): 사실 충실도 5줄만 있어 톤 drift 발생.
# v2 (현재): 정체성 → 진행자 → 금지 표현 → 구조 → 사실/숫자/커버리지/중립성.
#
# 변경 이력은 INSTRUCTIONS_V1 을 아래에 보존해 A/B 비교에 사용할 수 있습니다.


INSTRUCTIONS_V1 = (
    "중요: 이 소스들은 한국 {category_ko} 뉴스의 실제 기사들입니다.\n\n"
    "⚠️ 필수 규칙:\n"
    "1. 반드시 제공된 소스 기사에 있는 사실만 다루세요. "
    "외부 지식이나 일반 상식을 추가하지 마세요.\n"
    "2. 소스에 없는 숫자, 통계, 인용구, 사건을 만들어내지 마세요.\n"
    "3. 소스 기사의 주요 내용을 빠짐없이 다루세요. "
    "일부 기사만 집중해서 다루면 안 됩니다.\n"
    "4. 정치적 주제에서는 모든 입장을 균형있게 다루세요.\n"
    "5. 전문 용어는 쉽게 풀어서 설명하세요.\n\n"
    "형식: 두 명의 진행자(앵커와 해설 전문가)가 자연스럽게 대화하는 한국어 뉴스 브리핑."
)


INSTRUCTIONS_V2_TEMPLATE = """당신은 "Briefly"의 전문 한국어 뉴스 브리핑 오디오를 제작합니다.

## 프로그램 정체성
Briefly는 한국 직장인을 위한 약 7분 분량의 데일리 {category_ko} 뉴스 브리핑입니다. 이번 에피소드는 **{time_slot} 브리핑**입니다 — 하루 두 번(오전/오후) 제공되는 정기 시간대 중 하나입니다. KBS 라디오 뉴스나 NPR Morning Edition 같은 **정통 방송 뉴스** 톤을 따릅니다. 캐주얼한 교양·설명 팟캐스트 스타일이 아닙니다.

## 진행자와 어조
- **앵커**: 차분하고 신뢰감 있는 뉴스 앵커. 헤드라인을 전달하고 대화를 이끕니다.
- **해설**: 전문 해설위원. 배경과 맥락, 의미를 짚어줍니다.
- 두 사람 모두 **방송 뉴스 존댓말**을 씁니다: "~로 집계됐습니다", "~라고 밝혔습니다", "그렇습니다", "맞습니다".

## 금지 표현 — 이것이 가장 중요합니다
아래 표현이 나오면 이 오디오는 실패입니다. 절대 사용하지 마세요:

- **친구 수다체**: "~잖아요", "~이더라고요", "어떻게 생각하세요?", "그쵸?"
- **감탄 리액션**: "와", "오", "아", "진짜요?", "대박이네요", "신기하네요", "깜짝 놀랐어요"
- **개인 감상**: "제가 보기엔", "정말 충격적입니다", "흥미로운 건", "재미있는 건"
- **청취자 호명**: "여러분", "청취자님", "오늘 우리가 볼 건", "같이 살펴보시죠"
- **기계적 전환**: "다음 소식은", "이어서", "다음으로 넘어가서"
- **메타 언어**: "기사에 따르면", "이 자료에 보면", "제공된 내용에서는"

대신 정통 뉴스 어조를 사용하세요: "정부 발표에 따르면", "업계 집계에 따르면", "보도에 따르면", "매체마다 추산이 다른데".

## 구조 (약 7분)
1. 앵커의 짧은 오프닝 한 문장으로 시작합니다: "안녕하세요, Briefly {category_ko} {time_slot} 브리핑입니다. 오늘의 주요 소식입니다."
2. 제공된 토픽을 **순서대로 모두** 다룹니다. 한두 가지에만 집중하지 마세요. 각 토픽 약 1분에서 1분 30초.
3. 토픽 전환은 앞 내용의 각도를 이어받는 **유기적 브릿지**로 합니다. 예: "이런 소비 흐름은 정책 쪽에도 영향을 줍니다" → 다음 토픽(정책).
4. 앵커의 짧은 클로징으로 마무리합니다: "지금까지 Briefly {category_ko} {time_slot} 브리핑이었습니다. 함께해주셔서 감사합니다."

## 사실과 숫자
- 제공된 소스에 있는 내용만 말합니다. **외부 지식이나 일반 상식을 절대 추가하지 마세요.** 소스에 없는 숫자·날짜·인용구·사건을 만들지 마세요. 이것은 방송 뉴스의 가장 기본 원칙입니다.
- 한 문장에 들어가는 숫자는 **최대 2개**입니다. 예산 분야별 배분처럼 수치가 여러 개인 경우 문장을 나누어 읽어주세요.
  - ❌ "고유가 10조4천억, 민생 2조8천억, 산업 3조, 지방 9조7천억, 국채 1조입니다."
  - ✅ "가장 큰 몫은 고유가 부담 완화에 들어간 10조4천억 원입니다. 그다음이 지방 재정 보강으로 9조7천억 원이 배정됐습니다..."
- 숫자를 말할 때는 반드시 시점·대상 같은 맥락을 동반합니다: "매출은 190% 늘었습니다" ❌ → "지난해 하이볼 매출은 190% 늘었습니다" ✅

### 단위 보존 — 방송 사고를 막는 절대 원칙
한국어 큰 단위(**만 / 억 / 조**)를 **절대 생략하거나 줄이지 마세요**. 단위 하나를 빠뜨리면 숫자가 10,000배 왜곡됩니다. 이것은 방송 정정 사안입니다.

실제로 발생했던 치명적 오류 (같은 실수를 반복하지 마세요):
- ❌ "3,256만 명" 을 "3,256명" 으로 읽음 → **단위 탈락, 인원이 10,000배 축소**
- ❌ "1만 40톤" 을 "1만 4톤" 으로 읽음 → **자릿수 탈락, 양이 10배 축소**
- ❌ "5억 9,701만 원" 을 "5억 9,710만 원" 으로 읽음 → **마지막 두 자릿수 뒤바뀜**

큰 숫자를 발음할 때는 **조 · 억 · 만** 경계에서 의식적으로 짧게 쉬고, 각 단위를 또박또박 말합니다:
- "3,256만 명" → "삼천이백오십육 · 만 · 명"
- "26조 2,000억 원" → "이십육조 · 이천억 · 원"
- "5억 9,701만 원" → "오억 · 구천칠백일만 · 원"

숫자가 여러 단위에 걸쳐 있을 때 단위를 하나라도 건너뛰거나 대충 뭉개면, 그건 **뉴스 사실관계 오류**입니다. 원문에 있는 단위는 전부 살려서 발음하세요.

## 커버리지
제공된 **모든 토픽**을 빠짐없이 다룹니다. 각 토픽은 1분 내외로 균형 있게 배분하세요. 흥미로운 한두 가지에만 시간을 쓰는 것은 금지입니다.

## 중립성
정치·정책 주제에서는 찬반 입장을 동일 비중으로 다룹니다. 소스에 한쪽 관점만 있으면 그 사실만 전달하고, 반대 입장을 상상해서 만들지 마세요. "놀라운", "충격적", "혁신적", "파격적" 같은 평가어는 쓰지 않습니다.

## 용어
전문 용어(추경, NPU, GPU, MoU 등)가 처음 나오면 해설이 한 문장으로 간단히 풀어 설명합니다.
"""


def _build_instructions(
    category_ko: str,
    version: str = "v2",
    time_slot: Optional[str] = None,
) -> str:
    """NotebookLM 오디오 instructions를 빌드합니다.

    Args:
        category_ko: 한글 카테고리명
        version: "v1" (구 버전, 5줄) 또는 "v2" (현재, 정통 방송 뉴스 톤 강제)
        time_slot: "오전" 또는 "오후". None 이면 현재 KST 시각 기준 자동 판정.
                   v1 에서는 사용되지 않습니다.

    Returns:
        category_ko, time_slot 이 치환된 instructions 문자열
    """
    if version == "v1":
        return INSTRUCTIONS_V1.format(category_ko=category_ko)

    if time_slot is None:
        from app.utils.date import get_briefing_slot
        time_slot = get_briefing_slot()

    return INSTRUCTIONS_V2_TEMPLATE.format(
        category_ko=category_ko,
        time_slot=time_slot,
    )


async def _generate_podcast_async(
    sources: List[Dict[str, str]],
    category_ko: str,
    language: str = "ko",
    method_label: str = "",
    instructions_version: str = "v2",
    time_slot: Optional[str] = None,
) -> Optional[str]:
    """
    NotebookLM으로 팟캐스트를 생성합니다 (async 내부).

    Args:
        sources: 소스 리스트 [{"title": ..., "content": ...}, ...]
        category_ko: 한글 카테고리명
        language: 오디오 언어 코드
        method_label: 파일명에 붙일 방식 라벨 (A/B/C)
        instructions_version: 오디오 instructions 버전 ("v1" 또는 "v2")
        time_slot: "오전" 또는 "오후". None 이면 현재 KST 기준 자동 판정.

    Returns:
        생성된 오디오 파일 경로 (str), 실패 시 None
    """
    from notebooklm import NotebookLMClient, AudioLength, DEFAULT_STORAGE_PATH

    storage = Path(DEFAULT_STORAGE_PATH)
    if not storage.exists():
        logger.error(
            f"❌ NotebookLM 인증 파일 없음: {storage}. "
            "'notebooklm login' 실행 필요."
        )
        return None

    # time_slot 이 지정되지 않았으면 현재 KST 기준으로 자동 판정
    if time_slot is None:
        from app.utils.date import get_briefing_slot
        time_slot = get_briefing_slot()

    instructions = _build_instructions(
        category_ko,
        version=instructions_version,
        time_slot=time_slot,
    )
    logger.info(
        f"📋 Instructions {instructions_version} 사용 "
        f"({len(instructions)}자, time_slot={time_slot})"
    )

    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    label = f"_{method_label}" if method_label else ""
    nb_title = f"Briefly {category_ko} {time_slot} 브리핑{label} {ts}"

    t0 = time.time()

    async with await NotebookLMClient.from_storage() as client:
        nb = await client.notebooks.create(nb_title)
        logger.info(f"📓 Notebook 생성: {nb.id} ({method_label or 'default'})")

        source_ids = []
        try:
            for source in sources:
                src = await client.sources.add_text(
                    nb.id,
                    source["title"],
                    source["content"],
                    wait=False,
                )
                source_ids.append(src.id)

            logger.info(f"⏳ 소스 인덱싱 대기 ({len(source_ids)}개)...")
            await client.sources.wait_for_sources(
                nb.id, source_ids, timeout=180.0
            )

            logger.info(f"🎧 오디오 생성 요청 (language={language})...")
            status = await client.artifacts.generate_audio(
                nb.id,
                source_ids=source_ids,
                language=language,
                instructions=instructions,
                audio_length=AudioLength.SHORT,
            )

            logger.info(f"⏳ 생성 완료 대기 (최대 20분)...")
            await client.artifacts.wait_for_completion(
                nb.id, status.task_id, timeout=1200.0
            )

            output_dir = Path("outputs")
            output_dir.mkdir(exist_ok=True)
            output_path = str(
                output_dir / f"podcast_{category_ko}_{time_slot}{label}_{ts}.mp3"
            )

            await client.artifacts.download_audio(nb.id, output_path)
            elapsed = time.time() - t0

            logger.info(
                f"✅ 팟캐스트 생성 완료: {output_path} ({elapsed:.1f}초)"
            )
            return output_path

        except Exception as e:
            logger.error(f"❌ 팟캐스트 생성 실패: {e}")
            return None

        finally:
            try:
                await client.notebooks.delete(nb.id)
                logger.info("🗑️ Notebook 정리 완료")
            except Exception:
                pass


def _script_to_sources(script: str, category_ko: str) -> List[Dict[str, str]]:
    """GPT 대본을 NotebookLM 소스 형식으로 변환.

    대본은 NotebookLM TTS 의 숫자 단위 탈락 오류를 막기 위해
    `_tts_safe_numbers()` 로 전처리됩니다.
    """
    safe_script = _tts_safe_numbers(script)
    return [{
        "title": f"Briefly {category_ko} 뉴스 대본",
        "content": safe_script,
    }]


def generate_podcast(
    script: str,
    category_ko: str,
    language: str = "ko",
    instructions_version: str = "v2",
    time_slot: Optional[str] = None,
) -> Optional[str]:
    """
    GPT 대본을 NotebookLM에 넘겨 팟캐스트 오디오를 생성합니다.

    방식 B (대본 → NotebookLM) 전용.

    Args:
        script: generate_script()로 생성된 대본 텍스트
        category_ko: 한글 카테고리명
        language: 오디오 언어 코드
        instructions_version: 오디오 instructions 버전 ("v1" 또는 "v2")
        time_slot: "오전" 또는 "오후". None 이면 현재 KST 기준 자동 판정

    Returns:
        생성된 오디오 파일 경로, 실패 시 None
    """
    if not script:
        logger.error("대본이 비어 있습니다.")
        return None

    sources = _script_to_sources(script, category_ko)
    logger.info(f"🎙️ 대본 → NotebookLM (1개 소스)")

    return asyncio.run(
        _generate_podcast_async(
            sources,
            category_ko,
            language,
            "podcast",
            instructions_version=instructions_version,
            time_slot=time_slot,
        )
    )


def check_auth() -> bool:
    """NotebookLM 인증 상태를 확인합니다."""
    from notebooklm import DEFAULT_STORAGE_PATH

    storage = Path(DEFAULT_STORAGE_PATH)
    if not storage.exists():
        return False

    # 간단한 API 호출로 쿠키 유효성 검사
    async def _check():
        from notebooklm import NotebookLMClient
        try:
            async with await NotebookLMClient.from_storage() as client:
                await client.notebooks.list()
                return True
        except Exception:
            return False

    return asyncio.run(_check())


def refresh_auth(wait_before_enter: float = 10.0) -> bool:
    """
    NotebookLM 인증을 자동 갱신합니다.

    `notebooklm login`을 실행하면 브라우저가 열리고 Google OAuth로 리다이렉트됩니다.
    브라우저에 이미 Google 로그인이 돼 있으면 자동으로 인증이 완료되고,
    CLI에서 Enter만 치면 쿠키가 저장됩니다.

    이 함수는 login 프로세스 실행 → 10초 대기(OAuth 완료 대기) → Enter 전송 →
    완료 대기 → check_auth()로 성공 여부 확인 순서로 동작합니다.

    Args:
        wait_before_enter: Enter 전송 전 대기 시간 (초). 기본 10초.

    Returns:
        갱신 성공 여부
    """
    import subprocess

    logger.info(f"🔐 NotebookLM 인증 갱신 시도 (Enter 전 {wait_before_enter}초 대기)...")

    try:
        proc = subprocess.Popen(
            ["notebooklm", "login"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # 브라우저가 열리고 OAuth 리다이렉트가 완료될 때까지 대기
        time.sleep(wait_before_enter)

        # Enter 전송
        proc.stdin.write(b"\n")
        proc.stdin.flush()

        # 프로세스 완료 대기 (최대 30초)
        proc.wait(timeout=30)

        if proc.returncode != 0:
            stderr = proc.stderr.read().decode(errors="replace")
            logger.warning(f"  ⚠️ notebooklm login 비정상 종료 (code={proc.returncode}): {stderr[:200]}")

    except subprocess.TimeoutExpired:
        proc.kill()
        logger.error("  ❌ notebooklm login 타임아웃 (30초)")
        return False
    except FileNotFoundError:
        logger.error("  ❌ notebooklm CLI를 찾을 수 없습니다. pip install notebooklm 필요.")
        return False
    except Exception as e:
        logger.error(f"  ❌ 인증 갱신 실패: {e}")
        return False

    # 갱신 성공 여부 확인
    ok = check_auth()
    if ok:
        logger.info("  ✅ 인증 갱신 성공")
    else:
        logger.error("  ❌ 인증 갱신 후에도 인증 실패")
    return ok


def ensure_auth() -> bool:
    """
    인증을 확인하고, 만료됐으면 자동 갱신을 시도합니다.

    scheduler.py에서 오디오 생성 전에 호출하는 통합 인터페이스.

    Returns:
        인증 유효 여부 (갱신 시도 포함)
    """
    if check_auth():
        return True

    logger.warning("  ⚠️ NotebookLM 인증 만료 → 자동 갱신 시도")
    return refresh_auth()
