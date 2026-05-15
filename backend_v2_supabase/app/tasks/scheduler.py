"""
Briefly v2 로컬 파이프라인 스케줄러

Ubuntu 노트북에서 cron으로 실행 (오전 05:00, 오후 16:00 KST 권장).

통합 브리핑 리워크(2026-04-19) 이후의 구조:

[Feed Phase — 6개 카테고리 전부]
  뉴스 수집 → 임베딩 → 중복 제거 → 클러스터링 → 토픽 랭킹
  → NewsCards 저장 (Home/Today 탭용, rank 1~20)
  → 헤드라인 생성/저장 (top 5)
  → 하드뉴스(정치·경제·국제) 한정으로 토픽별 비례 배분 풀 추가 구성

[Briefing Phase — 하루 1회, 이번 time_slot 에 대해]
  3개 하드뉴스 카테고리의 top K 토픽을 엮어 단일 통합 대본 생성
  → NotebookLM 으로 8~10분 오디오 생성
  → podcasts 테이블 (UNIQUE date, slot) 에 1행으로 저장

사용법:
    # 기본: 현재 KST 시각 기준 오전/오후 자동 판정
    python -m app.tasks.scheduler

    # 명시적 time-slot 지정
    python -m app.tasks.scheduler --time-slot morning
    python -m app.tasks.scheduler --time-slot afternoon

    # 특정 카테고리만 (feed 단계 한정)
    python -m app.tasks.scheduler --categories economy politics

    # 팟캐스트 생성 제외 (수집+feed 만, 대본/오디오 생략)
    python -m app.tasks.scheduler --skip-podcast

cron 등록 (Ubuntu):
    crontab -e
    0 5  * * * cd /home/user/Briefly/backend_v2_supabase && /usr/bin/python3 -m app.tasks.scheduler --time-slot morning   >> /var/log/briefly.log 2>&1
    0 16 * * * cd /home/user/Briefly/backend_v2_supabase && /usr/bin/python3 -m app.tasks.scheduler --time-slot afternoon >> /var/log/briefly.log 2>&1
"""

import os
import sys
import json
import time
import logging
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Set, Tuple

import pytz
from dotenv import load_dotenv
load_dotenv()

_KST = pytz.timezone("Asia/Seoul")

from app.constants.category_map import CATEGORY_MAP
from app.services.naver_news_service import NaverNewsService
from app.services.embedding_service import embed_articles
from app.services.clustering_service import (
    remove_near_duplicates,
    cluster_articles,
    rank_topics,
    build_topic_weighted_pool,
)
from app.services.script_service import generate_script
from app.utils.date import get_today_kst, get_now_kst, get_briefing_slot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# httpx·hpack·httpcore 의 per-request INFO 로그는 파이프라인 로그 7천 줄 중
# 절반 이상을 차지해 가독성을 해쳤음 (Discord 웹훅·Naver fetch·Supabase 호출 전부
# POST/GET 라인 찍음). WARNING 으로 올려서 실질적 오류만 찍히게 함. 필요 시
# 디버깅할 때 일시적으로 낮추면 됨.
for _noisy in ("httpx", "httpcore", "hpack", "urllib3"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)


# ──────────────────────────────────────────────
# 통합 브리핑 상수
# ──────────────────────────────────────────────

# 팟캐스트에 들어가는 하드뉴스 3종 (순서 고정: 정치 → 경제 → 국제).
# 나머지 카테고리(사회·문화·IT/과학)는 feed 단계만 수행하고 팟캐스트에는 미포함.
HARD_NEWS_CATEGORIES_KO: List[str] = ["정치", "경제", "국제"]

# 통합 브리핑 회차당 카테고리별 topic 수. 3분야 × 4토픽 = 12 토픽, ~40초/토픽.
# 2026-04-20 실측: SHORT + 3토픽/분야 = 6분 8초 (맥락 부족). 4토픽/분야로 확장해
# 대본 밀도·분량 동시 확보 (Plan A).
PODCAST_TOPICS_PER_CATEGORY: int = 4

# NotebookLM 에 같이 전달할 REF 소스 — 토픽당 대표 기사 수.
# 3분야 × PODCAST_TOPICS_PER_CATEGORY 토픽 × 이 값 = 총 REF 건수 (현재 36건).
PODCAST_REF_ARTICLES_PER_TOPIC: int = 3

# 통합 브리핑 대본 목표 글자 수 (generate_script target_length 기본값과 일치).
# 2026-04-20 실측: 4999자 대본 + SHORT = 6분 8초 (하한 미달). 자/분 비율(~816자/분)
# 기준 7500~8000자 대본이면 SHORT 모드에서 9~10분 수렴 기대 (Plan A).
BRIEFING_TARGET_LENGTH: int = 7500

# 시간 윈도우 기본값 (KST hour). 오전: 전날 18 ~ 당일 05, 오후: 당일 05 ~ 16.
MORNING_WINDOW_START_HOUR: int = 18  # 전날
MORNING_WINDOW_END_HOUR: int = 5     # 당일
AFTERNOON_WINDOW_START_HOUR: int = 5   # 당일
AFTERNOON_WINDOW_END_HOUR: int = 16    # 당일

# 윈도우 내 기사가 이 임계치 미만이면 fallback 으로 윈도우 시작점을 backward 확장.
WINDOW_MIN_ARTICLES: int = 10
WINDOW_FALLBACK_EXTEND_HOURS: int = 3

# 시간 윈도우 자체의 ON/OFF 스위치.
# 출시 전 단계(2026-04-27)에서는 임의 시각에 파이프라인을 돌려도 충분한 기사를 확보할 수
# 있어야 하므로 비활성화. 윈도우 OFF 시 `collect_category_for_window` 대신 네이버 "오늘
# 카테고리 리스트" 전체를 그대로 받아옵니다 (published_at 필터 없음). 출시 후 윈도우
# 기반 수집으로 돌리려면 이 플래그를 True 로.
BRIEFING_WINDOW_ENABLED: bool = False

# previous-topics 중복 제거: 최근 이 시간 내 저장된 팟캐스트들의 covered_keywords 를 참조.
DEDUP_LOOKBACK_HOURS: int = 24

# 토픽의 키워드 집합이 직전 팟캐스트의 어떤 집합과 이만큼 겹치면 중복으로 판정.
DEDUP_KEYWORD_OVERLAP_THRESHOLD: int = 2

# 토픽의 top 키워드 몇 개를 covered_keywords 로 저장 / dedup 비교할지.
DEDUP_KEYWORDS_PER_TOPIC: int = 3

# published_at 결측률이 이 임계치를 넘기면 alerts 채널에 경고 (네이버 HTML 구조 변경 감지).
PUB_MISSING_RATE_ALERT_THRESHOLD: float = 0.10

# Feed 단계 수집(네이버 상세페이지 스크래핑) 병렬도. I/O-bound 이라 threading 유효.
# 임베딩·클러스터링은 KURE GPU 메모리 공유 때문에 순차 유지 — 수집만 병렬.
# 카테고리가 6개이므로 6 으로 올리면 카테고리당 worker 1개 = 자연스러운 상한.
# 카테고리 워커 안에서는 request_delay=0.2s 직렬 호출 → 카테고리당 ~5 QPS,
# 6 워커 동시 = ~30 QPS. 네이버 카테고리 페이지에 안전한 수준.
# 그 이상 (예: request_delay 단축) 으로 가려면 rate-limit 모니터링 필요.
COLLECT_PARALLELISM: int = 6


def _slot_label(time_slot_ko: str) -> str:
    """'오전'/'오후' → 'AM'/'PM' (storage key 용)"""
    return "AM" if time_slot_ko == "오전" else "PM"


def _resolve_time_slot(cli_value: Optional[str]) -> str:
    """CLI --time-slot 값을 한글 time_slot('오전'|'오후')으로 정규화."""
    if cli_value is None:
        slot_ko = get_briefing_slot()
        logger.info(f"  time_slot 자동 판정: {slot_ko} (KST {get_now_kst().strftime('%H:%M')})")
        return slot_ko

    normalized = cli_value.strip().lower()
    if normalized in ("morning", "am", "오전"):
        return "오전"
    if normalized in ("afternoon", "evening", "pm", "오후"):
        return "오후"
    raise ValueError(
        f"--time-slot 값이 잘못됐습니다: {cli_value!r}. "
        "허용 값: morning | afternoon (또는 오전 | 오후)"
    )


def compute_time_window(
    time_slot_ko: str,
    now: Optional[datetime] = None,
) -> Tuple[datetime, datetime]:
    """time_slot 으로부터 기사 수집 윈도우(KST tz-aware)를 계산합니다.

    오전 05:05 KST 실행 → 윈도우 = 전날 18:00 ~ 당일 05:00
    오후 16:05 KST 실행 → 윈도우 = 당일 05:00 ~ 당일 16:00

    Args:
        time_slot_ko: "오전" 또는 "오후"
        now: 현재 시각 기준. None 이면 KST now.

    Returns:
        (window_start, window_end) — 둘 다 KST tz-aware datetime. end 는 exclusive.
    """
    base = (now or get_now_kst()).astimezone(_KST)
    today = base.date()
    yesterday = today - timedelta(days=1)

    if time_slot_ko == "오전":
        start = _KST.localize(datetime(
            yesterday.year, yesterday.month, yesterday.day,
            MORNING_WINDOW_START_HOUR, 0, 0,
        ))
        end = _KST.localize(datetime(
            today.year, today.month, today.day,
            MORNING_WINDOW_END_HOUR, 0, 0,
        ))
    else:  # 오후
        start = _KST.localize(datetime(
            today.year, today.month, today.day,
            AFTERNOON_WINDOW_START_HOUR, 0, 0,
        ))
        end = _KST.localize(datetime(
            today.year, today.month, today.day,
            AFTERNOON_WINDOW_END_HOUR, 0, 0,
        ))
    return start, end


def topic_keyword_set(topic: dict, top_k: int = DEDUP_KEYWORDS_PER_TOPIC) -> Set[str]:
    """토픽 dict 에서 top_k 키워드를 set 으로 반환."""
    kws = topic.get("keywords") or []
    out: Set[str] = set()
    for item in kws[:top_k]:
        # clustering_service 는 (word, count) tuple 로 저장
        if isinstance(item, (list, tuple)) and item:
            out.add(str(item[0]))
        elif isinstance(item, str):
            out.add(item)
    return out


def is_topic_duplicate(
    topic: dict,
    prev_kw_sets: List[List[str]],
    threshold: int = DEDUP_KEYWORD_OVERLAP_THRESHOLD,
) -> bool:
    """토픽의 top 키워드 집합이 직전 팟캐스트 어느 한 토픽과 threshold 이상 겹치면 True."""
    current = topic_keyword_set(topic)
    if len(current) < threshold:
        return False
    for prev in prev_kw_sets:
        overlap = current & set(prev)
        if len(overlap) >= threshold:
            return True
    return False


def _build_briefing_title(ordered_hard_news: List[dict]) -> Optional[str]:
    """Gemma4 헤드라인을 재활용해 에피소드 title 을 구성합니다.

    각 하드뉴스 카테고리에서 **podcast_topics top 1 에 해당하는 Gemma4 헤드라인 1개**
    를 뽑아 쉼표로 연결. 추가 LLM 호출 없음.

    topics_with_headlines 는 headline_topics(top 5) 기준이라, podcast_topics top 1 과
    topic_id 로 매칭해서 해당 토픽의 헤드라인을 찾습니다.
    """
    parts: List[str] = []
    for r in ordered_hard_news:
        podcast_topics = r.get("podcast_topics") or []
        if not podcast_topics:
            continue
        lead_topic = podcast_topics[0]
        lead_topic_id = lead_topic.get("topic_id")

        headline = None
        for h in r.get("topics_with_headlines") or []:
            if h.get("topic_id") == lead_topic_id:
                headline = h.get("headline")
                break
        if not headline:
            # 헤드라인 매칭 실패 시 대표 기사 제목의 앞부분으로 폴백
            rep = lead_topic.get("representative_article", {})
            headline = (rep.get("title") or "")[:40]
        headline = (headline or "").strip()
        if headline:
            parts.append(headline)

    return ", ".join(parts) if parts else None


def _build_covered_keywords(ordered_hard_news: List[dict]) -> List[List[str]]:
    """이 에피소드에 실제 들어간 토픽들의 top 키워드 집합 리스트.

    각 카테고리 × podcast_topics 전부를 평탄화해 반환 — 다음 실행의 dedup 조회용.
    """
    out: List[List[str]] = []
    for r in ordered_hard_news:
        for topic in r.get("podcast_topics") or []:
            kws = sorted(topic_keyword_set(topic))
            if kws:
                out.append(kws)
    return out


# ──────────────────────────────────────────────
# 수집 (병렬 prefetch 지원)
# ──────────────────────────────────────────────

def _collect_with_window_fallback(
    news_service: "NaverNewsService",
    category_ko: str,
    window_start: datetime,
    window_end: datetime,
) -> Tuple[List[dict], dict, bool]:
    """단일 카테고리 수집 + fallback 확장. run_pipeline 의 병렬 prefetch 에서 호출.

    BRIEFING_WINDOW_ENABLED=False 일 때는 시간 윈도우 필터를 우회하고 네이버 "오늘
    카테고리 리스트" 를 그대로 사용합니다. 출시 전 단계용. 다운스트림 코드가
    win_stats 의 키를 참조하므로 윈도우 OFF 모드에서도 동일 형태 dict 를 반환합니다.

    Returns:
        (articles, window_stats, extended)
        extended=True 면 원 윈도우 부족으로 3h backward 확장 적용됨.
        윈도우 OFF 모드에서는 항상 extended=False.
    """
    if not BRIEFING_WINDOW_ENABLED:
        # 윈도우 OFF: 네이버 카테고리 페이지 그대로 (today 디폴트).
        articles = news_service.collect_category(category_ko=category_ko)
        today_key = get_now_kst().strftime("%Y%m%d")
        # window_start / window_end 는 호출자가 로깅/통계에 쓰므로 passthrough.
        stats = {
            "window_start": window_start.isoformat(),
            "window_end": window_end.isoformat(),
            "window_hours": round(
                (window_end - window_start).total_seconds() / 3600, 2
            ),
            "naver_date_list_keys": [today_key],
            "total_collected": len(articles),
            "kept": len(articles),
            "dropped_outside": 0,
            "missing_pub": 0,
            "window_disabled": True,
        }
        logger.info(
            f"  🚫 [{category_ko}] 시간 윈도우 비활성화 — "
            f"네이버 오늘 카테고리 리스트 {len(articles)}건 그대로 사용"
        )
        return articles, stats, False

    articles, stats = news_service.collect_category_for_window(
        category_ko=category_ko,
        window_start=window_start,
        window_end=window_end,
    )
    extended = False
    if len(articles) < WINDOW_MIN_ARTICLES:
        extended = True
        extended_start = window_start - timedelta(
            hours=WINDOW_FALLBACK_EXTEND_HOURS
        )
        logger.info(
            f"  [{category_ko}] 원 윈도우 {len(articles)}건 < "
            f"{WINDOW_MIN_ARTICLES} → {WINDOW_FALLBACK_EXTEND_HOURS}h 확장 "
            f"(병렬 prefetch)"
        )
        articles, stats = news_service.collect_category_for_window(
            category_ko=category_ko,
            window_start=extended_start,
            window_end=window_end,
        )
    return articles, stats, extended


# ──────────────────────────────────────────────
# Feed Phase (카테고리별)
# ──────────────────────────────────────────────

def process_category_feed(
    category_ko: str,
    config: dict,
    news_service: NaverNewsService,
    date_str: str,
    slot_str: str,
    window_start: datetime,
    window_end: datetime,
    prev_kw_sets: Optional[List[List[str]]] = None,
    prefetched: Optional[Tuple[List[dict], dict, bool]] = None,
) -> dict:
    """카테고리 하나에 대해 Feed 단계까지 실행합니다.

    수행: 윈도우 내 뉴스 수집 (부족 시 backward 확장)
         → 임베딩 → 중복제거 → 클러스터링 → 토픽 랭킹
         → NewsCards 저장 (rank 1~20) → 헤드라인 생성/저장 (top 5)
         → **하드뉴스 카테고리**에 한해 이전 팟캐스트 중복 제거 + 통합 브리핑용 풀(top K)

    팟캐스트(대본·오디오 생성)는 여기서 하지 않습니다.
    여러 카테고리 feed 결과를 모아 generate_integrated_briefing() 한 번으로 처리합니다.

    Args:
        window_start / window_end: 기사 `published_at` 필터 범위 (KST tz-aware, end exclusive)
        prev_kw_sets: 직전 팟캐스트들의 covered_keywords (dedup 기준). None 이면 dedup 스킵.

    Returns:
        feed 통계 + (하드뉴스면) podcast_topics / pool_articles / allocation_info
        + topics_with_headlines (title 생성용)
    """
    category_en = config["api_name"]
    t0 = time.time()

    result = {
        "category": category_ko,
        "category_en": category_en,
        "status": "started",
        # Briefing phase 에 넘길 필드. 하드뉴스가 아니거나 실패 시 None.
        "podcast_topics": None,
        "pool_articles": None,
        "allocation_info": None,
        "topics_with_headlines": None,  # title 생성 재료
    }

    try:
        from app.services.notify_service import log_step

        log_step(category_ko, "🚀 파이프라인 시작")
        logger.info(f"\n{'='*50}")
        logger.info(f"  [{category_ko}] Feed 단계 시작")
        logger.info(f"  윈도우: {window_start:%Y-%m-%d %H:%M} ~ {window_end:%Y-%m-%d %H:%M} KST")
        logger.info(f"{'='*50}")

        # ── 1. 뉴스 수집 (시간 윈도우 필터 + backward 확장 fallback) ──
        # prefetched 가 주어지면 run_pipeline 의 병렬 수집 결과를 그대로 사용.
        if prefetched is not None:
            articles, win_stats, extended = prefetched
            log_step(
                category_ko,
                f"1️⃣ 뉴스 수집 (병렬 prefetch 사용, 윈도우 필터 통과)",
            )
            if extended:
                log_step(
                    category_ko,
                    f"⚠️ 병렬 수집 단계에서 윈도우 부족 → "
                    f"{WINDOW_FALLBACK_EXTEND_HOURS}h 확장 적용됨",
                    color=0xFFAA00,
                )
            result["collected_window"] = len(articles)
        else:
            collect_label = (
                "1️⃣ 뉴스 수집 시작 (윈도우 필터)"
                if BRIEFING_WINDOW_ENABLED
                else "1️⃣ 뉴스 수집 시작 (윈도우 비활성화)"
            )
            log_step(category_ko, collect_label)
            try:
                articles, win_stats, extended = _collect_with_window_fallback(
                    news_service, category_ko, window_start, window_end,
                )
                if extended:
                    log_step(
                        category_ko,
                        f"⚠️ 윈도우 부족 → "
                        f"{WINDOW_FALLBACK_EXTEND_HOURS}h 확장",
                        color=0xFFAA00,
                    )
                result["collected_window"] = len(articles)
            except Exception as e:
                log_step(
                    category_ko,
                    f"❌ 1️⃣ 뉴스 수집 실패: {str(e)[:100]}",
                    color=0xFF0000,
                )
                raise

        result["collected"] = len(articles)
        result["window_stats"] = win_stats

        # 결측률 임계치 초과 시 alerts 경고 (네이버 HTML 구조 변경 감지)
        total_seen = win_stats.get("total_collected", 0) or 0
        missing = win_stats.get("missing_pub", 0) or 0
        if total_seen > 0:
            missing_rate = missing / total_seen
            if missing_rate > PUB_MISSING_RATE_ALERT_THRESHOLD:
                from app.services.notify_service import notify_missing_pub_rate
                notify_missing_pub_rate(
                    category_ko=category_ko,
                    missing=missing,
                    total=total_seen,
                    rate=missing_rate,
                )
                logger.warning(
                    f"  ⚠️ [{category_ko}] published_at 결측률 "
                    f"{missing_rate:.1%} > {PUB_MISSING_RATE_ALERT_THRESHOLD:.0%} "
                    f"임계 — alerts 경고 발송"
                )

        # pipeline 채널 detail: 윈도우 필터 통계
        date_keys = win_stats.get("naver_date_list_keys") or []
        date_keys_short = [
            f"{k[4:6]}-{k[6:8]}" for k in date_keys if len(k) == 8
        ]
        ws_dt = datetime.fromisoformat(win_stats["window_start"]).astimezone(_KST)
        we_dt = datetime.fromisoformat(win_stats["window_end"]).astimezone(_KST)
        extend_mark = " · 3h 확장됨" if extended else ""
        detail_lines = [
            f"{len(date_keys)}개 네이버 날짜 리스트 ("
            f"{', '.join(date_keys_short)}) → "
            f"{win_stats.get('total_collected', 0)}건 수집",
            f"→ 유지 {win_stats.get('kept', 0)}건 · 윈도우 밖 "
            f"{win_stats.get('dropped_outside', 0)}건 · published_at 결측 "
            f"{win_stats.get('missing_pub', 0)}건",
            f"→ 윈도우: {ws_dt:%m-%d %H:%M} ~ {we_dt:%m-%d %H:%M} "
            f"({win_stats.get('window_hours', 0)}h){extend_mark}",
        ]
        log_step(
            category_ko,
            f"1️⃣ 수집 완료: {len(articles)}건 (윈도우 필터 통과)",
            detail="\n".join(detail_lines),
        )

        if len(articles) < WINDOW_MIN_ARTICLES:
            logger.warning(
                f"  [{category_ko}] 확장 후에도 {len(articles)}건 — 부족, 스킵"
            )
            log_step(
                category_ko,
                f"⚠️ 기사 부족 ({len(articles)}건) — 스킵",
                color=0xFFAA00,
            )
            result["status"] = "skipped_insufficient"
            return result

        category_articles_full = list(articles)

        # ── 2. 임베딩 ──
        log_step(category_ko, "2️⃣ 임베딩 시작")
        try:
            logger.info(f"  [{category_ko}] 임베딩 생성...")
            embeddings = embed_articles(articles)
            log_step(category_ko, f"2️⃣ 임베딩 완료: {embeddings.shape}")
        except Exception as e:
            log_step(category_ko, f"❌ 2️⃣ 임베딩 실패: {str(e)[:100]}", color=0xFF0000)
            raise

        # 임베딩 완료 후 GPU 메모리 해제 (Gemma4 헤드라인 생성을 위해)
        from app.services.embedding_service import unload_model
        unload_model()

        # ── 3. Near-Duplicate 제거 ──
        log_step(category_ko, "3️⃣ 중복 제거 시작")
        try:
            keep_indices = remove_near_duplicates(embeddings, threshold=0.95)
            articles = [articles[i] for i in keep_indices]
            embeddings = embeddings[keep_indices]
            result["after_dedup"] = len(articles)
            log_step(category_ko, f"3️⃣ 중복 제거 완료: {result['collected']}건 → {len(articles)}건")
        except Exception as e:
            log_step(category_ko, f"❌ 3️⃣ 중복 제거 실패: {str(e)[:100]}", color=0xFF0000)
            raise

        # ── 4. 클러스터링 ──
        log_step(category_ko, "4️⃣ 클러스터링 시작")
        try:
            logger.info(f"  [{category_ko}] 클러스터링...")
            labels, clusters, cluster_info = cluster_articles(
                embeddings, n_articles=len(articles)
            )
            result["clustering"] = {
                "n_clusters": cluster_info["n_clusters"],
                "noise_ratio": cluster_info["noise_ratio"],
                "max_cluster_size": cluster_info["max_cluster_size"],
                "mcs": cluster_info["mcs"],
                "umap_dim": cluster_info["umap_dim"],
                "attempt": cluster_info.get("attempt", 1),
            }
            log_step(category_ko, f"4️⃣ 클러스터링 완료: {cluster_info['n_clusters']}개 클러스터")
        except Exception as e:
            log_step(category_ko, f"❌ 4️⃣ 클러스터링 실패: {str(e)[:100]}", color=0xFF0000)
            raise

        # ── 5. 토픽 랭킹 (top 20 한 번에 가져온 뒤 섹션별로 slice) ──
        log_step(category_ko, "5️⃣ 토픽 랭킹 시작")
        try:
            logger.info(f"  [{category_ko}] 토픽 랭킹...")
            all_ranked_topics = rank_topics(
                clusters, articles, embeddings,
                top_n=20, articles_per_topic=3,
                category_articles=category_articles_full,
                use_weighted_score=True,
            )
            headline_topics = all_ranked_topics[:5]  # 헤드라인 생성용
            result["ranked_topics_total"] = len(all_ranked_topics)
            result["headline_topics_count"] = len(headline_topics)

            topic_lines = "\n".join(
                f"  {i+1}. ({t['size']}건) {t['representative_article'].get('title', '')[:40]}"
                for i, t in enumerate(headline_topics)
            )
            log_step(
                category_ko,
                f"5️⃣ 토픽 랭킹 완료: top {len(headline_topics)} (전체 {len(all_ranked_topics)}개)",
                topic_lines,
            )
        except Exception as e:
            log_step(category_ko, f"❌ 5️⃣ 토픽 랭킹 실패: {str(e)[:100]}", color=0xFF0000)
            raise

        for i, topic in enumerate(headline_topics):
            logger.info(
                f"    토픽 {i+1} ({topic['size']}건): "
                f"{topic['representative_article'].get('title', '')[:50]}"
            )

        # ── 5-b. NewsCards 저장 (홈 탭용, 클러스터 대표 기사 rank 1~20) ──
        log_step(category_ko, "5️⃣-b 홈 탭 NewsCards 저장 시작")
        try:
            from app.services.supabase_storage_service import save_news_cards
            saved_count = save_news_cards(
                topics=all_ranked_topics,
                category_en=category_en,
                date_str=date_str,
                max_cards=20,
                slot=slot_str,
            )
            result["news_cards_saved"] = saved_count
            log_step(category_ko, f"5️⃣-b NewsCards 저장 완료: {saved_count}건")
        except Exception as e:
            log_step(category_ko, f"❌ 5️⃣-b NewsCards 저장 실패: {str(e)[:100]}", color=0xFF0000)
            # NewsCards 저장 실패는 치명적이지 않으므로 계속 진행
            result["news_cards_saved"] = 0

        # ── 6. 오늘의 브리핑 헤드라인 생성 (Gemma4 로컬) ──
        log_step(category_ko, "6️⃣ 헤드라인 생성 시작 (Gemma4)")
        try:
            logger.info(f"  [{category_ko}] 헤드라인 생성...")
            from app.services.headline_service import generate_all_headlines
            topics_with_headlines = generate_all_headlines(headline_topics)

            from app.services.supabase_storage_service import save_headlines
            save_headlines(
                category_en=category_en,
                date_str=date_str,
                headlines=topics_with_headlines,
                slot=slot_str,
            )
            # title 생성(Gemma4 헤드라인 재활용) 에 필요하므로 briefing phase 로 전달
            result["topics_with_headlines"] = topics_with_headlines
            log_step(category_ko, f"6️⃣ 헤드라인 완료: {len(topics_with_headlines)}건 저장")
        except Exception as e:
            log_step(category_ko, f"❌ 6️⃣ 헤드라인 실패: {str(e)[:100]}", color=0xFF0000)
            raise

        # ── 7. 통합 브리핑용 풀 구성 (하드뉴스 카테고리만, previous-topics dedup 포함) ──
        if category_ko in HARD_NEWS_CATEGORIES_KO:
            log_step(
                category_ko,
                f"7️⃣ 통합 브리핑용 소스 풀 구성 시작 "
                f"(top {PODCAST_TOPICS_PER_CATEGORY}, dedup prev_kw={len(prev_kw_sets or [])})",
            )
            try:
                # dedup: 직전 팟캐스트에서 이미 다룬 토픽(키워드 집합 overlap ≥ threshold) 제외.
                # 제외 대상의 대표 기사 제목과 겹친 키워드를 같이 모아 웹훅으로 전송.
                dedup_excluded: List[dict] = []
                if prev_kw_sets:
                    filtered_topics = []
                    prev_sets_typed = [set(p) for p in prev_kw_sets]
                    for t in all_ranked_topics:
                        current = topic_keyword_set(t)
                        overlap_kws = None
                        if len(current) >= DEDUP_KEYWORD_OVERLAP_THRESHOLD:
                            for prev_set in prev_sets_typed:
                                shared = current & prev_set
                                if len(shared) >= DEDUP_KEYWORD_OVERLAP_THRESHOLD:
                                    overlap_kws = sorted(shared)
                                    break
                        if overlap_kws:
                            title_preview = (
                                t.get("representative_article", {}).get("title") or ""
                            )[:36]
                            dedup_excluded.append({
                                "title": title_preview,
                                "overlap": overlap_kws,
                            })
                        else:
                            filtered_topics.append(t)

                    if dedup_excluded:
                        logger.info(
                            f"  [{category_ko}] previous-topics dedup: "
                            f"{len(dedup_excluded)}개 제거 "
                            f"(threshold={DEDUP_KEYWORD_OVERLAP_THRESHOLD} 겹침)"
                        )
                        # 상위 5개까지 detail 에 표시
                        lines = [
                            f"• \"{x['title']}\" ← 겹침 [{', '.join(x['overlap'])}]"
                            for x in dedup_excluded[:5]
                        ]
                        more = len(dedup_excluded) - 5
                        if more > 0:
                            lines.append(f"... 외 {more}건")
                        log_step(
                            category_ko,
                            f"🚫 previous-topics dedup 제외 {len(dedup_excluded)}건",
                            detail="\n".join(lines),
                            color=0xFFAA00,
                        )
                else:
                    filtered_topics = list(all_ranked_topics)

                podcast_topics = filtered_topics[:PODCAST_TOPICS_PER_CATEGORY]
                if not podcast_topics:
                    logger.warning(
                        f"  [{category_ko}] dedup 후 남은 토픽 없음 — 팟캐스트 기여 스킵"
                    )
                    log_step(
                        category_ko,
                        "⚠️ dedup 후 토픽 0개 — 팟캐스트 기여 스킵",
                        color=0xFFAA00,
                    )
                else:
                    pool_articles, allocation_info = build_topic_weighted_pool(
                        podcast_topics, articles, embeddings,
                        target=50, min_per_topic=6,
                    )
                    result["podcast_topics"] = podcast_topics
                    result["pool_articles"] = pool_articles
                    result["allocation_info"] = allocation_info
                    log_step(
                        category_ko,
                        f"7️⃣ 소스 풀 완료: {len(pool_articles)}건 "
                        f"(팟캐스트 토픽 {len(podcast_topics)}개)",
                    )
            except Exception as e:
                log_step(category_ko, f"❌ 7️⃣ 소스 풀 실패: {str(e)[:100]}", color=0xFF0000)
                raise
        else:
            logger.info(
                f"  [{category_ko}] 팟캐스트 제외 카테고리 — 풀 구성 스킵"
            )

        result["status"] = "success"
        result["elapsed_sec"] = round(time.time() - t0, 1)

        from app.services.notify_service import format_elapsed as _fmt_elapsed
        log_step(
            category_ko,
            f"🏁 Feed 단계 완료 (⏱️ {_fmt_elapsed(result['elapsed_sec'])})",
            color=0x00FF00,
        )
        logger.info(
            f"✅ [{category_ko}] Feed 완료: {result['collected']}건 수집 → "
            f"{result['after_dedup']}건 중복제거 → "
            f"{result['clustering']['n_clusters']}개 토픽 "
            f"({result['elapsed_sec']}초)"
        )

    except Exception as e:
        logger.exception(f"❌ [{category_ko}] Feed 실패: {e}")
        result["status"] = "failed"
        result["error"] = str(e)
        result["elapsed_sec"] = round(time.time() - t0, 1)

        from app.services.notify_service import notify_pipeline_error
        notify_pipeline_error(category_ko, str(e))

    return result


# ──────────────────────────────────────────────
# Briefing Phase (하루 1회, time_slot 당 1회)
# ──────────────────────────────────────────────

def generate_integrated_briefing(
    feed_results: List[dict],
    date_str: str,
    time_slot_ko: str,
    slot_str: str,
    skip_podcast: bool = False,
) -> dict:
    """하드뉴스 3카테고리 feed 결과를 엮어 통합 브리핑 대본/오디오를 생성합니다.

    Args:
        feed_results: process_category_feed() 결과 리스트 (전 카테고리).
        date_str: YYYY-MM-DD (KST)
        time_slot_ko: "오전" 또는 "오후" (대본/오디오 프롬프트에 사용)
        slot_str: "AM" 또는 "PM" (storage key 용)
        skip_podcast: True 면 NotebookLM 오디오 생성 스킵, 대본만 저장.

    Returns:
        briefing 단계 결과 dict
    """
    from app.services.notify_service import log_step, format_elapsed
    from app.services.notebooklm_service import (
        generate_podcast,
        probe_audio_duration_seconds,
    )
    from app.services.supabase_storage_service import save_podcast

    brief_label = f"통합브리핑#{time_slot_ko}"
    t0 = time.time()

    result = {
        "stage": "briefing",
        "time_slot": time_slot_ko,
        "slot": slot_str,
        "status": "started",
    }

    log_step(brief_label, f"🎬 통합 브리핑 {time_slot_ko} 시작")

    # ── 하드뉴스 feed 결과만 추출, HARD_NEWS_CATEGORIES_KO 순서로 정렬 ──
    by_category = {r["category"]: r for r in feed_results}
    ordered_hard_news: List[dict] = []
    missing: List[str] = []
    for cat_ko in HARD_NEWS_CATEGORIES_KO:
        r = by_category.get(cat_ko)
        if not r or r.get("status") != "success" or not r.get("podcast_topics"):
            missing.append(cat_ko)
            continue
        ordered_hard_news.append(r)

    if not ordered_hard_news:
        log_step(brief_label, "❌ 하드뉴스 feed 결과 없음 — 브리핑 생성 중단", color=0xFF0000)
        result["status"] = "failed"
        result["error"] = "no_hard_news_feeds_available"
        return result

    if missing:
        logger.warning(
            f"  ⚠️ 누락 하드뉴스 카테고리: {missing} — 가능한 {len(ordered_hard_news)}개로 진행"
        )
        log_step(
            brief_label,
            f"⚠️ 누락 카테고리 {missing} — {len(ordered_hard_news)}개로 진행",
            color=0xFFAA00,
        )

    # ── categories_data 조립 (script_service.generate_script 포맷) ──
    categories_data = [
        {
            "category_ko": r["category"],
            "topics": r["podcast_topics"],
            "pool_articles": r["pool_articles"],
            "allocation_info": r["allocation_info"],
        }
        for r in ordered_hard_news
    ]
    categories_list = " → ".join(c["category_ko"] for c in categories_data)
    result["categories"] = [c["category_ko"] for c in categories_data]

    # ── title 생성: Gemma4 헤드라인 재활용 ──
    # 각 하드뉴스 카테고리 × podcast_topics top 1 의 헤드라인을 쉼표로 연결.
    # 헤드라인은 feed phase 의 Gemma4 출력을 재사용 — 추가 LLM 비용 0.
    title = _build_briefing_title(ordered_hard_news)
    result["title"] = title
    logger.info(f"  🏷️ 에피소드 title: {title!r}")

    # ── covered_keywords 추출: 다음 실행의 dedup 기준 ──
    # 에피소드에 실제 들어간 토픽들의 top 키워드 집합.
    covered_keywords = _build_covered_keywords(ordered_hard_news)
    result["covered_keywords"] = covered_keywords
    logger.info(
        f"  🔑 covered_keywords: {len(covered_keywords)}개 토픽 키워드 집합 저장 예정"
    )

    # ── NotebookLM REF 소스: 각 하드뉴스 카테고리 × top 토픽 × 대표 기사 N건 ──
    # 카테고리 태그를 붙여 REF 소스 제목에 "[REF][정치] ..." 식으로 노출되게 함.
    reference_articles: List[dict] = []
    for r in ordered_hard_news:
        cat_ko = r["category"]
        for topic in r["podcast_topics"]:
            sel = topic.get("selected_articles") or []
            for a in sel[:PODCAST_REF_ARTICLES_PER_TOPIC]:
                if not isinstance(a, dict):
                    continue
                tagged = dict(a)
                tagged.setdefault("category_ko", cat_ko)
                reference_articles.append(tagged)
    logger.info(
        f"  📚 REF 소스 {len(reference_articles)}건 준비 "
        f"({len(ordered_hard_news)}분야 × "
        f"{PODCAST_TOPICS_PER_CATEGORY}토픽 × "
        f"{PODCAST_REF_ARTICLES_PER_TOPIC}기사 상한)"
    )

    # ── 대본 생성 ──
    log_step(brief_label, f"📝 대본 생성 시작 ({categories_list})")
    try:
        logger.info(f"  통합 브리핑 대본 생성: {categories_list} / {time_slot_ko}")
        script = generate_script(
            categories_data=categories_data,
            time_slot=time_slot_ko,
            target_length=BRIEFING_TARGET_LENGTH,
            briefing_date=date_str,
        )
        if not script:
            log_step(brief_label, "❌ 대본 생성 실패 (빈 결과)", color=0xFF0000)
            result["status"] = "script_failed"
            return result
        result["script_length"] = len(script)
        log_step(brief_label, f"📝 대본 완료: {len(script)}자")
    except Exception as e:
        log_step(brief_label, f"❌ 대본 생성 실패: {str(e)[:100]}", color=0xFF0000)
        logger.exception("통합 브리핑 대본 생성 실패")
        result["status"] = "script_failed"
        result["error"] = str(e)
        return result

    # ── 대본 파일 저장 (항상, 로컬 백업) ──
    script_dir = Path("outputs") / "scripts"
    script_dir.mkdir(parents=True, exist_ok=True)
    ts = get_now_kst().strftime("%H%M%S")
    script_filename = f"briefing_{slot_str}_{date_str}_{ts}.txt"
    script_path = script_dir / script_filename
    script_path.write_text(script, encoding="utf-8")
    result["script_path"] = str(script_path)
    logger.info(f"  📝 대본 저장: {script_path}")

    # ── 오디오 생성 ──
    audio_path: Optional[str] = None
    duration_sec: Optional[int] = None
    if skip_podcast:
        log_step(brief_label, "🎧 오디오 생략 (--skip-podcast)")
        result["audio"] = "skipped"
    else:
        log_step(brief_label, "🎧 NotebookLM 오디오 생성 시작 (~15분)")
        try:
            audio_path = generate_podcast(
                script=script,
                time_slot=time_slot_ko,
                reference_articles=reference_articles,
                briefing_date=date_str,
            )
            if audio_path:
                duration_sec = probe_audio_duration_seconds(audio_path)
                duration_text = (
                    format_elapsed(duration_sec) if duration_sec else "길이 미상"
                )
                log_step(
                    brief_label,
                    f"🎧 오디오 완료: {Path(audio_path).name} ({duration_text})",
                )
                result["audio"] = audio_path
                result["duration_sec"] = duration_sec
            else:
                log_step(brief_label, "❌ 오디오 생성 실패 (결과 없음)", color=0xFF0000)
                from app.services.notify_service import notify_pipeline_error
                notify_pipeline_error(
                    brief_label,
                    "NotebookLM 오디오 생성 실패 — 대본은 저장됨. 서버 로그 확인 필요.",
                )
                result["audio"] = "failed"
        except Exception as e:
            log_step(brief_label, f"❌ 오디오 생성 실패: {str(e)[:100]}", color=0xFF0000)
            from app.services.notify_service import notify_pipeline_error
            notify_pipeline_error(brief_label, f"오디오 생성 예외: {str(e)[:300]}")
            logger.exception("통합 브리핑 오디오 생성 실패")
            result["audio"] = "failed"
            # 오디오 실패는 저장 단계를 중단시키지 않음 (대본은 저장)

    # ── Supabase 저장 (Storage + podcasts, UNIQUE(date, slot)) ──
    log_step(brief_label, "💾 Supabase 저장 시작")
    try:
        storage = save_podcast(
            date_str=date_str,
            slot=slot_str,
            script=script,
            audio_path=audio_path,
            title=title,
            covered_keywords=covered_keywords,
            duration_sec=duration_sec,
        )
        result["storage"] = storage
        log_step(brief_label, f"💾 저장 완료: {storage['podcast_id']}")
    except Exception as e:
        log_step(brief_label, f"❌ Supabase 저장 실패: {str(e)[:100]}", color=0xFF0000)
        from app.services.notify_service import notify_pipeline_error
        notify_pipeline_error(brief_label, f"Supabase 저장 실패: {str(e)[:300]}")
        logger.exception("통합 브리핑 저장 실패")
        result["status"] = "storage_failed"
        result["error"] = str(e)
        return result

    result["status"] = "success"
    result["elapsed_sec"] = round(time.time() - t0, 1)
    log_step(
        brief_label,
        f"🏁 통합 브리핑 완료 (⏱️ {format_elapsed(result['elapsed_sec'])})",
        color=0x00FF00,
    )
    return result


# ──────────────────────────────────────────────
# Pipeline 오케스트레이션
# ──────────────────────────────────────────────

def run_pipeline(
    time_slot_ko: str,
    categories: Optional[List[str]] = None,
    skip_podcast: bool = False,
    skip_script: bool = False,
):
    """전체 파이프라인을 실행합니다.

    Args:
        time_slot_ko: "오전" 또는 "오후"
        categories: feed 단계 대상 필터 (None 이면 CATEGORY_MAP 의 수집 가능한 전 카테고리)
        skip_podcast: True 면 NotebookLM 오디오 생성 스킵 (대본만 저장).
                      인증 실패 시에도 자동으로 True 로 전환됨.
        skip_script: True 면 통합 브리핑 단계(GPT 대본 생성·저장 + NotebookLM)를 통째로
                     스킵. Feed 단계만 검증하고 싶을 때 사용. skip_podcast 를 자동 함의.
    """
    total_start = time.time()
    now = get_now_kst()
    date_str = get_today_kst()
    slot_str = _slot_label(time_slot_ko)

    # 시간 윈도우 계산
    window_start, window_end = compute_time_window(time_slot_ko, now)

    logger.info(f"{'='*60}")
    logger.info(f"  Briefly v2 파이프라인 시작 ({time_slot_ko} / slot={slot_str})")
    logger.info(f"  시각: {now.strftime('%Y-%m-%d %H:%M:%S')} KST (date={date_str})")
    if BRIEFING_WINDOW_ENABLED:
        logger.info(
            f"  수집 윈도우: {window_start:%Y-%m-%d %H:%M} ~ {window_end:%Y-%m-%d %H:%M} KST"
        )
    else:
        logger.info("  🚫 수집 윈도우 비활성화 (출시 전) — 네이버 오늘 리스트 전체 수집")
    logger.info(f"{'='*60}")

    # NotebookLM 인증 확인 + 자동 갱신 (팟캐스트 생성 시)
    if not skip_podcast:
        from app.services.notebooklm_service import ensure_auth
        if not ensure_auth():
            logger.warning(
                "⚠️ NotebookLM 인증 갱신 실패 → 대본만 저장 모드로 전환"
            )
            skip_podcast = True
            from app.services.notify_service import notify_auth_failure
            notify_auth_failure()

    # 직전 팟캐스트들의 covered_keywords 로드 (previous-topics dedup)
    from app.services.supabase_storage_service import fetch_recent_covered_keywords
    prev_kw_sets = fetch_recent_covered_keywords(lookback_hours=DEDUP_LOOKBACK_HOURS)

    # 카테고리 필터
    if categories:
        target = {
            k: v for k, v in CATEGORY_MAP.items()
            if v["api_name"] in categories or k in categories
        }
    else:
        target = {
            k: v for k, v in CATEGORY_MAP.items()
            if v.get("naver_sid")  # Naver sid가 있는 카테고리만
        }

    logger.info(f"  Feed 대상 카테고리: {list(target.keys())}")
    logger.info(f"  하드뉴스(팟캐스트 포함): {HARD_NEWS_CATEGORIES_KO}")

    news_service = NaverNewsService(request_delay=0.2)
    feed_results: List[dict] = []

    # ── Prefetch Phase: 카테고리 병렬 수집 (I/O-bound) ──
    # 네이버 상세페이지 스크래핑이 Feed 전체 시간의 대부분을 차지하고, 순수 I/O 대기라
    # thread 병렬화가 유효. 임베딩·클러스터링은 KURE GPU 공유 때문에 순차 유지.
    from app.services.notify_service import log_step
    t_prefetch = time.time()
    logger.info(
        f"📥 카테고리 병렬 수집 시작 ({len(target)}개 카테고리, "
        f"max_workers={COLLECT_PARALLELISM})"
    )
    log_step(
        "PREFETCH",
        f"📥 병렬 수집 시작: {', '.join(target.keys())}",
    )
    prefetched: dict = {}
    with ThreadPoolExecutor(max_workers=COLLECT_PARALLELISM) as ex:
        futures = {
            ex.submit(
                _collect_with_window_fallback,
                news_service, cat_ko, window_start, window_end,
            ): cat_ko
            for cat_ko in target.keys()
        }
        for fut in as_completed(futures):
            cat_ko = futures[fut]
            try:
                articles, stats, extended = fut.result()
                prefetched[cat_ko] = (articles, stats, extended)
                logger.info(
                    f"  ✅ [{cat_ko}] 병렬 수집 완료: {len(articles)}건 "
                    f"(확장={extended})"
                )
            except Exception as e:
                logger.exception(f"[{cat_ko}] 병렬 수집 실패: {e}")
                prefetched[cat_ko] = ([], {}, False)
    prefetch_elapsed = time.time() - t_prefetch
    logger.info(
        f"📥 병렬 수집 총 소요: {prefetch_elapsed:.1f}초 "
        f"({len(prefetched)} 카테고리 완료)"
    )
    from app.services.notify_service import format_elapsed
    log_step(
        "PREFETCH",
        f"📥 병렬 수집 완료: ⏱️ {format_elapsed(prefetch_elapsed)}",
        color=0x00FF00,
    )

    # ── Feed Phase: 카테고리별 순차 처리 (embed/cluster/rank — GPU 공유) ──
    for cat_ko, config in target.items():
        result = process_category_feed(
            cat_ko, config, news_service, date_str, slot_str,
            window_start=window_start,
            window_end=window_end,
            prev_kw_sets=prev_kw_sets,
            prefetched=prefetched.get(cat_ko),
        )
        feed_results.append(result)

    # ── Briefing Phase: 통합 브리핑 1회 ──
    # categories 필터가 하드뉴스 셋과 겹치지 않으면 브리핑 단계 스킵.
    if skip_script:
        logger.info("  🚫 --skip-script — 통합 브리핑 단계(대본+오디오) 통째로 스킵")
        briefing_result = {
            "stage": "briefing",
            "status": "skipped_skip_script_flag",
        }
    else:
        feed_hard_news = [
            r for r in feed_results
            if r["category"] in HARD_NEWS_CATEGORIES_KO
        ]
        if not feed_hard_news:
            logger.info(
                "  하드뉴스 카테고리가 feed 대상에 없음 → 통합 브리핑 단계 스킵"
            )
            briefing_result = {
                "stage": "briefing",
                "status": "skipped_no_hard_news_in_filter",
            }
        else:
            briefing_result = generate_integrated_briefing(
                feed_results=feed_results,
                date_str=date_str,
                time_slot_ko=time_slot_ko,
                slot_str=slot_str,
                skip_podcast=skip_podcast,
            )

    # ── 요약 ──
    total_elapsed = time.time() - total_start

    logger.info(f"\n{'='*60}")
    logger.info(f"  파이프라인 완료 ({total_elapsed:.0f}초)")
    logger.info(f"{'='*60}")

    for r in feed_results:
        status_icon = "✅" if r["status"] == "success" else "❌"
        logger.info(
            f"  {status_icon} [{r['category']}] Feed: {r.get('collected', 0)}건 → "
            f"{r.get('clustering', {}).get('n_clusters', '?')}개 토픽 "
            f"({r.get('elapsed_sec', 0)}초)"
        )

    b_icon = "✅" if briefing_result.get("status") == "success" else "❌"
    logger.info(
        f"  {b_icon} [통합 브리핑 {time_slot_ko}] {briefing_result.get('status')} "
        f"({briefing_result.get('elapsed_sec', 0)}초)"
    )

    # Discord 완료 알림 (feed + briefing 통합 요약)
    from app.services.notify_service import notify_pipeline_success
    notify_pipeline_success(feed_results, briefing_result)

    # 결과 JSON 저장 (pool_articles 같은 대용량 필드는 축약)
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    ts = now.strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"pipeline_result_{slot_str}_{ts}.json"

    # 직렬화용 feed 결과 (pool_articles 는 크기만 남김)
    def _summarize_feed(r: dict) -> dict:
        out = {k: v for k, v in r.items() if k not in ("pool_articles", "podcast_topics", "allocation_info")}
        out["pool_articles_count"] = len(r["pool_articles"]) if r.get("pool_articles") else 0
        out["podcast_topics_count"] = len(r["podcast_topics"]) if r.get("podcast_topics") else 0
        return out

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": ts,
            "time_slot": time_slot_ko,
            "slot": slot_str,
            "date": date_str,
            "elapsed_sec": round(total_elapsed, 1),
            "feed_results": [_summarize_feed(r) for r in feed_results],
            "briefing_result": briefing_result,
        }, f, ensure_ascii=False, indent=2)

    logger.info(f"  결과 저장: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Briefly v2 통합 브리핑 파이프라인")
    parser.add_argument(
        "--time-slot",
        dest="time_slot",
        choices=["morning", "afternoon", "오전", "오후", "AM", "PM", "am", "pm"],
        default=None,
        help="브리핑 슬롯. 생략 시 현재 KST 시각으로 자동 판정 (<12시=오전, >=12시=오후).",
    )
    parser.add_argument(
        "--categories", nargs="*",
        help="Feed 단계 카테고리 필터 (예: economy politics). 생략 시 전체.",
    )
    parser.add_argument(
        "--skip-podcast", action="store_true",
        help="NotebookLM 오디오 생성 스킵 (수집+대본만).",
    )
    parser.add_argument(
        "--skip-script", action="store_true",
        help="통합 브리핑 단계 통째로 스킵 (Feed 단계만 검증). --skip-podcast 자동 함의.",
    )
    args = parser.parse_args()

    time_slot_ko = _resolve_time_slot(args.time_slot)

    run_pipeline(
        time_slot_ko=time_slot_ko,
        categories=args.categories,
        skip_podcast=args.skip_podcast or args.skip_script,
        skip_script=args.skip_script,
    )


if __name__ == "__main__":
    main()
