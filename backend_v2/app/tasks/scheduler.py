"""
Briefly v2 로컬 파이프라인 스케줄러

Ubuntu 노트북에서 cron으로 실행 (07:00, 18:00 KST).

전체 파이프라인:
  1. 뉴스 수집 (Naver)
  2. Near-Duplicate 제거
  3. 임베딩 (KURE-v1)
  4. 클러스터링 (UMAP + HDBSCAN)
  5. 토픽 랭킹 & 대표 기사 선정
  6. 팟캐스트 생성 (NotebookLM)
  7. 업로드 & 저장 (S3 + DynamoDB)

사용법:
    # 전체 파이프라인 실행
    python -m app.tasks.scheduler

    # 특정 카테고리만
    python -m app.tasks.scheduler --categories economy politics

    # 팟캐스트 생성 제외 (수집+클러스터링만)
    python -m app.tasks.scheduler --skip-podcast

cron 등록 (Ubuntu):
    crontab -e
    0 7 * * * cd /home/user/Briefly/backend_v2 && /usr/bin/python3 -m app.tasks.scheduler >> /var/log/briefly.log 2>&1
    0 18 * * * cd /home/user/Briefly/backend_v2 && /usr/bin/python3 -m app.tasks.scheduler >> /var/log/briefly.log 2>&1
"""

import os
import sys
import json
import time
import logging
import argparse
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

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
from app.utils.date import get_today_kst, get_now_kst

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def process_category(
    category_ko: str,
    config: dict,
    news_service: NaverNewsService,
    skip_podcast: bool = False,
) -> dict:
    """카테고리 하나에 대해 전체 파이프라인을 실행합니다."""
    category_en = config["api_name"]
    t0 = time.time()

    result = {
        "category": category_ko,
        "category_en": category_en,
        "status": "started",
    }

    try:
        from app.services.notify_service import log_step

        log_step(category_ko, "🚀 파이프라인 시작")
        logger.info(f"\n{'='*50}")
        logger.info(f"  [{category_ko}] 파이프라인 시작")
        logger.info(f"{'='*50}")

        # ── 1. 뉴스 수집 ──
        log_step(category_ko, "1️⃣ 뉴스 수집 시작")
        try:
            articles = news_service.collect_category(category_ko)
            result["collected"] = len(articles)
            log_step(category_ko, f"1️⃣ 수집 완료: {len(articles)}건")
        except Exception as e:
            log_step(category_ko, f"❌ 1️⃣ 뉴스 수집 실패: {str(e)[:100]}", color=0xFF0000)
            raise

        if len(articles) < 10:
            logger.warning(f"  [{category_ko}] 기사 {len(articles)}건 — 부족, 스킵")
            log_step(category_ko, f"⚠️ 기사 부족 ({len(articles)}건) — 스킵", color=0xFFAA00)
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

        # ── 5. 토픽 랭킹 (Phase 2 가중 점수) ──
        log_step(category_ko, "5️⃣ 토픽 랭킹 시작")
        try:
            logger.info(f"  [{category_ko}] 토픽 랭킹...")
            topics = rank_topics(
                clusters, articles, embeddings,
                top_n=5, articles_per_topic=3,
                category_articles=category_articles_full,
                use_weighted_score=True,
            )
            result["topics"] = len(topics)

            topic_lines = "\n".join(
                f"  {i+1}. ({t['size']}건) {t['representative_article'].get('title', '')[:40]}"
                for i, t in enumerate(topics)
            )
            log_step(category_ko, f"5️⃣ 토픽 랭킹 완료: {len(topics)}토픽", topic_lines)
        except Exception as e:
            log_step(category_ko, f"❌ 5️⃣ 토픽 랭킹 실패: {str(e)[:100]}", color=0xFF0000)
            raise

        for i, topic in enumerate(topics):
            logger.info(
                f"    토픽 {i+1} ({topic['size']}건): "
                f"{topic['representative_article'].get('title', '')[:50]}"
            )

        # ── 6. 오늘의 브리핑 헤드라인 생성 (Gemma4 로컬) ──
        log_step(category_ko, "6️⃣ 헤드라인 생성 시작 (Gemma4)")
        try:
            logger.info(f"  [{category_ko}] 헤드라인 생성...")
            from app.services.headline_service import generate_all_headlines
            topics_with_headlines = generate_all_headlines(topics)

            from app.services.storage_service import save_headlines
            from app.utils.date import get_today_kst as _today_hl
            save_headlines(
                category_en=category_en,
                date_str=_today_hl(),
                headlines=topics_with_headlines,
            )
            log_step(category_ko, f"6️⃣ 헤드라인 완료: {len(topics_with_headlines)}건 저장")
        except Exception as e:
            log_step(category_ko, f"❌ 6️⃣ 헤드라인 실패: {str(e)[:100]}", color=0xFF0000)
            raise

        # ── 7. 토픽별 비례 배분 풀 ──
        log_step(category_ko, "7️⃣ 소스 풀 구성 시작")
        try:
            pool_articles, allocation_info = build_topic_weighted_pool(
                topics, articles, embeddings, target=50, min_per_topic=6,
            )
            log_step(category_ko, f"7️⃣ 소스 풀 완료: {len(pool_articles)}건")
        except Exception as e:
            log_step(category_ko, f"❌ 7️⃣ 소스 풀 실패: {str(e)[:100]}", color=0xFF0000)
            raise

        # ── 8. 대본 생성 (gpt-5.4) ──
        log_step(category_ko, "8️⃣ 대본 생성 시작 (gpt-5.4)")
        try:
            logger.info(f"  [{category_ko}] 대본 생성...")
            script = generate_script(
                topics=topics,
                category_ko=category_ko,
                pool_articles=pool_articles,
                allocation_info=allocation_info,
            )
            result["script_length"] = len(script) if script else 0

            if not script:
                log_step(category_ko, "❌ 8️⃣ 대본 생성 실패 (빈 결과)", color=0xFF0000)
                result["status"] = "script_failed"
                return result

            log_step(category_ko, f"8️⃣ 대본 완료: {len(script)}자")
        except Exception as e:
            log_step(category_ko, f"❌ 8️⃣ 대본 생성 실패: {str(e)[:100]}", color=0xFF0000)
            raise

        # 대본 저장 (항상)
        from app.utils.date import get_today_kst, get_now_kst as _now
        script_dir = Path("outputs") / "scripts"
        script_dir.mkdir(parents=True, exist_ok=True)
        script_filename = f"script_{category_en}_{get_today_kst()}_{_now().strftime('%H%M%S')}.txt"
        script_path = script_dir / script_filename
        script_path.write_text(script, encoding="utf-8")
        result["script_path"] = str(script_path)
        logger.info(f"  📝 대본 저장: {script_path}")

        # ── 9. 팟캐스트 오디오 생성 (NotebookLM) ──
        if not skip_podcast:
            log_step(category_ko, "9️⃣ NotebookLM 오디오 생성 시작 (~15분)")
            try:
                logger.info(f"  [{category_ko}] NotebookLM 오디오 생성...")
                from app.services.notebooklm_service import generate_podcast

                audio_path = generate_podcast(
                    script=script,
                    category_ko=category_ko,
                )
                result["podcast"] = audio_path or "failed"
                if audio_path:
                    log_step(category_ko, f"9️⃣ 오디오 완료: {Path(audio_path).name}")
                else:
                    log_step(category_ko, "❌ 9️⃣ 오디오 생성 실패 (결과 없음)", color=0xFF0000)
            except Exception as e:
                log_step(category_ko, f"❌ 9️⃣ 오디오 생성 실패: {str(e)[:100]}", color=0xFF0000)
                result["podcast"] = "failed"
                # 오디오 실패는 파이프라인을 중단하지 않음
        else:
            result["podcast"] = "skipped"
            log_step(category_ko, "9️⃣ 오디오 생략 (--skip-podcast)")

        # ── 10. S3 + DynamoDB 저장 ──
        log_step(category_ko, "🔟 S3 + DynamoDB 저장 시작")
        try:
            from app.services.storage_service import save_pipeline_result
            from app.utils.date import get_today_kst as _today

            audio_file = result.get("podcast")
            if audio_file in ("skipped", "failed", None):
                audio_file = None

            storage = save_pipeline_result(
                category_en=category_en,
                date_str=_today(),
                script=script,
                audio_path=audio_file,
            )
            result["storage"] = storage
            log_step(category_ko, f"🔟 저장 완료: {storage['frequency_id']}")
        except Exception as e:
            log_step(category_ko, f"❌ 🔟 저장 실패: {str(e)[:100]}", color=0xFF0000)
            raise

        result["status"] = "success"
        result["elapsed_sec"] = round(time.time() - t0, 1)

        log_step(category_ko, f"🏁 파이프라인 완료 ({result['elapsed_sec']:.0f}초)", color=0x00FF00)
        logger.info(
            f"✅ [{category_ko}] 완료: {result['collected']}건 수집 → "
            f"{result['after_dedup']}건 중복제거 → "
            f"{result['clustering']['n_clusters']}개 토픽 "
            f"({result['elapsed_sec']}초)"
        )

    except Exception as e:
        logger.exception(f"❌ [{category_ko}] 파이프라인 실패: {e}")
        result["status"] = "failed"
        result["error"] = str(e)
        result["elapsed_sec"] = round(time.time() - t0, 1)

        from app.services.notify_service import notify_pipeline_error
        notify_pipeline_error(category_ko, str(e))

    return result


def run_pipeline(
    categories: list = None,
    skip_podcast: bool = False,
):
    """전체 파이프라인을 실행합니다."""
    total_start = time.time()
    now = get_now_kst()

    logger.info(f"{'='*60}")
    logger.info(f"  Briefly v2 파이프라인 시작")
    logger.info(f"  시각: {now.strftime('%Y-%m-%d %H:%M:%S')} KST")
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

    logger.info(f"  대상 카테고리: {list(target.keys())}")

    news_service = NaverNewsService(request_delay=0.2)
    all_results = []

    # 카테고리별 순차 처리 (KURE-v1 모델 메모리 공유)
    for cat_ko, config in target.items():
        result = process_category(
            cat_ko, config, news_service, skip_podcast
        )
        all_results.append(result)

    # 요약
    total_elapsed = time.time() - total_start

    logger.info(f"\n{'='*60}")
    logger.info(f"  파이프라인 완료 ({total_elapsed:.0f}초)")
    logger.info(f"{'='*60}")

    for r in all_results:
        status_icon = "✅" if r["status"] == "success" else "❌"
        logger.info(
            f"  {status_icon} {r['category']}: {r.get('collected', 0)}건 → "
            f"{r.get('clustering', {}).get('n_clusters', '?')}개 토픽 "
            f"({r.get('elapsed_sec', 0)}초)"
        )

    # Discord 완료 알림
    from app.services.notify_service import notify_pipeline_success
    notify_pipeline_success(all_results)

    # 결과 JSON 저장
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    ts = now.strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"pipeline_result_{ts}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": ts,
            "elapsed_sec": round(total_elapsed, 1),
            "results": all_results,
        }, f, ensure_ascii=False, indent=2)

    logger.info(f"  결과 저장: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Briefly v2 파이프라인")
    parser.add_argument(
        "--categories", nargs="*",
        help="카테고리 필터 (예: economy politics)"
    )
    parser.add_argument(
        "--skip-podcast", action="store_true",
        help="팟캐스트 생성 건너뛰기 (수집+클러스터링만)"
    )
    args = parser.parse_args()

    run_pipeline(
        categories=args.categories,
        skip_podcast=args.skip_podcast,
    )


if __name__ == "__main__":
    main()
