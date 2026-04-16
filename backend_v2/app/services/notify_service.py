"""
알림 서비스 (Discord 웹훅 2채널)

#briefly-alerts:    최종 결과, 에러, 인증 경고 (하루 2건)
#briefly-pipeline:  단계별 진행 로그 (카테고리당 8~10건)

환경변수:
    DISCORD_WEBHOOK_URL           — alerts 채널
    DISCORD_PIPELINE_WEBHOOK_URL  — pipeline 채널
"""

import os
import logging
from typing import List

import httpx

logger = logging.getLogger(__name__)


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


def notify_pipeline_success(results: list):
    """파이프라인 완료 알림 → alerts."""
    fields = []
    for r in results:
        cat = r.get("category", "?")
        status = r.get("status", "?")
        collected = r.get("collected", 0)
        topics = r.get("topics", 0)
        script_len = r.get("script_length", 0)
        podcast = r.get("podcast", "skipped")
        elapsed = r.get("elapsed_sec", 0)

        icon = "✅" if status == "success" else "❌"
        audio = "🎧" if podcast not in ("skipped", "failed", None) else "📝"

        fields.append({
            "name": f"{icon} {cat}",
            "value": f"기사 {collected}건 → {topics}토픽\n대본 {script_len}자 {audio}\n{elapsed:.0f}초",
            "inline": True,
        })

    total_time = sum(r.get("elapsed_sec", 0) for r in results)
    send_discord(
        message=f"총 {len(results)}개 카테고리 처리 완료 ({total_time:.0f}초)",
        color=0x00FF00,
        title="📻 Briefly 파이프라인 완료",
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


# ──────────────────────────────────────────────
# #briefly-pipeline (단계별 진행 로그)
# ──────────────────────────────────────────────

def log_step(category: str, step: str, detail: str = "", color: int = 0x3498DB) -> bool:
    """파이프라인 단계 로그 → pipeline 채널."""
    msg = f"**[{category}]** {step}"
    if detail:
        msg += f"\n{detail}"
    return _send(_get_pipeline_webhook(), msg, color=color)
