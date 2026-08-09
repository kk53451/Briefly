"""
Grafana Cloud Loki 메트릭 푸시

Discord 알림과 **병행**해서 동작합니다. 역할이 다릅니다:
    Discord — 즉시 알림. 사람이 읽는다.
    Loki    — 시계열 축적. "어제보다 느려졌나 / 수집량 줄었나 / 어디가 자주 깨지나".

Prometheus 가 아니라 Loki 를 쓰는 이유: 이 파이프라인은 cron 배치라 실행마다
프로세스가 새로 뜬다. Prometheus 카운터는 매번 0 으로 리셋돼서 "카테고리별 실패
횟수" 같은 누적 질문에 못 답한다. Loki 는 이벤트를 세는 방식이라 그 문제가 없고,
에러 원문까지 같이 보존된다. 숫자 추세는 LogQL `unwrap` 으로 뽑는다:

    avg_over_time({job="briefly"} | json | unwrap elapsed_sec [1d]) by (category)

환경변수 (backend_v2_supabase/.env):
    GRAFANA_LOKI_URL    — https://logs-prod-XXX.grafana.net
    GRAFANA_LOKI_USER   — 숫자 user id
    GRAFANA_LOKI_TOKEN  — glc_ 로 시작하는 Cloud Access Policy 토큰

셋 중 하나라도 비어 있으면 **조용히 no-op** 합니다. 전송 실패도 절대 파이프라인을
죽이지 않습니다 (notify_service._send 와 같은 철학).
"""

import os
import json
import time
import atexit
import logging
import threading
from typing import Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# 라벨 정규화
# ──────────────────────────────────────────────
# Loki 라벨은 ASCII 로 유지합니다. 한글 라벨도 저장은 되지만 LogQL 을 손으로 짤 때
# 번거롭고, Grafana 변수/정규식에서 인코딩 문제가 생기기 쉽습니다.

_CATEGORY_LABELS = {
    "정치": "politics",
    "경제": "economy",
    "사회": "society",
    "문화": "culture",
    "국제": "international",
    "IT/과학": "tech",
}

# notify_service._extract_step_prefix 가 뽑아내는 prefix → ASCII step 라벨.
# 숫자 이모지가 있으면 그걸, 없으면 첫 토큰(대개 이모지 하나)이 넘어옵니다.
_STEP_LABELS = {
    "1️⃣": "collect",
    "2️⃣": "embed",
    "3️⃣": "dedup",
    "4️⃣": "cluster",
    "5️⃣": "rank",
    "5️⃣-b": "newscards",
    "6️⃣": "headline",
    "7️⃣": "pool",
    "📥": "prefetch",
    "📝": "script",
    "🎧": "audio",
    "💾": "storage",
    "🎬": "briefing_start",
    "🚀": "pipeline_start",
    "🏁": "phase_done",
}


def category_label(category_ko: str) -> Tuple[str, Optional[str]]:
    """한글 카테고리 문자열 → (category 라벨, slot 라벨 or None).

    log_step 의 첫 인자는 실제 카테고리("정치")뿐 아니라 "PREFETCH" 나
    "통합브리핑#오전" 같은 의사(pseudo) 카테고리도 들어옵니다. 후자는 슬롯 정보가
    문자열에 섞여 있으므로 분리해서 별도 라벨로 뺍니다 — 안 그러면 category 라벨이
    슬롯마다 갈라져 카디널리티가 두 배가 됩니다.
    """
    if category_ko in _CATEGORY_LABELS:
        return _CATEGORY_LABELS[category_ko], None
    if category_ko == "PREFETCH":
        return "prefetch", None
    if category_ko.startswith("통합브리핑"):
        slot = None
        if "오전" in category_ko:
            slot = "AM"
        elif "오후" in category_ko:
            slot = "PM"
        return "briefing", slot
    return "pipeline", None


def step_label(step_prefix: str) -> str:
    """notify_service 가 뽑은 step prefix → ASCII step 라벨."""
    return _STEP_LABELS.get(step_prefix, "other")


# ──────────────────────────────────────────────
# 버퍼
# ──────────────────────────────────────────────
# 이벤트마다 HTTP POST 하면 단계별 계측 기준 실행당 100건 넘게 왕복합니다
# (건당 100~300ms → 최대 30초 낭비). 버퍼에 모았다가 한 번에 밀어넣습니다.
# 프로세스가 중간에 죽어도 유실이 최소가 되도록 임계치는 낮게 잡고,
# 정상 종료 시에는 atexit 이 남은 것을 비웁니다.

_FLUSH_THRESHOLD = 25
_HTTP_TIMEOUT = 10.0

# (정렬된 라벨 튜플) → [(unix_nano 문자열, 로그 라인)]
_buffer: Dict[Tuple[Tuple[str, str], ...], List[Tuple[str, str]]] = {}
_lock = threading.Lock()


def _config() -> Optional[Tuple[str, str, str]]:
    """(url, user, token). 하나라도 없으면 None → 전체 no-op."""
    url = os.getenv("GRAFANA_LOKI_URL", "").strip().rstrip("/")
    user = os.getenv("GRAFANA_LOKI_USER", "").strip()
    token = os.getenv("GRAFANA_LOKI_TOKEN", "").strip()
    if not (url and user and token):
        return None
    return url, user, token


def is_enabled() -> bool:
    """계측이 켜져 있는지. 스모크 테스트/진단용."""
    return _config() is not None


def push(
    event: str,
    category: str = "pipeline",
    status: str = "info",
    step: Optional[str] = None,
    slot: Optional[str] = None,
    **fields,
) -> None:
    """이벤트 하나를 버퍼에 넣습니다. 임계치를 넘으면 자동 flush.

    Args:
        event:    이벤트 종류 라벨 (feed_summary / briefing_summary / step / error ...)
        category: ASCII 카테고리 라벨 (category_label() 결과)
        status:   success / failed / skipped / warning / info
        step:     ASCII step 라벨 (단계별 계측일 때만)
        slot:     AM / PM
        **fields: 로그 라인에 JSON 으로 실릴 숫자·문자 필드.
                  숫자 필드가 나중에 `unwrap` 대상이 됩니다.

    예외를 밖으로 내보내지 않습니다.
    """
    if _config() is None:
        return

    try:
        labels = {
            "job": "briefly",
            # 스모크 테스트가 실제 실행 데이터와 섞이면 대시보드 추세가 오염됩니다.
            # 테스트는 GRAFANA_LOKI_ENV=smoke 로 돌리고, 대시보드는 env="prod" 만
            # 봅니다. 값이 2개뿐이라 카디널리티 부담은 없습니다.
            "env": os.getenv("GRAFANA_LOKI_ENV", "prod"),
            "event": event,
            "category": category,
            "status": status,
        }
        if step:
            labels["step"] = step
        if slot:
            labels["slot"] = slot

        # None 필드는 제거 — 로그 라인이 짧아지고, `unwrap` 대상 필드가 있는
        # 샘플만 남아서 쿼리 결과가 명확해집니다.
        payload = {k: v for k, v in fields.items() if v is not None}
        line = json.dumps(payload, ensure_ascii=False, default=str)
        ts_nano = str(time.time_ns())
        key = tuple(sorted(labels.items()))

        with _lock:
            _buffer.setdefault(key, []).append((ts_nano, line))
            total = sum(len(v) for v in _buffer.values())

        if total >= _FLUSH_THRESHOLD:
            flush()
    except Exception as e:
        logger.debug(f"Loki push 버퍼링 실패 (무시): {e}")


def flush() -> bool:
    """버퍼에 쌓인 것을 Loki 로 전송합니다.

    Returns:
        True  — 전송 성공, 또는 보낼 게 없음
        False — 전송 실패 (버퍼는 비워짐. 재시도하지 않습니다 — 관측 데이터를
                살리려다 파이프라인을 지연시키는 게 더 나쁩니다.)
    """
    global _buffer

    cfg = _config()
    if cfg is None:
        return True

    url, user, token = cfg

    with _lock:
        if not _buffer:
            return True
        # 반드시 **새 dict 로 교체**해야 합니다. `pending = _buffer` 후
        # `_buffer.clear()` 를 하면 같은 객체를 가리키므로 pending 까지 비어서
        # 빈 payload 가 전송됩니다 (Loki 는 빈 streams 도 204 로 받아주기 때문에
        # 조용히 성공한 것처럼 보입니다).
        pending = _buffer
        _buffer = {}

    try:
        streams = []
        for key, values in pending.items():
            # Loki 는 같은 스트림 안에서 타임스탬프 오름차순을 요구합니다
            # (최신 버전은 out-of-order 를 허용하지만 의존하지 않습니다).
            # 서로 다른 스트림끼리는 무관합니다.
            values.sort(key=lambda v: int(v[0]))
            streams.append({
                "stream": dict(key),
                "values": [[ts, line] for ts, line in values],
            })

        with httpx.Client(timeout=_HTTP_TIMEOUT) as client:
            resp = client.post(
                f"{url}/loki/api/v1/push",
                json={"streams": streams},
                auth=(user, token),
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()

        count = sum(len(v) for v in pending.values())
        logger.debug(f"Loki flush 완료: {count}건 / {len(streams)}스트림")
        return True
    except Exception as e:
        # 본문에 원인이 담기는 경우가 많아 (429 rate limit, 400 라벨 오류 등)
        # 같이 남깁니다. WARNING 인 이유: 파이프라인은 계속 돌아야 하지만
        # 관측이 조용히 죽는 건 알아차릴 수 있어야 합니다.
        detail = ""
        if isinstance(e, httpx.HTTPStatusError):
            detail = f" — {e.response.status_code}: {e.response.text[:200]}"
        logger.warning(f"Loki 전송 실패 (파이프라인은 계속 진행){detail}: {e}")
        return False


# 정상 종료 시 남은 버퍼 비우기. cron 배치라 프로세스 종료가 곧 실행 종료입니다.
atexit.register(flush)
