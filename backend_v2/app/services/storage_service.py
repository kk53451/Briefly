"""
S3 + DynamoDB 저장 서비스

파이프라인 결과물(대본 + MP3 + 헤드라인)을 기존 backend 인프라에 저장합니다.

S3 경로:    news-audio/{date}/shared/{category}_{slot}.mp3
DynamoDB:   Frequencies 테이블, PK = {category}#{date}#{slot}
            Headlines 테이블,   PK = {category}#{date}#{slot}

환경변수:
    S3_BUCKET               (기본: briefly-news-audio)
    DDB_FREQ_TABLE          (기본: Frequencies)
    DDB_HEADLINES_TABLE     (기본: Headlines)
    AWS_DEFAULT_REGION      (기본: ap-northeast-2)
"""

import os
import json
import logging
from typing import Dict, List, Optional

import boto3

from app.utils.date import get_briefing_slot, get_now_kst

logger = logging.getLogger(__name__)

S3_BUCKET = os.getenv("S3_BUCKET", "briefly-news-audio")
DDB_TABLE = os.getenv("DDB_FREQ_TABLE", "Frequencies")
DDB_HEADLINES = os.getenv("DDB_HEADLINES_TABLE", "Headlines")
REGION = os.getenv("AWS_DEFAULT_REGION", "ap-northeast-2")


def upload_audio_to_s3(
    local_path: str,
    category_en: str,
    date_str: str,
    slot: str = None,
) -> Optional[str]:
    """
    MP3 파일을 S3에 업로드하고 오브젝트 키를 반환합니다.

    Args:
        local_path: 로컬 MP3 파일 경로
        category_en: 영문 카테고리 (economy, politics, ...)
        date_str: YYYY-MM-DD 형식 날짜
        slot: "AM" 또는 "PM". None이면 현재 KST 기준 자동 판정.

    Returns:
        S3 오브젝트 키 (예: "news-audio/2026-04-16/shared/economy_AM.mp3")
        실패 시 None
    """
    if slot is None:
        slot = "AM" if get_briefing_slot() == "오전" else "PM"

    s3_key = f"news-audio/{date_str}/shared/{category_en}_{slot}.mp3"

    try:
        s3 = boto3.client("s3", region_name=REGION)
        s3.upload_file(
            local_path,
            S3_BUCKET,
            s3_key,
            ExtraArgs={"ContentType": "audio/mpeg"},
        )
        logger.info(f"  ☁️ S3 업로드 완료: s3://{S3_BUCKET}/{s3_key}")
        return s3_key
    except Exception as e:
        logger.error(f"  ❌ S3 업로드 실패: {e}")
        return None


def get_audio_presigned_url(s3_key: str, expiry: int = 604800) -> Optional[str]:
    """
    S3 오브젝트의 presigned URL을 생성합니다.

    Args:
        s3_key: S3 오브젝트 키
        expiry: URL 유효 시간 (초, 기본 7일)

    Returns:
        presigned URL 문자열, 실패 시 None
    """
    try:
        s3 = boto3.client("s3", region_name=REGION)
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET, "Key": s3_key},
            ExpiresIn=expiry,
        )
        return url
    except Exception as e:
        logger.error(f"  ❌ Presigned URL 생성 실패: {e}")
        return None


def save_frequency(
    category_en: str,
    date_str: str,
    script: str,
    audio_url: Optional[str] = None,
    slot: str = None,
) -> bool:
    """
    Frequencies 테이블에 팟캐스트 데이터를 저장합니다.

    PK 포맷: {category}#{date}#{slot}
    예: economy#2026-04-16#AM

    Args:
        category_en: 영문 카테고리
        date_str: YYYY-MM-DD 형식 날짜
        script: 대본 텍스트
        audio_url: S3 presigned URL (없으면 None)
        slot: "AM" 또는 "PM". None이면 현재 KST 기준 자동 판정.

    Returns:
        성공 여부
    """
    if slot is None:
        slot = "AM" if get_briefing_slot() == "오전" else "PM"

    frequency_id = f"{category_en}#{date_str}#{slot}"
    now = get_now_kst()

    item = {
        "frequency_id": {"S": frequency_id},
        "script": {"S": script},
        "category": {"S": category_en},
        "date": {"S": date_str},
        "slot": {"S": slot},
        "created_at": {"S": now.isoformat()},
    }

    if audio_url:
        item["audio_url"] = {"S": audio_url}

    try:
        ddb = boto3.client("dynamodb", region_name=REGION)
        ddb.put_item(TableName=DDB_TABLE, Item=item)
        logger.info(f"  💾 DynamoDB 저장 완료: {frequency_id}")
        return True
    except Exception as e:
        logger.error(f"  ❌ DynamoDB 저장 실패: {e}")
        return False


def save_pipeline_result(
    category_en: str,
    date_str: str,
    script: str,
    audio_path: Optional[str] = None,
    slot: str = None,
) -> dict:
    """
    파이프라인 결과물을 S3 + DynamoDB에 한 번에 저장합니다.

    scheduler.py에서 호출하는 통합 인터페이스.

    Args:
        category_en: 영문 카테고리
        date_str: YYYY-MM-DD 형식 날짜
        script: 대본 텍스트
        audio_path: 로컬 MP3 파일 경로 (없으면 대본만 저장)
        slot: "AM" 또는 "PM"

    Returns:
        {"s3_key", "audio_url", "frequency_id", "saved"} 딕셔너리
    """
    if slot is None:
        slot = "AM" if get_briefing_slot() == "오전" else "PM"

    result = {
        "frequency_id": f"{category_en}#{date_str}#{slot}",
        "s3_key": None,
        "audio_url": None,
        "saved": False,
    }

    # 1. 오디오가 있으면 S3 업로드
    if audio_path:
        s3_key = upload_audio_to_s3(audio_path, category_en, date_str, slot)
        if s3_key:
            result["s3_key"] = s3_key
            result["audio_url"] = get_audio_presigned_url(s3_key)

    # 2. DynamoDB 저장 (대본은 항상 저장, 오디오 URL은 있으면 포함)
    saved = save_frequency(
        category_en=category_en,
        date_str=date_str,
        script=script,
        audio_url=result["audio_url"],
        slot=slot,
    )
    result["saved"] = saved

    return result


# ──────────────────────────────────────────────
# NewsCards 저장 (홈 탭용 — 클러스터 대표 기사)
# ──────────────────────────────────────────────

def save_news_cards(
    topics: List[Dict],
    category_en: str,
    date_str: str,
    max_cards: int = 20,
) -> int:
    """
    클러스터 대표 기사를 NewsCards 테이블에 저장합니다.

    홈 탭(`/api/news/today`, `/api/news/home`)에서 쓰입니다.
    클러스터 크기 기준으로 rank 1~N을 부여하고, top max_cards 개만 저장합니다.

    Args:
        topics: rank_topics() 결과 (이미 크기 내림차순 정렬)
        category_en: 영문 카테고리
        date_str: YYYY-MM-DD
        max_cards: 저장할 최대 카드 수 (기본 20)

    Returns:
        저장된 카드 수
    """
    import re
    from datetime import datetime as _dt

    ddb = boto3.client("dynamodb", region_name=REGION)
    news_table = os.getenv("DDB_NEWS_TABLE", "NewsCards")

    selected = topics[:max_cards]
    category_date = f"{category_en}#{date_str}"
    collected_at = get_now_kst().isoformat()

    saved = 0
    # DynamoDB BatchWriteItem 제한: 1회 25개
    for batch_start in range(0, len(selected), 25):
        batch = selected[batch_start : batch_start + 25]
        put_requests = []

        for i, topic in enumerate(batch, start=batch_start):
            rep = topic.get("representative_article", {})
            rank = i + 1
            cluster_size = int(topic.get("size", 0))

            # news_id 추출: 링크에서 {oid}_{aid}, 없으면 rank 기반 대체 키
            link = rep.get("link", "") or ""
            m = re.search(r"/article/(\d+)/(\d+)", link)
            if m:
                news_id = f"naver_{m.group(1)}_{m.group(2)}"
            else:
                news_id = f"{category_en}_{date_str}_rank{rank}"

            item = {
                "news_id": {"S": news_id},
                "category_date": {"S": category_date},
                "category": {"S": category_en},
                "rank": {"N": str(rank)},
                "cluster_size": {"N": str(cluster_size)},
                "title": {"S": (rep.get("title") or "")[:500]},
                "images": {"S": (rep.get("thumbnail") or "")},
                "provider_link_page": {"S": link},
                "provider": {"S": (rep.get("press") or rep.get("provider") or "")},
                "byline": {"S": (rep.get("journalist") or "")},
                "published_at": {"S": (rep.get("published_at") or "")},
                "hilight": {"S": (rep.get("lede") or "")[:300]},
                "collected_at": {"S": collected_at},
                "content": {"S": (rep.get("content") or "")[:3000]},
            }

            put_requests.append({"PutRequest": {"Item": item}})

        try:
            resp = ddb.batch_write_item(RequestItems={news_table: put_requests})
            # unprocessed 재시도 (최대 3회)
            unprocessed = resp.get("UnprocessedItems", {})
            retry = 0
            while unprocessed and retry < 3:
                resp = ddb.batch_write_item(RequestItems=unprocessed)
                unprocessed = resp.get("UnprocessedItems", {})
                retry += 1
            saved += len(put_requests) - sum(len(v) for v in unprocessed.values())
        except Exception as e:
            logger.error(f"  ❌ NewsCards 배치 저장 실패: {e}")

    logger.info(f"  🗂️ NewsCards 저장: {saved}/{len(selected)}건 ({category_date}, rank 1~{len(selected)})")
    return saved


# ──────────────────────────────────────────────
# Headlines 저장
# ──────────────────────────────────────────────

def save_headlines(
    category_en: str,
    date_str: str,
    headlines: List[Dict],
    slot: str = None,
) -> bool:
    """
    오늘의 브리핑 헤드라인을 Headlines 테이블에 저장합니다.

    PK: {category}#{date}#{slot}  (예: economy#2026-04-17#AM)

    각 헤드라인 항목은 headline, summary, cluster_size, representative_article 등을
    포함하며, JSON으로 직렬화해 하나의 아이템으로 저장합니다.

    Args:
        category_en: 영문 카테고리
        date_str: YYYY-MM-DD 형식 날짜
        headlines: generate_all_headlines() 결과 리스트
        slot: "AM" 또는 "PM"

    Returns:
        저장 성공 여부
    """
    if slot is None:
        slot = "AM" if get_briefing_slot() == "오전" else "PM"

    category_date = f"{category_en}#{date_str}#{slot}"
    now = get_now_kst()

    # 각 헤드라인에서 DynamoDB 저장에 필요한 필드만 추출
    headline_items = []
    for h in headlines:
        rep = h.get("representative_article", {})
        headline_items.append({
            "topic_id": h.get("topic_id", 0),
            "headline": h.get("headline", ""),
            "summary": h.get("summary", ""),
            "cluster_size": h.get("size", 0),
            "representative_news_id": rep.get("news_id", rep.get("link", "")),
            "representative_title": rep.get("title", ""),
            "representative_image": rep.get("thumbnail", rep.get("images", "")),
            "representative_press": rep.get("press", rep.get("provider", "")),
            "keywords": [kw for kw, _ in h.get("keywords", [])],
        })

    item = {
        "category_date": {"S": category_date},
        "category": {"S": category_en},
        "date": {"S": date_str},
        "slot": {"S": slot},
        "headlines": {"S": json.dumps(headline_items, ensure_ascii=False)},
        "headline_count": {"N": str(len(headline_items))},
        "created_at": {"S": now.isoformat()},
    }

    try:
        ddb = boto3.client("dynamodb", region_name=REGION)
        ddb.put_item(TableName=DDB_HEADLINES, Item=item)
        logger.info(f"  💾 Headlines 저장 완료: {category_date} ({len(headline_items)}건)")
        return True
    except Exception as e:
        logger.error(f"  ❌ Headlines 저장 실패: {e}")
        return False
