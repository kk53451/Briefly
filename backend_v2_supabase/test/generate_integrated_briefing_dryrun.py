"""
통합 브리핑 대본 dry-run (NotebookLM 오디오 생성 없이 대본만).

===============================================================================
이 스크립트를 왜 유지하는가 (2026-04-19 메모)
===============================================================================
`python -m app.tasks.scheduler --skip-podcast` 로도 유사한 결과를 얻을 수 있어
중복처럼 보일 수 있습니다. 그럼에도 이 파일은 **의도적으로 유지** 됩니다.

차이점:
- scheduler 경로는 Naver 실시간 수집·임베딩·KURE 모델 로드까지 거쳐
  6 카테고리를 다 돌리므로 1시간 이상 걸립니다. Supabase/Discord 등 외부
  의존성도 건드립니다.
- 이 dry-run 은 `backend/test/data/news_*.json` **오프라인 샘플 데이터**를
  재활용하고, 하드뉴스 3카테고리만 돌리며, Supabase 저장/알림을 건너뜁니다.
  임베딩 캐시가 이미 있으면 총 4~6분에 끝나 프롬프트 변경(SYSTEM_PROMPT,
  GENERATION_PROMPT_TEMPLATE, instructions, REF 토픽 구성 등) 에 대한
  **품질 회귀 체크용 fast feedback loop** 로 쓰입니다.

즉 이건 **개발·튜닝용 로컬 유틸** 입니다. 프로덕션 파이프라인과는 완전 분리.

스크립트 교체/삭제 기준:
- 샘플 데이터 경로(`backend/test/data/news_*.json`) 가 사라지거나,
  `categories_data` 인자 형태가 다시 바뀌거나,
- 프롬프트 튜닝이 수렴해서 더 이상 빠른 iteration 이 필요 없어지면
  그때 삭제 고려.
===============================================================================

사용:
    cd backend_v2_supabase
    python -X utf8 -m test.generate_integrated_briefing_dryrun
    python -X utf8 -m test.generate_integrated_briefing_dryrun --time-slot 오후 --target-length 6000

필수 환경변수: OPENAI_API_KEY (임베딩 제외, 대본 생성에 필요).
임베딩은 로컬 KURE 모델을 씁니다.
"""

import argparse
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# 통합 브리핑에 포함되는 3개 하드뉴스 카테고리 (순서 고정)
HARD_NEWS: List[Dict[str, str]] = [
    {"ko": "정치", "en": "politics"},
    {"ko": "경제", "en": "economy"},
    {"ko": "국제", "en": "international"},
]

DATA_PATH = Path("../backend/test/data/news_2026-04-11.json")
OUTPUT_DIR = Path("test/results")


def load_articles_for_category(data: dict, category_en: str) -> List[Dict]:
    """샘플 JSON 에서 단일 카테고리 기사 리스트를 뽑아냅니다."""
    articles = data.get("articles", data) if isinstance(data, dict) else data
    return [a for a in articles if a.get("category") == category_en]


def build_category_data(
    category_ko: str,
    category_en: str,
    articles_raw: List[Dict],
    top_n: int,
) -> Dict:
    """단일 카테고리에 대해 임베딩→dedup→클러스터링→rank→풀 을 끝까지 돌립니다.

    Returns:
        {"category_ko", "topics", "pool_articles", "allocation_info"} — generate_script 입력 형식.
    """
    from app.services.embedding_service import embed_articles, unload_model
    from app.services.clustering_service import (
        remove_near_duplicates,
        cluster_articles,
        rank_topics,
        build_topic_weighted_pool,
    )

    logger.info(f"\n[{category_ko}] 기사 {len(articles_raw)}건으로 feed phase 시작")
    if len(articles_raw) < 20:
        raise RuntimeError(f"[{category_ko}] 기사 부족: {len(articles_raw)}건")

    articles = list(articles_raw)
    category_articles_full = list(articles)

    # 1. 임베딩
    embeddings = embed_articles(articles)
    logger.info(f"  🧬 임베딩: shape={embeddings.shape}")

    # 2. Near-dup 제거
    keep = remove_near_duplicates(embeddings, threshold=0.95)
    articles = [articles[i] for i in keep]
    embeddings = embeddings[keep]
    logger.info(f"  🔍 dedup 후: {len(articles)}건")

    # 3. 클러스터링
    _labels, clusters, cinfo = cluster_articles(embeddings, n_articles=len(articles))
    logger.info(
        f"  🎯 클러스터링: {cinfo['n_clusters']}개, "
        f"noise {cinfo['noise_ratio']:.1%}, "
        f"최대 {cinfo['max_cluster_size']}"
    )

    # 4. 토픽 랭킹 (Phase 2 가중 점수)
    topics = rank_topics(
        clusters,
        articles,
        embeddings,
        top_n=top_n,
        articles_per_topic=3,
        category_articles=category_articles_full,
        use_weighted_score=True,
    )
    logger.info(f"  📊 top {len(topics)} 토픽:")
    for i, t in enumerate(topics):
        title = t.get("representative_article", {}).get("title", "")[:50]
        logger.info(f"    {i+1}. ({t['size']}건) {title}")

    # 5. 토픽별 비례 배분 풀
    pool_articles, allocation_info = build_topic_weighted_pool(
        topics, articles, embeddings, target=50, min_per_topic=6,
    )
    logger.info(f"  📦 pool: {len(pool_articles)}건")
    for info in allocation_info:
        logger.info(
            f"    Topic {info.get('topic_id')} (size={info.get('topic_size')}): "
            f"{info.get('allocated')}건"
        )

    return {
        "category_ko": category_ko,
        "topics": topics,
        "pool_articles": pool_articles,
        "allocation_info": allocation_info,
    }


def main():
    parser = argparse.ArgumentParser(description="통합 브리핑 대본 dry-run")
    parser.add_argument(
        "--time-slot",
        choices=["오전", "오후", "morning", "afternoon"],
        default="오전",
        help="대본의 오프닝/클로징에 반영할 time_slot (기본: 오전)",
    )
    parser.add_argument(
        "--target-length", type=int, default=6000,
        help="목표 대본 길이 (한글 글자 수, 기본 6000 = 8~10분 타깃)",
    )
    parser.add_argument(
        "--topics-per-category", type=int, default=3,
        help="카테고리당 포함할 top 토픽 수 (기본 3)",
    )
    parser.add_argument(
        "--data-path",
        default=str(DATA_PATH),
        help="샘플 기사 JSON 경로",
    )
    args = parser.parse_args()

    # time_slot 정규화 (영문 → 한글)
    ts_map = {"morning": "오전", "afternoon": "오후", "오전": "오전", "오후": "오후"}
    time_slot_ko = ts_map[args.time_slot]

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    logger.info("=" * 70)
    logger.info(f"  통합 브리핑 대본 dry-run ({time_slot_ko})")
    logger.info(f"  하드뉴스: {[c['ko'] for c in HARD_NEWS]}")
    logger.info(f"  카테고리당 top {args.topics_per_category} 토픽, 목표 {args.target_length}자")
    logger.info("=" * 70)

    # 기사 로드
    data_path = Path(args.data_path)
    if not data_path.exists():
        logger.error(f"❌ 샘플 데이터 없음: {data_path}")
        return

    with open(data_path, encoding="utf-8") as f:
        data = json.load(f)

    # 카테고리별 feed phase
    categories_data: List[Dict] = []
    for cat in HARD_NEWS:
        raw = load_articles_for_category(data, cat["en"])
        try:
            cd = build_category_data(
                cat["ko"], cat["en"], raw, top_n=args.topics_per_category
            )
            categories_data.append(cd)
        except Exception as e:
            logger.error(f"❌ [{cat['ko']}] feed phase 실패: {e}")
            return

    # 임베딩 모델 메모리 해제 (GPT 호출 전)
    try:
        from app.services.embedding_service import unload_model
        unload_model()
    except Exception:
        pass

    # ── NotebookLM REF 소스 시뮬레이션 (실제 호출은 하지 않음) ──
    # 스케줄러의 generate_integrated_briefing 과 동일 로직으로 각 토픽의
    # selected_articles 상위 N건을 모아 총 건수·타이틀 미리보기를 출력.
    from app.tasks.scheduler import (
        PODCAST_REF_ARTICLES_PER_TOPIC as REF_PER_TOPIC,
    )
    reference_articles: List[Dict] = []
    for cd in categories_data:
        cat_ko = cd["category_ko"]
        for topic in cd["topics"]:
            sel = topic.get("selected_articles") or []
            for a in sel[:REF_PER_TOPIC]:
                if not isinstance(a, dict):
                    continue
                tagged = dict(a)
                tagged.setdefault("category_ko", cat_ko)
                reference_articles.append(tagged)

    logger.info("\n" + "=" * 70)
    logger.info(f"  📚 NotebookLM REF 소스 프리뷰 ({len(reference_articles)}건)")
    logger.info(f"     {len(categories_data)}분야 × {args.topics_per_category}토픽 × "
                f"{REF_PER_TOPIC}기사 상한")
    logger.info("=" * 70)
    for i, a in enumerate(reference_articles, 1):
        press = a.get("press") or a.get("provider", "")
        title = (a.get("title") or "")[:60]
        logger.info(f"  [REF][{a.get('category_ko','?')}] ({press}) {title}")

    logger.info("\n" + "=" * 70)
    logger.info("  📝 통합 브리핑 대본 생성 (OpenAI)")
    logger.info("=" * 70)

    from app.services.script_service import generate_script
    t0 = time.time()
    script = generate_script(
        categories_data=categories_data,
        time_slot=time_slot_ko,
        target_length=args.target_length,
    )
    elapsed = time.time() - t0

    if not script:
        logger.error("❌ 대본 생성 실패 (빈 결과)")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"briefing_dryrun_{time_slot_ko}_{ts}.txt"
    out_path.write_text(script, encoding="utf-8")

    logger.info("")
    logger.info("=" * 70)
    logger.info(f"✅ 대본 저장: {out_path}")
    logger.info(f"   길이: {len(script)}자, 생성 시간: {elapsed:.1f}초")
    logger.info("=" * 70)

    # ── 프리뷰: 오프닝 / 카테고리 전환 / 클로징 ──
    logger.info("\n--- OPENING (첫 600자) ---")
    logger.info(script[:600])

    logger.info("\n--- CLOSING (마지막 500자) ---")
    logger.info(script[-500:])

    # 분야 키워드가 대본 어디에 처음 나타나는지 간단 지표
    logger.info("\n--- 카테고리 키워드 등장 위치 ---")
    for cat in HARD_NEWS:
        idx = script.find(cat["ko"])
        if idx < 0:
            logger.info(f"  {cat['ko']}: (명시적 언급 없음 — 브릿지 의미적일 가능성)")
        else:
            logger.info(f"  {cat['ko']}: 첫 등장 offset {idx} / {len(script)}")


if __name__ == "__main__":
    main()
