"""
알림 서비스 (Discord 웹훅 2채널)

#briefly-alerts:    최종 결과, 에러, 인증 경고 (하루 2건)
#briefly-pipeline:  단계별 진행 로그 (카테고리당 8~10건)

환경변수:
    DISCORD_WEBHOOK_URL           — alerts 채널
    DISCORD_PIPELINE_WEBHOOK_URL  — pipeline 채널
"""

import os
import re
import time
import logging
from typing import Dict, List

import httpx

logger = logging.getLogger(__name__)


# log_step 단계별 소요 시간 측정용 — (category, step prefix) → 시작 timestamp.
# "시작" 호출 시 기록하고 "완료"/"실패" 호출 시 빼내서 elapsed 메시지에 첨부.
_STEP_TIMERS: Dict[str, float] = {}

# step 문자열에서 단계 식별자 추출용 (예: "5️⃣-b 홈 탭 NewsCards 저장 시작" → "5️⃣-b")
# emoji digit + optional sub-letter 매칭, 없으면 첫 토큰으로 fallback.
_STEP_PREFIX_RE = re.compile(r"\d️⃣(?:-[a-zA-Z])?")


def _extract_step_prefix(step: str) -> str:
    m = _STEP_PREFIX_RE.search(step)
    if m:
        return m.group(0)
    return step.split(maxsplit=1)[0] if step else ""


def _format_elapsed(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}초"
    minutes, secs = divmod(seconds, 60)
    return f"{int(minutes)}분 {secs:.1f}초"


def _get_alert_webhook() -> str:
    return os.getenv("DISCORD_WEBHOOK_URL", "")


def _get_pipeline_webhook() -> str:
    return os.getenv("DISCORD_PIPELINE_WEBHOOK_URL", "")


def _send(
    webhook_url: str,
    message: str,
    color: int = 0x00FF00,
    title: str = None,
    fields: List[dict] = None,
) -> bool:
    """Discord 웹훅 전송 (내부 공통)."""
    if not webhook_url:
        return False

    payload = {}
    if title or fields:
        embed = {"description": message, "color": color}
        if title:
            embed["title"] = title
        if fields:
            embed["fields"] = fields
        payload["embeds"] = [embed]
    else:
        payload["content"] = message

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(webhook_url, json=payload)
            resp.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Discord 알림 전송 실패: {e}")
        return False


# ──────────────────────────────────────────────
# #briefly-alerts (최종 결과, 에러, 인증)
# ──────────────────────────────────────────────

def send_discord(message: str, color: int = 0x00FF00, title: str = None, fields: List[dict] = None) -> bool:
    """alerts 채널로 전송."""
    return _send(_get_alert_webhook(), message, color, title, fields)


def format_elapsed(total_sec: float) -> str:
    """초 → '3분 21초' 또는 '47초'. 한 시간 넘으면 '1시간 5분 12초'."""
    total = int(total_sec)
    hours, rem = divmod(total, 3600)
    minutes, seconds = divmod(rem, 60)
    if hours:
        return f"{hours}시간 {minutes}분 {seconds}초"
    if minutes:
        return f"{minutes}분 {seconds}초"
    return f"{seconds}초"


# 이전 버전과의 호환을 위한 별칭 (향후 제거 예정)
_format_elapsed = format_elapsed


def notify_pipeline_success(feed_results: list, briefing_result: dict = None):
    """파이프라인 완료 알림 → alerts.

    통합 브리핑 리워크 이후:
    - 카테고리별 필드는 Feed 단계 통계만 표시 (기사/토픽 수).
    - briefing_result 가 주어지면 통합 브리핑(오전/오후) 상태를 마지막 필드로 추가.
      이때 briefing_result["title"] 이 있으면 헤드라인 한 줄 요약도 같이 표시.
    """
    fields = []
    for r in feed_results:
        cat = r.get("category", "?")
        status = r.get("status", "?")
        collected = r.get("collected", 0)
        n_clusters = r.get("clustering", {}).get("n_clusters", "?")
        headline_count = r.get("headline_topics_count", 0)
        elapsed = r.get("elapsed_sec", 0)

        icon = "✅" if status == "success" else "❌"

        fields.append({
            "name": f"{icon} {cat}",
            "value": (
                f"기사 {collected}건\n"
                f"{n_clusters}클러스터 / 헤드라인 {headline_count}\n"
                f"⏱️ {format_elapsed(elapsed)}"
            ),
            "inline": True,
        })

    if briefing_result:
        b_status = briefing_result.get("status", "?")
        b_slot = briefing_result.get("time_slot", "?")
        b_script = briefing_result.get("script_length", 0)
        b_audio = briefing_result.get("audio", "skipped")
        b_elapsed = briefing_result.get("elapsed_sec", 0)
        b_title = briefing_result.get("title")

        # status=success 라도 audio=failed 면 부분 실패 — alerts 채널에서 한눈에 보이도록 ⚠️
        audio_failed = b_audio == "failed"
        if b_status == "success":
            b_icon = "⚠️" if audio_failed else "✅"
        else:
            b_icon = "❌"
        audio_icon = "🎧" if b_audio not in ("skipped", "failed", None) else "📝"

        value_lines = [b_status]
        if b_title:
            # Discord field value 는 1024자 제한 — 제목은 길어도 150자로 컷
            title_preview = b_title if len(b_title) <= 150 else b_title[:147] + "..."
            value_lines.append(f"_{title_preview}_")
        value_lines.append(f"대본 {b_script}자 {audio_icon}")
        value_lines.append(format_elapsed(b_elapsed))

        fields.append({
            "name": f"{b_icon} 통합 브리핑 ({b_slot})",
            "value": "\n".join(value_lines),
            "inline": False,  # 제목이 들어가므로 줄바꿈 여유 있게 풀폭
        })

    total_time = sum(r.get("elapsed_sec", 0) for r in feed_results)
    if briefing_result:
        total_time += briefing_result.get("elapsed_sec", 0)

    slot_label = briefing_result.get("time_slot") if briefing_result else None
    title = (
        f"📻 Briefly {slot_label} 파이프라인 완료"
        if slot_label
        else "📻 Briefly 파이프라인 완료"
    )

    send_discord(
        message=(
            f"**⏱️ 총 소요시간**: {format_elapsed(total_time)}\n"
            f"Feed {len(feed_results)}개 카테고리 + 통합 브리핑 처리 완료"
        ),
        color=0x00FF00,
        title=title,
        fields=fields,
    )


def notify_pipeline_error(category: str, error: str):
    """에러 알림 → alerts."""
    send_discord(
        message=f"**카테고리**: {category}\n**에러**: ```{error[:500]}```",
        color=0xFF0000,
        title="🚨 Briefly 파이프라인 오류",
    )


def notify_auth_failure():
    """인증 만료 알림 → alerts."""
    send_discord(
        message="NotebookLM 인증 자동 갱신 실패.\n대본은 저장되지만 오디오 미생성.\n`notebooklm login` 수동 실행 필요.",
        color=0xFFAA00,
        title="⚠️ NotebookLM 인증 만료",
    )


def notify_missing_pub_rate(
    category_ko: str,
    missing: int,
    total: int,
    rate: float,
) -> bool:
    """`published_at` 결측 비율이 임계치 초과 시 alerts 로 경고.

    네이버 상세 페이지의 `data-date-time` 속성 파싱이 대량 실패하면 이 경고가
    뜹니다. 주로 네이버 HTML 구조 변경 신호 — 수집 파이프라인 조정 필요.
    """
    return send_discord(
        message=(
            f"**카테고리**: {category_ko}\n"
            f"**published_at 결측 비율**: {rate:.1%} "
            f"({missing}/{total} 건)\n"
            "네이버 상세페이지 날짜 파싱이 대량 실패했습니다. "
            "`naver_news_service._parse_kst_datetime` 와 "
            "`date-date-time` 속성 추출 로직 점검 필요."
        ),
        color=0xFFAA00,
        title="⚠️ published_at 결측률 임계치 초과",
    )


# ──────────────────────────────────────────────
# #briefly-pipeline (단계별 진행 로그)
# ──────────────────────────────────────────────

def log_step(category: str, step: str, detail: str = "", color: int = 0x3498DB) -> bool:
    """파이프라인 단계 로그 → pipeline 채널.

    동작:
      - "시작" 으로 끝나는 step 은 webhook 을 보내지 않고 타이머만 기록한다.
        (Discord 채널에는 완료/실패 이벤트만 남도록.)
      - "완료" / "실패" / "❌" 가 포함된 step 은 같은 (category, step-prefix) 의
        시작 시각을 빼내서 elapsed 시간을 메시지 끝에 자동 첨부한다.
        예) "**[정치]** 1️⃣ 뉴스 수집 완료: 200건 (12.3초)"
    """
    prefix = _extract_step_prefix(step)
    key = f"{category}|{prefix}" if prefix else f"{category}|_"

    # 시작 단계: webhook 미전송, 타이머만 기록.
    if step.rstrip().endswith("시작"):
        _STEP_TIMERS[key] = time.time()
        return True

    # 완료/실패: 타이머 정산 후 elapsed 첨부.
    elapsed_str = ""
    t0 = _STEP_TIMERS.pop(key, None)
    if t0 is not None and (("완료" in step) or ("실패" in step) or ("❌" in step)):
        elapsed_str = f" ({_format_elapsed(time.time() - t0)})"

    msg = f"**[{category}]** {step}{elapsed_str}"
    if detail:
        msg += f"\n{detail}"
    return _send(_get_pipeline_webhook(), msg, color=color)
