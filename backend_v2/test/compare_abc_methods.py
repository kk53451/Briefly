"""
A/B/C 팟캐스트 생성 방식 비교 실험

같은 토픽에 대해 3가지 방식으로 팟캐스트를 생성하고 G-Eval로 평가합니다.

방식 A: 원본 기사 → NotebookLM
방식 B: GPT 대본 → NotebookLM
방식 C: 원본 기사 + GPT 대본 → NotebookLM

사용법:
    cd backend_v2
    python -m test.compare_abc_methods --category economy

    # 대본 생성 + 평가만 (팟캐스트 생성 없이)
    python -m test.compare_abc_methods --category economy --script-only
"""

import sys
import json
import time
import argparse
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# 기존 backend/test/data에서 수집된 데이터 사용
DATA_DIR = Path(__file__).parent.parent.parent / "backend" / "test" / "data"


def load_articles(category: str, date: str = "2026-04-11"):
    """로컬 JSON에서 기사 로드"""
    path = DATA_DIR / f"news_{date}.json"
    if not path.exists():
        logger.error(f"데이터 없음: {path}")
        return []

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return [a for a in data["articles"] if a.get("category") == category]


def run_experiment(category_en: str, script_only: bool = False):
    """A/B/C 비교 실험 실행"""
    from app.constants.category_map import API_TO_KO
    from app.services.embedding_service import embed_articles
    from app.services.clustering_service import (
        remove_near_duplicates,
        cluster_articles,
        rank_topics,
        build_topic_weighted_pool,
    )
    from app.services.script_service import generate_script
    from app.services.eval_service import evaluate_script, format_eval_report

    category_ko = API_TO_KO.get(category_en, category_en)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    logger.info(f"\n{'='*60}")
    logger.info(f"  A/B/C 비교 실험: {category_ko}")
    logger.info(f"{'='*60}\n")

    # 1. 데이터 로드
    articles = load_articles(category_en)
    if not articles:
        return
    logger.info(f"기사 {len(articles)}건 로드")

    # 2. 임베딩
    logger.info("임베딩 생성...")
    embeddings = embed_articles(articles)

    # 3. 중복 제거
    keep = remove_near_duplicates(embeddings)
    articles = [articles[i] for i in keep]
    embeddings = embeddings[keep]

    # 4. 클러스터링
    logger.info("클러스터링...")
    labels, clusters, info = cluster_articles(embeddings)

    # 5. 토픽 랭킹 (상위 5개, 토픽당 3개 기사)
    topics = rank_topics(clusters, articles, embeddings, top_n=5, articles_per_topic=3)
    logger.info(f"토픽 {len(topics)}개 선정")

    for i, t in enumerate(topics):
        presses = [a.get("press", "") for a in t["selected_articles"]]
        logger.info(
            f"  토픽 {i+1} ({t['size']}건): "
            f"{t['representative_article']['title'][:40]}... "
            f"[{', '.join(presses)}]"
        )

    # 6. 토픽 기반 비례 샘플링으로 소스 풀 구성
    logger.info("\n토픽 기반 비례 풀 구성 중...")
    pool_articles, allocation_info = build_topic_weighted_pool(
        topics, articles, embeddings, target=50, min_per_topic=6
    )
    logger.info(f"풀 구성 완료: {len(pool_articles)}건")

    # 7. GPT 대본 생성 (토픽-소스 매핑 방식)
    logger.info("\n대본 생성 중...")
    script = generate_script(
        topics, category_ko,
        pool_articles=pool_articles,
        allocation_info=allocation_info,
    )
    if not script:
        logger.error("대본 생성 실패")
        return

    # 대본 저장
    script_file = RESULTS_DIR / f"script_{category_en}_{ts}.txt"
    script_file.write_text(script, encoding="utf-8")
    logger.info(f"대본 저장: {script_file} ({len(script)}자)")
    logger.info(f"\n--- 대본 미리보기 (앞 500자) ---\n{script[:500]}\n---")

    # 7. G-Eval 평가 (대본 품질) — 카테고리 전체 기사를 소스로 제공
    logger.info("\nG-Eval 대본 평가 중...")
    eval_result = evaluate_script(script, articles)
    if eval_result:
        report = format_eval_report(eval_result)
        logger.info(f"\n--- G-Eval 결과 ---\n{report}\n---")

    # 8. 팟캐스트 생성 (A/B/C)
    podcast_results = {}

    if not script_only:
        from app.services.notebooklm_service import generate_podcast

        for method in ["A", "B", "C"]:
            logger.info(f"\n{'─'*40}")
            logger.info(f"  방식 {method} 팟캐스트 생성")
            logger.info(f"{'─'*40}")

            audio_path = generate_podcast(
                topics, category_ko,
                script=script if method in ("B", "C") else None,
                method=method,
            )
            podcast_results[method] = audio_path or "failed"
            logger.info(f"  방식 {method}: {audio_path or 'FAILED'}")
    else:
        logger.info("\n--script-only 모드: 팟캐스트 생성 생략")

    # 9. 결과 저장
    result = {
        "experiment_date": ts,
        "category": category_en,
        "category_ko": category_ko,
        "article_count": len(articles),
        "topic_count": len(topics),
        "topics": [
            {
                "size": t["size"],
                "representative_title": t["representative_article"]["title"],
                "selected_presses": t["selected_presses"],
            }
            for t in topics
        ],
        "script_length": len(script),
        "script_file": str(script_file),
        "eval": eval_result,
        "podcasts": podcast_results,
    }

    output_file = RESULTS_DIR / f"abc_experiment_{category_en}_{ts}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    logger.info(f"\n결과 저장: {output_file}")

    # 요약
    logger.info(f"\n{'='*60}")
    logger.info(f"  실험 완료 요약")
    logger.info(f"{'='*60}")
    logger.info(f"  카테고리: {category_ko}")
    logger.info(f"  기사: {len(articles)}건 → {len(topics)}개 토픽")
    logger.info(f"  대본: {len(script)}자")
    if eval_result:
        logger.info(f"  G-Eval: {eval_result.get('overall_score', '?')}/5.0")
    for method, path in podcast_results.items():
        logger.info(f"  방식 {method}: {path}")


def main():
    parser = argparse.ArgumentParser(description="A/B/C 팟캐스트 비교 실험")
    parser.add_argument("--category", default="economy", help="카테고리 (영문)")
    parser.add_argument(
        "--script-only", action="store_true",
        help="대본 생성 + G-Eval만 (팟캐스트 생성 안 함)"
    )
    args = parser.parse_args()

    run_experiment(args.category, script_only=args.script_only)


if __name__ == "__main__":
    main()
