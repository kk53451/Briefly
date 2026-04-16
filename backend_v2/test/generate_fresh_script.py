"""
최신 SYSTEM_PROMPT 를 반영한 새 대본 생성기 (9차 실험용).

compare_engines.py 와 동일한 파이프라인이지만 G-Eval 을 생략합니다.
Phase 2 가중 토픽 랭킹 + v2.1 VOICE TEXTURE 반영 대본을 빠르게 한 번 뽑기 위한
일회성 유틸입니다.

사용:
    cd backend_v2
    python -X utf8 -m test.generate_fresh_script

기본: 경제 카테고리. 다른 카테고리는 --category <en> 플래그로.
"""

import argparse
import json
import logging
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


CATEGORY_TO_KO = {
    "economy": "경제",
    "politics": "정치",
    "society": "사회",
    "culture": "문화",
    "international": "국제",
    "sports": "스포츠",
    "tech": "IT/과학",
}

DATA_PATH = Path("../backend/test/data/news_2026-04-11.json")
OUTPUT_DIR = Path("test/results")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", default="economy", choices=list(CATEGORY_TO_KO.keys()))
    parser.add_argument("--target-length", type=int, default=4000)
    parser.add_argument("--top-n", type=int, default=5)
    args = parser.parse_args()

    category_en = args.category
    category_ko = CATEGORY_TO_KO[category_en]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    logger.info("=" * 66)
    logger.info(f"  9차 대본 생성: {category_ko} (VOICE TEXTURE 반영)")
    logger.info("=" * 66)

    # ── 1. 기사 로드 ──
    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    articles = [a for a in data["articles"] if a.get("category") == category_en]
    logger.info(f"📰 기사 로드: {len(articles)}건 ({category_en})")

    if len(articles) < 20:
        logger.error(f"❌ 기사 부족: {len(articles)}건")
        return

    # corpus coverage 용 — dedup 전 원본 리스트 보존
    category_articles_full = list(articles)

    # ── 2. 임베딩 ──
    from app.services.embedding_service import embed_articles
    embeddings = embed_articles(articles)

    # ── 3. Near-dup 제거 ──
    import numpy as np
    from app.services.clustering_service import (
        remove_near_duplicates,
        cluster_articles,
        rank_topics,
        build_topic_weighted_pool,
    )

    keep = remove_near_duplicates(embeddings)
    articles = [articles[i] for i in keep]
    embeddings = embeddings[keep]
    logger.info(f"🔍 near-dup 제거 후: {len(articles)}건")

    # ── 4. 클러스터링 ──
    labels, clusters, cinfo = cluster_articles(embeddings, n_articles=len(articles))
    logger.info(
        f"🎯 클러스터링: {cinfo['n_clusters']}개, "
        f"noise {cinfo['noise_ratio']:.1%}, "
        f"최대 크기 {cinfo['max_cluster_size']}"
    )

    # ── 5. 토픽 랭킹 (Phase 2 가중 점수) ──
    topics = rank_topics(
        clusters,
        articles,
        embeddings,
        top_n=args.top_n,
        articles_per_topic=3,
        category_articles=category_articles_full,
        use_weighted_score=True,
    )
    logger.info(f"📊 토픽 {len(topics)}개 선정")
    for i, t in enumerate(topics):
        logger.info(
            f"  토픽 {i+1} ({t['size']}건): "
            f"{t['representative_article'].get('title', '')[:50]}..."
        )

    # ── 6. 토픽별 비례 배분 풀 ──
    pool_articles, allocation_info = build_topic_weighted_pool(
        topics, articles, embeddings, target=50, min_per_topic=6,
    )
    logger.info(f"📦 pool: {len(pool_articles)}건")
    for info in allocation_info:
        logger.info(
            f"    Topic {info['topic_id']} (size={info['topic_size']}): "
            f"{info['allocated']}건"
        )

    # ── 7. 대본 생성 (VOICE TEXTURE 반영) ──
    from app.services.script_service import generate_script
    t0 = time.time()
    script = generate_script(
        topics=topics,
        category_ko=category_ko,
        pool_articles=pool_articles,
        allocation_info=allocation_info,
        target_length=args.target_length,
    )
    gen_elapsed = time.time() - t0

    if not script:
        logger.error("❌ 대본 생성 실패")
        return

    # ── 8. 저장 ──
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"script_{category_en}_openai_{ts}.txt"
    out_path.write_text(script, encoding="utf-8")

    logger.info("")
    logger.info("=" * 66)
    logger.info(f"✅ 대본 저장: {out_path.name}")
    logger.info(f"   길이: {len(script)}자, 생성 시간: {gen_elapsed:.1f}초")
    logger.info("=" * 66)
    logger.info("")
    logger.info("--- 앞 400자 미리보기 ---")
    logger.info(script[:400])


if __name__ == "__main__":
    main()
