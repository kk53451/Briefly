"""
OpenAI (gpt-5.4) vs Claude (opus-4-6) 대본 생성 품질 비교 실험

동일 입력(토픽 가중 풀, 프롬프트)을 두 엔진에 투입하여
대본을 나란히 생성하고 동일 judge (gpt-5.4)로 G-Eval 평가합니다.

사용법:
    cd backend_v2
    python -m test.compare_engines --category economy

    # 특정 엔진만 (비용/크레딧 이슈 테스트용)
    python -m test.compare_engines --category economy --engines openai
    python -m test.compare_engines --category economy --engines claude
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
# 루트와 backend_v2 양쪽 .env 로드 (CLAUDE_API_KEY는 루트에)
load_dotenv(Path(__file__).parent.parent.parent / ".env")
load_dotenv(Path(__file__).parent.parent / ".env", override=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)
DATA_DIR = Path(__file__).parent.parent.parent / "backend" / "test" / "data"


def load_articles(category: str, date: str = "2026-04-11"):
    path = DATA_DIR / f"news_{date}.json"
    if not path.exists():
        logger.error(f"데이터 없음: {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [a for a in data["articles"] if a.get("category") == category]


def run_pipeline_for_engine(
    engine_name: str,
    topics,
    articles,
    embeddings,
    category_ko: str,
    ts: str,
    category_en: str,
) -> dict:
    """단일 엔진으로 풀 구성 → 대본 생성 → G-Eval 실행"""
    from app.services.clustering_service import build_topic_weighted_pool
    from app.services.script_service import generate_script
    from app.services.eval_service import evaluate_script, format_eval_report
    from app.services.engines import get_engine

    logger.info(f"\n{'='*60}")
    logger.info(f"  엔진 실행: {engine_name}")
    logger.info(f"{'='*60}")

    t0 = time.time()

    # 엔진 생성 (Claude는 크레딧 없을 수 있음 → 실패 시 결과에 기록하고 계속)
    try:
        engine = get_engine(engine_name)
    except Exception as e:
        logger.error(f"엔진 초기화 실패 ({engine_name}): {e}")
        return {
            "engine": engine_name,
            "status": "init_failed",
            "error": str(e),
        }

    # 동일한 토픽 가중 풀 (엔진별로 풀은 같음)
    pool_articles, allocation_info = build_topic_weighted_pool(
        topics, articles, embeddings, target=50, min_per_topic=6
    )

    # 대본 생성
    try:
        script = generate_script(
            topics, category_ko,
            pool_articles=pool_articles,
            allocation_info=allocation_info,
            engine=engine,
        )
    except Exception as e:
        logger.exception(f"대본 생성 실패 ({engine_name}): {e}")
        return {
            "engine": engine_name,
            "status": "generation_failed",
            "error": str(e),
            "elapsed": time.time() - t0,
        }

    if not script:
        return {
            "engine": engine_name,
            "status": "empty_script",
            "elapsed": time.time() - t0,
        }

    # 대본 저장
    script_file = RESULTS_DIR / f"script_{category_en}_{engine_name}_{ts}.txt"
    script_file.write_text(script, encoding="utf-8")
    logger.info(f"📝 대본 저장: {script_file.name} ({len(script)}자)")
    logger.info(f"\n--- {engine_name} 대본 미리보기 (앞 400자) ---\n{script[:400]}\n---")

    # G-Eval (동일 judge: gpt-5.4)
    logger.info(f"\nG-Eval 평가 중 ({engine_name})...")
    eval_result = evaluate_script(script, articles)

    if eval_result:
        report = format_eval_report(eval_result)
        logger.info(f"\n--- {engine_name} G-Eval ---\n{report}\n---")

    return {
        "engine": engine_name,
        "status": "success",
        "script_file": str(script_file),
        "script_length": len(script),
        "eval": eval_result,
        "elapsed": round(time.time() - t0, 1),
    }


def main():
    parser = argparse.ArgumentParser(description="OpenAI vs Claude 대본 생성 비교")
    parser.add_argument("--category", default="economy")
    parser.add_argument(
        "--engines",
        nargs="+",
        default=["openai", "claude"],
        choices=["openai", "claude"],
        help="비교할 엔진 (기본 둘 다)"
    )
    args = parser.parse_args()

    from app.constants.category_map import API_TO_KO
    from app.services.embedding_service import embed_articles
    from app.services.clustering_service import (
        remove_near_duplicates,
        cluster_articles,
        rank_topics,
    )

    category_ko = API_TO_KO.get(args.category, args.category)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    logger.info(f"\n{'='*70}")
    logger.info(f"  대본 엔진 비교 실험: {category_ko}")
    logger.info(f"  엔진: {args.engines}")
    logger.info(f"{'='*70}\n")

    # 1. 데이터 로드
    articles = load_articles(args.category)
    if not articles:
        return
    logger.info(f"기사 {len(articles)}건 로드")

    # corpus coverage 계산용으로 dedup 전 전체 리스트 보존
    category_articles_full = list(articles)

    # 2. 임베딩 (캐시)
    logger.info("임베딩 생성...")
    embeddings = embed_articles(articles)

    # 3. Near-dup 제거
    from app.services.clustering_service import remove_near_duplicates
    import numpy as np
    keep = remove_near_duplicates(embeddings)
    articles = [articles[i] for i in keep]
    embeddings = embeddings[keep]

    # 4. 클러스터링
    logger.info("클러스터링...")
    labels, clusters, info = cluster_articles(embeddings)
    topics = rank_topics(
        clusters,
        articles,
        embeddings,
        top_n=5,
        articles_per_topic=3,
        category_articles=category_articles_full,
        use_weighted_score=True,
    )
    logger.info(f"토픽 {len(topics)}개 선정")
    for i, t in enumerate(topics):
        logger.info(
            f"  토픽 {i+1} ({t['size']}건): "
            f"{t['representative_article']['title'][:50]}..."
        )

    # 5. 각 엔진별 실행
    engine_results = {}
    for engine_name in args.engines:
        result = run_pipeline_for_engine(
            engine_name=engine_name,
            topics=topics,
            articles=articles,
            embeddings=embeddings,
            category_ko=category_ko,
            ts=ts,
            category_en=args.category,
        )
        engine_results[engine_name] = result

    # 6. 비교 테이블
    print(f"\n\n{'='*90}")
    print(f"{'ENGINE':<10} {'STATUS':<12} {'LEN':>6} {'OVERALL':>8} "
          f"{'NEUTR':>6} {'ACCUR':>6} {'READ':>6} {'COVER':>6} {'COH':>6} {'TIME':>7}")
    print(f"{'='*90}")

    for engine_name in args.engines:
        r = engine_results.get(engine_name, {})
        status = r.get("status", "?")
        length = r.get("script_length", "-")
        elapsed = r.get("elapsed", "-")

        if status == "success" and r.get("eval"):
            e = r["eval"]
            def s(dim):
                d = e.get(dim, {})
                v = d.get("score") if isinstance(d, dict) else None
                return str(v) if v is not None else "-"

            overall = e.get("overall_score", "-")
            print(f"{engine_name:<10} {'✅ ok':<12} {length:>6} "
                  f"{overall:>8} {s('neutrality'):>6} {s('accuracy'):>6} "
                  f"{s('readability'):>6} {s('coverage'):>6} "
                  f"{s('coherence'):>6} {elapsed:>6}s")
        else:
            print(f"{engine_name:<10} {status:<12} {length:>6} "
                  f"{'-':>8} {'-':>6} {'-':>6} {'-':>6} {'-':>6} {'-':>6} "
                  f"{elapsed:>6}")

    print(f"{'='*90}")

    # 7. 결과 저장
    output_file = RESULTS_DIR / f"engine_comparison_{args.category}_{ts}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "experiment_date": ts,
            "category": args.category,
            "category_ko": category_ko,
            "article_count": len(articles),
            "topic_count": len(topics),
            "engines": list(engine_results.keys()),
            "results": engine_results,
        }, f, ensure_ascii=False, indent=2)

    print(f"\n결과 저장: {output_file}")


if __name__ == "__main__":
    main()
