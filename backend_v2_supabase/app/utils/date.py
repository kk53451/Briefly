"""날짜 유틸리티 (KST 기준)"""

from datetime import datetime
from typing import Optional, Union
import pytz

KST = pytz.timezone("Asia/Seoul")


def get_today_kst() -> str:
    """오늘 날짜를 KST 기준 YYYY-MM-DD 형식으로 반환"""
    return datetime.now(KST).strftime("%Y-%m-%d")


def format_briefing_date_kr(date: Optional[Union[str, datetime]] = None) -> str:
    """브리핑 오프닝에서 낭독할 한국어 날짜 표기를 반환합니다.

    예: 2026-04-27 → "2026년 4월 27일"
    NotebookLM TTS 가 자연스럽게 "이천이십육년 사월 이십칠일" 로 발음할 수 있게
    leading zero 없이 자릿수만 표기합니다.

    Args:
        date: "YYYY-MM-DD" 문자열 또는 datetime. None 이면 오늘(KST).
    """
    if date is None:
        dt = datetime.now(KST)
    elif isinstance(date, str):
        dt = datetime.strptime(date, "%Y-%m-%d")
    else:
        dt = date
    return f"{dt.year}년 {dt.month}월 {dt.day}일"


def get_now_kst() -> datetime:
    """현재 시각을 KST 기준으로 반환"""
    return datetime.now(KST)


def get_briefing_slot(now: Optional[datetime] = None) -> str:
    """
    현재 시각(KST)을 기준으로 데일리 브리핑 슬롯을 반환합니다.

    Briefly는 하루 두 번(07:00 / 18:00 KST) 자동 생성되므로, 정오 이전은
    "오전", 정오 이후는 "오후" 브리핑으로 라벨링합니다. 팟캐스트 제목,
    오프닝/클로징 멘트에 사용됩니다.

    Args:
        now: 명시적으로 기준 시각을 지정하고 싶을 때 (테스트용).
             None 이면 현재 KST 시각을 사용합니다.

    Returns:
        "오전" 또는 "오후"
    """
    if now is None:
        now = get_now_kst()
    elif now.tzinfo is None:
        now = KST.localize(now)
    else:
        now = now.astimezone(KST)

    return "오전" if now.hour < 12 else "오후"
