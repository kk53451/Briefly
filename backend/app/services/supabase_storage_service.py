"""Supabase Storage + Postgres 저장 서비스.

통합 브리핑 리워크(2026-04-19) 이후:
- 팟캐스트는 오전/오후 통합 브리핑 2회만. 테이블은 `podcasts` (UNIQUE(date, slot)).
- 카테고리별 개별 팟캐스트·`frequencies` 테이블·`BRIEFING_CATEGORY_SENTINEL` 트릭은 제거됨.
- news_cards / headlines 는 계속 카테고리별 + (AM|PM) slot 로 저장 (Home/Today 피드용).

Storage 경로:
  팟캐스트:  {date}/briefing_{slot}.mp3   (bucket: briefly-audio, public)

Postgres:
  - podcasts      UNIQUE (date, slot)              # 통합 브리핑, 하루 2행
  - headlines     UNIQUE (category, date, slot)    # 카테고리별 피드 헤드라인
  - news_cards    PK news_id (rank 1..N upsert)    # 카테고리별 피드 카드
"""

import logging
import re
from datetime import datetime as _dt
from typing import Dict, List, Optional

from app.utils.date import get_briefing_slot, get_now_kst
from app.utils.supabase_client import get_audio_bucket, get_supabase

logger = logging.getLogger(__name__)


def _resolve_slot(slot: Optional[str]) -> str:
    if slot:
        return slot
    return "AM" if get_briefing_slot() == "오전" else "PM"


def _parse_published_at(value: Optional[str]) -> Optional[str]:
    """ISO 문자열을 timestamptz 컬럼에 안전하게 넣을 형식으로 정규화."""
    if not value:
        return None
    try:
        _dt.fromisoformat(value.replace("Z", "+00:00"))
        return value
    except ValueError:
        return None


def _pick_hero_image(rep: Dict) -> Optional[str]:
    """본문에서 긁은 images 배열의 첫 항목을 대표 이미지로 사용.

    naver_news_service.fetch_article_detail 가 og:image 를 배열 0번에 끼워넣기
    때문에 보통 첫 항목이 가장 큰 사진이다. 비어 있으면 목록 썸네일로 폴백.
    """
    body_images = rep.get("images")
    if isinstance(body_images, list) and body_images:
        first = body_images[0]
        if isinstance(first, str) and first:
            return first
    elif isinstance(body_images, str) and body_images:
        return body_images
    thumb = rep.get("thumbnail")
    return thumb or None


# ──────────────────────────────────────────────
# Storage (audio MP3)
# ──────────────────────────────────────────────

def upload_audio(
    local_path: str,
    date_str: str,
    slot: Optional[str] = None,
) -> Optional[str]:
    """통합 브리핑 MP3 를 Supabase Storage 에 업로드하고 object key 를 반환합니다.

    Returns:
        object key (예: "2026-04-19/briefing_AM.mp3") 또는 실패 시 None.
    """
    slot = _resolve_slot(slot)
    object_key = f"{date_str}/briefing_{slot}.mp3"
    bucket = get_audio_bucket()

    try:
        with open(local_path, "rb") as f:
            data = f.read()

        # supabase-py의 upload 는 path 충돌 시 에러. upsert=true 옵션 필요.
        get_supabase().storage.from_(bucket).upload(
            path=object_key,
            file=data,
            file_options={
                "content-type": "audio/mpeg",
                "upsert": "true",
            },
        )
        logger.info(f"  ☁️ Storage 업로드 완료: {bucket}/{object_key}")
        return object_key
    except Exception as e:
        logger.error(f"  ❌ Storage 업로드 실패: {e}")
        return None


# ──────────────────────────────────────────────
# Podcasts (통합 브리핑, UNIQUE(date, slot))
# ──────────────────────────────────────────────

def save_podcast(
    date_str: str,
    slot: str,
    script: str,
    audio_path: Optional[str] = None,
    title: Optional[str] = None,
    covered_keywords: Optional[List[List[str]]] = None,
    duration_sec: Optional[int] = None,
) -> dict:
    """통합 브리핑 팟캐스트(정치·경제·국제) 결과를 Storage + podcasts 에 저장합니다.

    오디오가 있으면 Supabase Storage 에 업로드 후 그 object key 를 `audio_path`
    컬럼에 기록합니다. 오디오가 없으면 대본만 저장합니다.

    Args:
        date_str: YYYY-MM-DD (KST)
        slot: "AM" 또는 "PM"
        script: generate_script() 로 생성된 통합 브리핑 대본
        audio_path: generate_podcast() 로 생성된 로컬 MP3 경로. None 이면 대본만 저장.
        title: 에피소드 한 줄 제목. 예) "추경 35조 합의, 서울 아파트 반등, 美·이란 협상 개시".
               None 이면 저장 시 생략(NULL).
        covered_keywords: 이 에피소드에서 다룬 토픽들의 top 키워드 집합.
                          형식: [["추경","35조","합의"], ["아파트","서울","반등"], ...]
                          다음 실행의 previous-topics dedup 에서 사용됨.
        duration_sec: 오디오 재생 길이(초). NotebookLM 이 반환한 MP3 를 mutagen 으로
                      probe 해 넣습니다. 모바일 에피소드 리스트의 "12:40" 표시용.
                      None 이면 NULL 저장 (클라이언트가 just_audio 로 fallback).

    Returns:
        {"podcast_id": "YYYY-MM-DD#SLOT", "audio_path": object_key|None, "saved": bool}
    """
    result = {
        "podcast_id": f"{date_str}#{slot}",
        "audio_path": None,
        "saved": False,
    }

    if audio_path:
        object_key = upload_audio(audio_path, date_str, slot)
        if object_key:
            result["audio_path"] = object_key

    row = {
        "date": date_str,
        "slot": slot,
        "script": script,
        "audio_path": result["audio_path"],
        "title": title,
        "covered_keywords": covered_keywords or [],
        "duration_sec": duration_sec,
    }

    try:
        get_supabase().table("podcasts").upsert(
            row, on_conflict="date,slot"
        ).execute()
        logger.info(f"  💾 Podcast 저장 완료: {result['podcast_id']}")
        result["saved"] = True
    except Exception as e:
        logger.error(f"  ❌ Podcast 저장 실패: {e}")

    return result


def fetch_recent_covered_keywords(
    lookback_hours: int = 24,
) -> List[List[str]]:
    """직전 lookback_hours 시간 내 저장된 팟캐스트들의 covered_keywords 를 평탄화해서 반환.

    반환값: 각 토픽의 키워드 집합 리스트.
        [["추경","35조","합의"], ["이란","협상","호르무즈"], ...]
    이 리스트를 다음 실행의 토픽 candidate 키워드와 비교해 중복 여부 판단.
    """
    since_dt = get_now_kst() - _td_hours(lookback_hours)
    since_iso = since_dt.isoformat()

    try:
        res = (
            get_supabase()
            .table("podcasts")
            .select("covered_keywords")
            .gte("created_at", since_iso)
            .execute()
        )
    except Exception as e:
        logger.warning(f"  ⚠️ 직전 covered_keywords 조회 실패: {e}")
        return []

    out: List[List[str]] = []
    for row in res.data or []:
        kw_sets = row.get("covered_keywords") or []
        if not isinstance(kw_sets, list):
            continue
        for kset in kw_sets:
            if isinstance(kset, list) and kset:
                out.append([str(k) for k in kset])
    logger.info(
        f"  📜 직전 {lookback_hours}h covered_keywords 로드: "
        f"{len(out)}개 토픽 키워드 집합"
    )
    return out


def _td_hours(h: int):
    from datetime import timedelta
    return timedelta(hours=h)


# ──────────────────────────────────────────────
# News cards (홈 탭, 카테고리별)
# ──────────────────────────────────────────────

def save_news_cards(
    topics: List[Dict],
    category_en: str,
    date_str: str,
    max_cards: int = 20,
    slot: Optional[str] = None,
) -> int:
    """클러스터 대표 기사를 news_cards 에 저장 (rank 1..N, upsert)."""
    slot = _resolve_slot(slot)
    selected = topics[:max_cards]
    collected_at = get_now_kst().isoformat()

    rows = []
    for i, topic in enumerate(selected):
        rep = topic.get("representative_article", {})
        rank = i + 1
        cluster_size = int(topic.get("size", 0))

        link = rep.get("link", "") or ""
        m = re.search(r"/article/(\d+)/(\d+)", link)
        if m:
            news_id = f"naver_{m.group(1)}_{m.group(2)}"
        else:
            news_id = f"{category_en}_{date_str}_{slot}_rank{rank}"

        # rank_topics 의 keywords 는 [(키워드, 가중빈도), ...] 튜플 리스트.
        # 토픽 단위 검색·필터링을 위해 평탄 문자열 배열로 저장 (top 5).
        keywords = [kw for kw, _ in topic.get("keywords", []) if kw][:5]

        rows.append({
            "news_id": news_id,
            "category": category_en,
            "date": date_str,
            "slot": slot,
            "rank": rank,
            "cluster_size": cluster_size,
            "title": (rep.get("title") or "")[:500],
            "images": (rep.get("thumbnail") or None),
            "hero_image": _pick_hero_image(rep),
            "provider_link_page": link or None,
            "provider": rep.get("press") or rep.get("provider") or None,
            "byline": rep.get("journalist") or None,
            "published_at": _parse_published_at(rep.get("published_at")),
            "hilight": (rep.get("lede") or "")[:300] or None,
            "content": (rep.get("content") or "")[:3000] or None,
            "keywords": keywords,
            "collected_at": collected_at,
        })

    if not rows:
        return 0

    try:
        get_supabase().table("news_cards").upsert(
            rows, on_conflict="news_id"
        ).execute()
        logger.info(
            f"  🗂️ news_cards 저장: {len(rows)}건 ({category_en}#{date_str}#{slot}, rank 1~{len(rows)})"
        )
        return len(rows)
    except Exception as e:
        logger.error(f"  ❌ news_cards 저장 실패: {e}")
        return 0


# ──────────────────────────────────────────────
# Headlines (카테고리별 피드)
# ──────────────────────────────────────────────

def save_headlines(
    category_en: str,
    date_str: str,
    headlines: List[Dict],
    slot: Optional[str] = None,
) -> bool:
    slot = _resolve_slot(slot)

    items = []
    for h in headlines:
        rep = h.get("representative_article", {})
        items.append({
            "topic_id": h.get("topic_id", 0),
            "headline": h.get("headline", ""),
            "summary": h.get("summary", ""),
            "cluster_size": h.get("size", 0),
            "representative_news_id": rep.get("news_id", rep.get("link", "")),
            "representative_title": rep.get("title", ""),
            "representative_image": rep.get("thumbnail", rep.get("images", "")),
            "representative_hero_image": _pick_hero_image(rep) or "",
            "representative_press": rep.get("press", rep.get("provider", "")),
            "keywords": [kw for kw, _ in h.get("keywords", [])],
        })

    row = {
        "category": category_en,
        "date": date_str,
        "slot": slot,
        "items": items,
        "headline_count": len(items),
    }

    try:
        get_supabase().table("headlines").upsert(
            row, on_conflict="category,date,slot"
        ).execute()
        logger.info(
            f"  💾 Headlines 저장 완료: {category_en}#{date_str}#{slot} ({len(items)}건)"
        )
        return True
    except Exception as e:
        logger.error(f"  ❌ Headlines 저장 실패: {e}")
        return False
