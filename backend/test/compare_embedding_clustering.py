"""
임베딩 모델 × 클러스터링 알고리즘 교차 비교 실험

같은 뉴스 데이터에 대해:
  - 임베딩: OpenAI text-embedding-3-small vs KURE-v1 (로컬)
  - 클러스터링: HDBSCAN vs Multi-DBSCAN vs Union-Find

총 2 × 3 = 6가지 조합 비교

사용법:
    cd backend/test
    python compare_embedding_clustering.py --category economy --date 2025-12-02

출력:
    results/embedding_clustering_comparison_{timestamp}.json
"""

import os
import sys
import json
import time
import argparse
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)
print(f"[env] loaded from {env_path} (exists={env_path.exists()})")

from app.utils.dynamo import get_news_by_category_and_date
from algorithms.hdbscan_clustering import cluster_with_hdbscan
from algorithms.multi_dbscan_clustering import cluster_with_multi_dbscan
from algorithms.unionfind_clustering import cluster_with_unionfind

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


# ============================================================
# 임베딩 생성
# ============================================================

def embed_with_openai(texts: List[str], model: str = "text-embedding-3-large") -> np.ndarray:
    """OpenAI API 임베딩"""
    from openai import OpenAI
    client = OpenAI()

    print(f"  OpenAI ({model}) 임베딩 생성 중... ({len(texts)}개)")
    start = time.time()

    embeddings = []
    batch_size = 50
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        res = client.embeddings.create(input=batch, model=model)
        embeddings.extend([d.embedding for d in res.data])
        print(f"    {min(i + batch_size, len(texts))}/{len(texts)} 완료")

    elapsed = time.time() - start
    result = np.array(embeddings)
    print(f"  완료: {result.shape}, {elapsed:.1f}초 (임베딩 생성 소요시간)")
    return result, elapsed


def embed_with_kure(texts: List[str]) -> np.ndarray:
    """KURE-v1 로컬 임베딩"""
    from sentence_transformers import SentenceTransformer

    model_name = "nlpai-lab/KURE-v1"
    print(f"  KURE-v1 ({model_name}) 로딩 중...")
    start_load = time.time()
    model = SentenceTransformer(model_name)
    load_time = time.time() - start_load
    print(f"  모델 로드 완료: {load_time:.1f}초")

    print(f"  임베딩 생성 중... ({len(texts)}개)")
    start = time.time()
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
    elapsed = time.time() - start
    print(f"  완료: {embeddings.shape}, {elapsed:.1f}초 (임베딩 생성 소요시간, 모델 로드 {load_time:.1f}초 별도)")
    return np.array(embeddings), elapsed + load_time


# ============================================================
# 클러스터링 실행
# ============================================================

def run_clustering_suite(
    embeddings: np.ndarray,
    embedding_name: str,
) -> List[Dict]:
    """하나의 임베딩에 대해 모든 클러스터링 알고리즘 실행"""
    from sklearn.metrics import silhouette_score

    results = []

    configs = [
        ("hdbscan_mcs3", lambda e: cluster_with_hdbscan(e, min_cluster_size=3)),
        ("hdbscan_mcs4", lambda e: cluster_with_hdbscan(e, min_cluster_size=4)),
        ("hdbscan_mcs5", lambda e: cluster_with_hdbscan(e, min_cluster_size=5)),
        ("multi_dbscan_moderate", lambda e: cluster_with_multi_dbscan(e, eps_list=[0.3, 0.45, 0.6], min_samples=3)),
        ("multi_dbscan_aggressive", lambda e: cluster_with_multi_dbscan(e, eps_list=[0.4, 0.55, 0.7], min_samples=3)),
        ("multi_dbscan_wide", lambda e: cluster_with_multi_dbscan(e, eps_list=[0.5, 0.65, 0.8], min_samples=3)),
        ("unionfind_t070", lambda e: cluster_with_unionfind(e, similarity_threshold=0.70, enable_outlier_filter=True)),
        ("unionfind_t080", lambda e: cluster_with_unionfind(e, similarity_threshold=0.80, enable_outlier_filter=True)),
        ("unionfind_t085", lambda e: cluster_with_unionfind(e, similarity_threshold=0.85, enable_outlier_filter=True)),
    ]

    for algo_name, algo_fn in configs:
        print(f"\n    [{embedding_name}] {algo_name}...")

        labels, clusters, info = algo_fn(embeddings)

        # 메트릭
        cluster_sizes = [len(m) for m in clusters.values()]
        n_noise = int(np.sum(labels == -1))
        n_clusters = len(clusters)

        result = {
            "embedding": embedding_name,
            "algorithm": algo_name,
            "n_clusters": n_clusters,
            "noise_count": n_noise,
            "noise_ratio": n_noise / len(labels) if len(labels) > 0 else 0,
            "cluster_sizes": sorted(cluster_sizes, reverse=True),
            "mean_cluster_size": float(np.mean(cluster_sizes)) if cluster_sizes else 0,
            "max_cluster_size": max(cluster_sizes) if cluster_sizes else 0,
            "singleton_clusters": sum(1 for s in cluster_sizes if s == 1),
            "execution_time": info.get("execution_time", 0),
        }

        # Silhouette score
        non_noise = labels != -1
        n_non = non_noise.sum()
        n_unique = len(set(labels[non_noise]))
        if n_non > 1 and 2 <= n_unique < n_non:
            try:
                result["silhouette"] = float(silhouette_score(
                    embeddings[non_noise], labels[non_noise], metric="cosine"
                ))
            except ValueError:
                pass

        # Pass 상세 (Multi-DBSCAN)
        if "pass_stats" in info:
            result["pass_stats"] = info["pass_stats"]

        results.append(result)

        # 간단 출력
        sil = f"{result['silhouette']:.3f}" if 'silhouette' in result else 'N/A'
        print(f"      clusters={n_clusters}, noise={n_noise}, sil={sil}, "
              f"sizes={sorted(cluster_sizes, reverse=True)[:8]}{'...' if len(cluster_sizes) > 8 else ''}")

    return results


# ============================================================
# 클러스터 내용 샘플 출력 (정성 평가용)
# ============================================================

def print_cluster_samples(
    labels: np.ndarray,
    clusters: Dict[int, List[int]],
    articles: List[Dict],
    top_n: int = 5,
):
    """상위 N개 클러스터의 기사 제목을 출력합니다."""
    sorted_clusters = sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True)

    for rank, (cid, members) in enumerate(sorted_clusters[:top_n], 1):
        print(f"\n  --- 토픽 {rank} ({len(members)}개 기사) ---")
        for idx in members[:5]:
            title = articles[idx].get("title", "N/A")[:60]
            press = articles[idx].get("provider", "")
            print(f"    [{press}] {title}")
        if len(members) > 5:
            print(f"    ... +{len(members)-5}개")


# ============================================================
# 메인
# ============================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", default="economy")
    parser.add_argument("--date", default="2025-12-02")
    parser.add_argument("--limit", type=int, default=None, help="기사 수 제한 (테스트용)")
    args = parser.parse_args()

    print(f"{'='*70}")
    print(f"  임베딩 × 클러스터링 교차 비교 실험")
    print(f"  카테고리: {args.category}, 날짜: {args.date}")
    print(f"{'='*70}\n")

    # 1. 데이터 로드
    print("1. DynamoDB에서 기사 로드...")
    articles = get_news_by_category_and_date(args.category, args.date)
    if not articles:
        print("기사가 없습니다.")
        return

    if args.limit:
        articles = articles[:args.limit]
    print(f"   {len(articles)}개 기사 로드됨\n")

    # 텍스트 준비 (제목 + 본문, 1000자 제한)
    texts = []
    for a in articles:
        text = a.get("title", "") + " " + (a.get("content") or a.get("hilight", ""))
        texts.append(text[:1000])

    # 2. 임베딩 생성 (두 모델)
    print("2. 임베딩 생성...")
    # 임베딩 캐시 (재실행 시 비용/시간 절약)
    cache_dir = RESULTS_DIR / "embedding_cache"
    cache_dir.mkdir(exist_ok=True)
    cache_key = f"{args.category}_{args.date}_{len(texts)}"

    openai_cache = cache_dir / f"openai_large_{cache_key}.npy"
    kure_cache = cache_dir / f"kure_v1_{cache_key}.npy"

    if openai_cache.exists():
        print(f"\n  === OpenAI text-embedding-3-large (캐시 로드) ===")
        emb_openai = np.load(str(openai_cache))
        time_openai = 0.0
        print(f"  캐시 로드 완료: {emb_openai.shape}")
    else:
        print(f"\n  === OpenAI text-embedding-3-large ===")
        emb_openai, time_openai = embed_with_openai(texts)
        np.save(str(openai_cache), emb_openai)

    if kure_cache.exists():
        print(f"\n  === KURE-v1 (캐시 로드) ===")
        emb_kure = np.load(str(kure_cache))
        time_kure = 0.0
        print(f"  캐시 로드 완료: {emb_kure.shape}")
    else:
        print(f"\n  === KURE-v1 (로컬) ===")
        emb_kure, time_kure = embed_with_kure(texts)
        np.save(str(kure_cache), emb_kure)

    print(f"\n  임베딩 차원 비교: OpenAI={emb_openai.shape[1]}, KURE-v1={emb_kure.shape[1]}")
    print(f"  임베딩 소요시간: OpenAI={time_openai:.1f}초, KURE-v1={time_kure:.1f}초")

    # 3. 클러스터링 실행
    print(f"\n3. 클러스터링 비교 실행...")
    print(f"\n{'='*50}")
    print(f"  OpenAI 임베딩 기반 클러스터링")
    print(f"{'='*50}")
    results_openai = run_clustering_suite(emb_openai, "openai")

    print(f"\n{'='*50}")
    print(f"  KURE-v1 임베딩 기반 클러스터링")
    print(f"{'='*50}")
    results_kure = run_clustering_suite(emb_kure, "kure_v1")

    all_results = results_openai + results_kure

    # 4. 최고 성능 조합으로 클러스터 내용 출력 (정성 평가)
    print(f"\n\n{'='*70}")
    print(f"  정성 평가: 최고 silhouette 조합의 클러스터 내용")
    print(f"{'='*70}")

    # OpenAI + HDBSCAN 클러스터 샘플
    print(f"\n  >>> OpenAI + HDBSCAN (mcs=3) <<<")
    labels_o, clusters_o, _ = cluster_with_hdbscan(emb_openai, min_cluster_size=3)
    print_cluster_samples(labels_o, clusters_o, articles)

    # KURE + HDBSCAN 클러스터 샘플
    print(f"\n  >>> KURE-v1 + HDBSCAN (mcs=3) <<<")
    labels_k, clusters_k, _ = cluster_with_hdbscan(emb_kure, min_cluster_size=3)
    print_cluster_samples(labels_k, clusters_k, articles)

    # 5. 비교 테이블
    print(f"\n\n{'='*95}")
    print(f"{'EMBEDDING':<12} {'ALGORITHM':<25} {'CLUST':>5} {'NOISE':>5} {'NOISE%':>7} {'SIL':>7} {'MAX':>5} {'TIME':>7}")
    print(f"{'='*95}")

    for r in sorted(all_results, key=lambda x: x.get("silhouette", -2), reverse=True):
        sil = f"{r['silhouette']:.4f}" if "silhouette" in r else "  N/A"
        noise_pct = f"{r['noise_ratio']:.1%}"
        print(f"{r['embedding']:<12} {r['algorithm']:<25} {r['n_clusters']:>5} "
              f"{r['noise_count']:>5} {noise_pct:>7} {sil:>7} "
              f"{r['max_cluster_size']:>5} {r['execution_time']:>6.3f}s")

    print(f"{'='*95}")

    # 6. 결과 저장
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = {
        "experiment_date": ts,
        "data": {"category": args.category, "date": args.date, "article_count": len(articles)},
        "embeddings": {
            "openai": {"model": "text-embedding-3-large", "dim": int(emb_openai.shape[1]), "elapsed_sec": round(time_openai, 2)},
            "kure_v1": {"model": "nlpai-lab/KURE-v1", "dim": int(emb_kure.shape[1]), "elapsed_sec": round(time_kure, 2)},
        },
        "results": all_results,
    }

    def convert(obj):
        if isinstance(obj, (np.integer,)): return int(obj)
        if isinstance(obj, (np.floating,)): return float(obj)
        if isinstance(obj, np.ndarray): return obj.tolist()
        return obj

    output_file = RESULTS_DIR / f"embedding_clustering_comparison_{ts}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2, default=convert)

    print(f"\n결과 저장: {output_file}")


if __name__ == "__main__":
    main()
