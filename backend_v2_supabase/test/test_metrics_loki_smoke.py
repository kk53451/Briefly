"""
Grafana Loki 계측 스모크 테스트

전체 파이프라인(20~40분, NotebookLM 포함)을 돌리지 않고 계측 경로만 검증합니다.

**실제 notify_service 함수를 그대로 호출**합니다. metrics_service 를 직접 찌르지
않는 이유: 검증하려는 건 push 함수가 아니라 "notify_service 훅이 제대로 걸렸는가"
이기 때문입니다. Discord 웹훅만 비워서 알림은 안 나가게 합니다.

전송 성공(2xx)만으로 통과 처리하지 **않습니다**. Loki 는 빈 `{"streams": []}` 도
204 로 받아주기 때문에, 클라이언트가 실제로 아무것도 안 보내도 성공처럼 보입니다
(실제로 이 함정에 한 번 빠졌습니다). 그래서 마지막에 Loki 를 되읽어서 기대한
이벤트가 전부 조회되는지까지 확인합니다.

데이터는 env="smoke" 라벨로 들어가므로 실제 실행 데이터(env="prod")와 섞이지
않습니다.

실행:
    cd backend_v2_supabase
    python -m test.test_metrics_loki_smoke
"""

import os
import sys
import time
from typing import Dict

import httpx
from dotenv import load_dotenv

# Windows 콘솔 기본 코덱(cp949)은 이모지를 못 찍어서 UnicodeEncodeError 로 죽습니다.
# 개발은 Windows, 운영은 Ubuntu 라 양쪽 모두에서 안전하게 UTF-8 로 고정합니다.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

load_dotenv()

# load_dotenv() 이후에 덮어써야 .env 값이 다시 들어오지 않습니다.
os.environ["GRAFANA_LOKI_ENV"] = "smoke"
os.environ["DISCORD_WEBHOOK_URL"] = ""
os.environ["DISCORD_PIPELINE_WEBHOOK_URL"] = ""

from app.services import metrics_service
from app.services.notify_service import (
    log_step,
    notify_pipeline_success,
    notify_pipeline_error,
    notify_auth_failure,
    notify_missing_pub_rate,
)

# 훅이 실제로 내보내야 하는 이벤트 종류. 하나라도 빠지면 훅이 끊긴 것입니다.
EXPECTED_EVENTS = {
    "step",
    "feed_summary",
    "briefing_summary",
    "run_summary",
    "error",
    "auth_failure",
    "missing_pub_rate",
}


def _fake_feed_result(category_ko: str, elapsed: float, collected: int) -> dict:
    """scheduler.process_category_feed() 반환 구조를 그대로 흉내냅니다."""
    return {
        "category": category_ko,
        "category_en": "smoke",
        "status": "success",
        "collected": collected,
        "after_dedup": collected - 12,
        "clustering": {
            "n_clusters": 14,
            "noise_ratio": 0.18,
            "max_cluster_size": 9,
            "mcs": 3,
            "umap_dim": 5,
            "attempt": 1,
        },
        "ranked_topics_total": 14,
        "headline_topics_count": 5,
        "news_cards_saved": 20,
        "elapsed_sec": elapsed,
        "window_stats": {
            "total_collected": collected + 30,
            "kept": collected,
            "dropped_outside": 30,
            "missing_pub": 2,
        },
    }


def _read_back(since_ns: int, attempts: int = 6, delay: float = 2.0) -> Dict[str, int]:
    """push 한 데이터를 Loki 에서 되읽어 이벤트 종류별 건수를 셉니다.

    인제스트 직후에는 조회가 안 될 수 있어 몇 초 간격으로 재시도합니다.

    Returns:
        {이벤트명: 라인수}. 조회 실패 또는 결과 없음이면 빈 dict.
    """
    url = os.getenv("GRAFANA_LOKI_URL", "").strip().rstrip("/")
    user = os.getenv("GRAFANA_LOKI_USER", "").strip()
    token = os.getenv("GRAFANA_LOKI_TOKEN", "").strip()

    for i in range(attempts):
        time.sleep(delay)
        try:
            resp = httpx.get(
                f"{url}/loki/api/v1/query_range",
                params={
                    "query": '{job="briefly", env="smoke"}',
                    "start": str(since_ns),
                    "end": str(time.time_ns()),
                    "limit": "500",
                },
                auth=(user, token),
                timeout=15.0,
            )
            resp.raise_for_status()
            counts: Dict[str, int] = {}
            for stream in resp.json()["data"]["result"]:
                event = stream["stream"].get("event", "?")
                counts[event] = counts.get(event, 0) + len(stream["values"])
            if counts:
                return counts
            print(f"   조회 재시도 {i + 1}/{attempts} — 아직 안 보임")
        except Exception as e:
            print(f"   조회 재시도 {i + 1}/{attempts} — {e}")
    return {}


def main() -> int:
    print("=" * 60)
    print("  Grafana Loki 계측 스모크 테스트")
    print("=" * 60)

    if not metrics_service.is_enabled():
        print("\n❌ 계측 비활성 — .env 에 아래 3개가 필요합니다:")
        print("     GRAFANA_LOKI_URL   (Loki 엔드포인트)")
        print("     GRAFANA_LOKI_USER  (숫자 user id)")
        print("     GRAFANA_LOKI_TOKEN (glc_ 로 시작하는 Access Policy 토큰)")
        return 1

    print(f"\n✅ 계측 활성 — {os.getenv('GRAFANA_LOKI_URL')}")
    print(f"   env 라벨: {os.environ['GRAFANA_LOKI_ENV']} (실 데이터와 분리됨)")

    since_ns = time.time_ns()

    # ── 1. 단계별 타이밍 (log_step 시작/완료 쌍) ──
    print("\n[1/5] 단계별 타이밍 — log_step 시작→완료 쌍")
    for cat, step_start, step_done, delay in [
        ("정치", "1️⃣ 뉴스 수집 시작", "1️⃣ 수집 완료: 180건", 0.25),
        ("정치", "2️⃣ 임베딩 시작", "2️⃣ 임베딩 완료: (180, 1024)", 0.15),
        ("경제", "4️⃣ 클러스터링 시작", "4️⃣ 클러스터링 완료: 14개 클러스터", 0.35),
        ("경제", "6️⃣ 헤드라인 생성 시작", "❌ 6️⃣ 헤드라인 실패: CUDA OOM", 0.10),
    ]:
        log_step(cat, step_start)
        time.sleep(delay)
        log_step(cat, step_done)
        print(f"   {cat} — {step_done[:34]}")

    # ── 2. 실행 요약 (메인 훅) ──
    print("\n[2/5] 실행 요약 — notify_pipeline_success")
    feed_results = [
        _fake_feed_result("정치", 201.3, 180),
        _fake_feed_result("경제", 188.7, 165),
        _fake_feed_result("국제", 176.2, 143),
    ]
    feed_results.append({
        "category": "문화",
        "status": "failed",
        "collected": 0,
        "elapsed_sec": 12.4,
        "error": "smoke test 유도 실패",
    })
    notify_pipeline_success(
        feed_results,
        briefing_result={
            "stage": "briefing",
            "time_slot": "오전",
            "slot": "AM",
            "status": "success",
            "script_length": 7412,
            "audio": "outputs/audio/smoke.mp3",
            "duration_sec": 566,
            "elapsed_sec": 903.5,
            "categories": ["정치", "경제", "국제"],
        },
    )
    print(f"   feed {len(feed_results)}건 + briefing + run_summary")

    # ── 3. 에러 / 경고 ──
    print("\n[3/5] 에러·경고 — error / auth_failure / missing_pub_rate")
    notify_pipeline_error("문화", "smoke test 유도 실패: ConnectionResetError")
    notify_auth_failure()
    notify_missing_pub_rate("사회", missing=23, total=150, rate=23 / 150)
    print("   3건")

    # ── 4. flush ──
    print("\n[4/5] flush")
    if not metrics_service.flush():
        print("   ❌ 전송 실패 — 위 WARNING 로그의 상태코드를 확인하세요.")
        print("      401/403 → 토큰 또는 user id 오류")
        print("      404     → GRAFANA_LOKI_URL 오류")
        return 1
    print("   ✅ 전송 성공 (2xx) — 단, 이것만으로는 부족하므로 되읽어 확인합니다")

    # ── 5. 되읽기 검증 ──
    # 여기가 진짜 검증입니다. Loki 는 빈 streams 도 204 로 받아주므로 2xx 만
    # 보고 통과시키면 "아무것도 안 보냈는데 성공" 을 못 잡습니다.
    print("\n[5/5] 되읽기 검증 — Loki 에서 실제 조회")
    counts = _read_back(since_ns)
    if not counts:
        print("\n❌ 전송은 2xx 인데 조회 결과가 없습니다.")
        print("   → 빈 payload 를 보냈거나, 다른 테넌트로 들어갔을 가능성.")
        return 1

    for event in sorted(counts):
        print(f"   {event}: {counts[event]}건")

    missing = EXPECTED_EVENTS - set(counts)
    if missing:
        print(f"\n❌ 누락된 이벤트: {sorted(missing)}")
        print("   → 해당 notify_service 훅이 끊겼습니다.")
        return 1

    total = sum(counts.values())
    print(f"\n✅ 기대 이벤트 {len(EXPECTED_EVENTS)}종 전부 확인 (총 {total}건)")
    print("=" * 60)
    print('  Grafana Explore:  {job="briefly", env="smoke"}')
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
