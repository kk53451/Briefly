"""
UMAP 차원 축소 + HDBSCAN 실험

UMAP n_components를 여러 값으로 바꿔가며 클러스터링 품질을 비교.
캐시된 KURE-v1 임베딩을 재사용합니다.

사용법:
    cd backend/test
    python compare_umap_dimensions.py
"""

import sys
import json
import time
import numpy as np
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from app.utils.dynamo import get_news_by_category_and_date
from algorithms.hdbscan_clustering import cluster_with_hdbscan

RESULTS_DIR = Path(__file__).parent / "results"

def run():
    # 캐시된 임베딩 로드
    cache_file = RESULTS_DIR / "embedding_cache" / "kure_v1_economy_2025-12-02_227.npy"
    if not cache_file.exists():
        print(f"캐시 파일 없음: {cache_file}")
        print("먼저 compare_embedding_clustering.py 를 실행하세요.")
        return

    print("1. 캐시된 KURE-v1 임베딩 로드...")
    embeddings = np.load(str(cache_file))
    print(f"   shape: {embeddings.shape}")

    # 기사 제목 로드 (정성 평가용)
    articles = get_news_by_category_and_date("economy", "2025-12-02")
    print(f"   기사 {len(articles)}개 로드\n")

    # UMAP 차원 실험
    import umap
    from sklearn.metrics import silhouette_score

    dimensions = [5, 10, 15, 25, 50, 100, 1024]  # 1024 = UMAP 없이 원본
    mcs_values = [3, 5, 8, 10]

    results = []

    for n_dim in dimensions:
        if n_dim >= embeddings.shape[1]:
            # 원본 (UMAP 안 함)
            reduced = embeddings.astype(np.float64)
            umap_time = 0.0
            label = f"원본({embeddings.shape[1]}d)"
        else:
            print(f"UMAP → {n_dim}d 축소 중...", end=" ", flush=True)
            start = time.time()
            reducer = umap.UMAP(
                n_components=n_dim,
                n_neighbors=15,
                min_dist=0.0,
                metric="cosine",
                random_state=42,
            )
            reduced = reducer.fit_transform(embeddings)
            umap_time = time.time() - start
            label = f"UMAP→{n_dim}d"
            print(f"{umap_time:.1f}초")

        for mcs in mcs_values:
            labels, clusters, info = cluster_with_hdbscan(
                reduced, min_cluster_size=mcs, metric="euclidean"
            )

            n_clusters = len(clusters)
            noise = int(np.sum(labels == -1))
            noise_ratio = noise / len(labels)
            sizes = sorted([len(m) for m in clusters.values()], reverse=True)

            # Silhouette
            sil = None
            non_noise = labels != -1
            n_non = non_noise.sum()
            n_unique = len(set(labels[non_noise]))
            if n_non > 1 and 2 <= n_unique < n_non:
                try:
                    sil = float(silhouette_score(
                        reduced[non_noise], labels[non_noise], metric="euclidean"
                    ))
                except ValueError:
                    pass

            result = {
                "dim": n_dim if n_dim < embeddings.shape[1] else "원본",
                "label": label,
                "mcs": mcs,
                "n_clusters": n_clusters,
                "noise": noise,
                "noise_ratio": noise_ratio,
                "silhouette": sil,
                "sizes_top8": sizes[:8],
                "umap_time": umap_time,
                "cluster_time": info.get("execution_time", 0),
            }
            results.append(result)

    # 결과 테이블
    print(f"\n{'='*105}")
    print(f"{'DIM':<12} {'MCS':>3} {'CLUST':>5} {'NOISE':>5} {'NOISE%':>7} {'SIL':>8} {'TOP SIZES':<40} {'TIME':>7}")
    print(f"{'='*105}")

    for r in sorted(results, key=lambda x: x.get("silhouette") or -2, reverse=True):
        sil = f"{r['silhouette']:.4f}" if r['silhouette'] is not None else "   N/A"
        sizes_str = str(r['sizes_top8'])
        if len(sizes_str) > 38:
            sizes_str = sizes_str[:38] + ".."
        total_time = r['umap_time'] + r['cluster_time']
        print(f"{r['label']:<12} {r['mcs']:>3} {r['n_clusters']:>5} {r['noise']:>5} "
              f"{r['noise_ratio']:>6.1%} {sil:>8} {sizes_str:<40} {total_time:>6.2f}s")

    print(f"{'='*105}")

    # 최적 조합으로 클러스터 내용 출력
    best = max([r for r in results if r['silhouette'] is not None],
               key=lambda x: x['silhouette'])
    print(f"\n최고 Silhouette: {best['label']} + mcs={best['mcs']} "
          f"(sil={best['silhouette']:.4f}, clusters={best['n_clusters']}, noise={best['noise']})")

    # 최적 조합 재실행 + 내용 출력
    if best['dim'] == "원본":
        best_reduced = embeddings.astype(np.float64)
    else:
        reducer = umap.UMAP(n_components=best['dim'], n_neighbors=15, min_dist=0.0,
                           metric="cosine", random_state=42)
        best_reduced = reducer.fit_transform(embeddings)

    labels, clusters, _ = cluster_with_hdbscan(best_reduced, min_cluster_size=best['mcs'],
                                                metric="euclidean")

    sorted_clusters = sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True)
    print(f"\n--- 토픽 내용 (상위 8개) ---")
    for rank, (cid, members) in enumerate(sorted_clusters[:8], 1):
        print(f"\n  토픽 {rank} ({len(members)}개):")
        for idx in members[:4]:
            title = articles[idx].get("title", "")[:55]
            press = articles[idx].get("provider", "")
            print(f"    [{press}] {title}")
        if len(members) > 4:
            print(f"    ... +{len(members)-4}개")

    # 저장
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = RESULTS_DIR / f"umap_dimension_comparison_{ts}.json"

    def convert(obj):
        if isinstance(obj, (np.integer,)): return int(obj)
        if isinstance(obj, (np.floating,)): return float(obj)
        if isinstance(obj, np.ndarray): return obj.tolist()
        return obj

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=convert)
    print(f"\n결과 저장: {output_file}")


if __name__ == "__main__":
    run()
