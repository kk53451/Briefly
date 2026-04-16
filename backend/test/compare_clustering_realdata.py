"""
실제 뉴스 데이터(3,951건)로 UMAP + HDBSCAN 클러스터링 실험

로컬 JSON 데이터 → KURE-v1 임베딩 → UMAP(15d) → HDBSCAN(mcs 다양) 비교
카테고리별로 실행하여 최적 mcs를 찾습니다.

사용법:
    cd backend
    python test/compare_clustering_realdata.py

    # 특정 카테고리만
    python test/compare_clustering_realdata.py --categories economy politics
"""

import sys
import json
import time
import argparse
import numpy as np
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

RESULTS_DIR = Path(__file__).parent / "results"
DATA_DIR = Path(__file__).parent / "data"
CACHE_DIR = RESULTS_DIR / "embedding_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def load_articles(date: str, category: str = None):
    """로컬 JSON에서 기사 로드"""
    path = DATA_DIR / f"news_{date}.json"
    if not path.exists():
        print(f"파일 없음: {path}")
        return []

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    articles = data["articles"]
    if category:
        articles = [a for a in articles if a.get("category") == category]

    return articles


def embed_articles(texts, category, date):
    """KURE-v1 임베딩 (캐시 지원)"""
    cache_key = f"kure_v1_realdata_{category}_{date}_{len(texts)}"
    cache_file = CACHE_DIR / f"{cache_key}.npy"

    if cache_file.exists():
        print(f"    캐시 로드: {cache_file.name}")
        return np.load(str(cache_file))

    from sentence_transformers import SentenceTransformer

    print(f"    KURE-v1 임베딩 생성 중 ({len(texts)}건)...")
    model = SentenceTransformer("nlpai-lab/KURE-v1")
    t0 = time.time()
    embeddings = model.encode(texts, batch_size=32, show_progress_bar=True)
    elapsed = time.time() - t0
    print(f"    완료: {elapsed:.1f}초")

    np.save(str(cache_file), embeddings)
    del model
    return embeddings


def run_clustering(embeddings, mcs_values, umap_dim=15):
    """UMAP + HDBSCAN 여러 mcs로 실행"""
    import umap
    from algorithms.hdbscan_clustering import cluster_with_hdbscan
    from sklearn.metrics import silhouette_score

    # UMAP 축소
    print(f"    UMAP → {umap_dim}d...", end=" ", flush=True)
    t0 = time.time()
    reducer = umap.UMAP(
        n_components=umap_dim, n_neighbors=15, min_dist=0.0,
        metric="cosine", random_state=42,
    )
    reduced = reducer.fit_transform(embeddings)
    print(f"{time.time()-t0:.1f}초")

    results = []
    for mcs in mcs_values:
        labels, clusters, info = cluster_with_hdbscan(
            reduced, min_cluster_size=mcs, metric="euclidean"
        )

        n_clusters = len(clusters)
        noise = int(np.sum(labels == -1))
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

        results.append({
            "mcs": mcs,
            "n_clusters": n_clusters,
            "noise": noise,
            "noise_ratio": noise / len(labels),
            "silhouette": sil,
            "sizes_top10": sizes[:10],
            "mean_size": float(np.mean(sizes)) if sizes else 0,
            "max_size": max(sizes) if sizes else 0,
            "singletons": sum(1 for s in sizes if s == 1),
            "labels": labels,
            "clusters": clusters,
        })

    return results, reduced


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default="2026-04-11")
    parser.add_argument("--categories", nargs="*")
    args = parser.parse_args()

    all_categories = ["politics", "economy", "society", "culture",
                      "international", "local", "sports", "tech"]

    if args.categories:
        categories = [c for c in all_categories if c in args.categories]
    else:
        categories = all_categories

    mcs_values = [3, 5, 8, 10, 15, 20, 25, 30]

    print(f"{'='*70}")
    print(f"  실제 뉴스 데이터 클러스터링 실험")
    print(f"  날짜: {args.date}")
    print(f"  카테고리: {categories}")
    print(f"  mcs 후보: {mcs_values}")
    print(f"{'='*70}\n")

    all_results = []

    for category in categories:
        articles = load_articles(args.date, category)
        if not articles:
            print(f"  [{category}] 데이터 없음, 스킵")
            continue

        print(f"\n{'='*60}")
        print(f"  [{category}] {len(articles)}건")
        print(f"{'='*60}")

        # 텍스트 준비
        texts = []
        for a in articles:
            text = a.get("title", "") + " " + a.get("content", "")
            texts.append(text[:1000])

        # 임베딩
        embeddings = embed_articles(texts, category, args.date)

        # 클러스터링
        results, reduced = run_clustering(embeddings, mcs_values)

        # 결과 테이블
        print(f"\n    {'MCS':>4} {'CLUST':>6} {'NOISE':>6} {'NOISE%':>7} {'SIL':>8} {'MEAN':>6} {'MAX':>5} {'TOP SIZES'}")
        print(f"    {'─'*75}")
        for r in results:
            sil = f"{r['silhouette']:.4f}" if r['silhouette'] else "   N/A"
            sizes_str = str(r['sizes_top10'][:7])
            print(f"    {r['mcs']:>4} {r['n_clusters']:>6} {r['noise']:>6} {r['noise_ratio']:>6.1%} "
                  f"{sil:>8} {r['mean_size']:>6.1f} {r['max_size']:>5} {sizes_str}")

        # 최적 mcs 선정 (silhouette 기준)
        valid = [r for r in results if r['silhouette'] is not None]
        if valid:
            best = max(valid, key=lambda x: x['silhouette'])
            print(f"\n    최적: mcs={best['mcs']} (sil={best['silhouette']:.4f}, "
                  f"clusters={best['n_clusters']}, noise={best['noise_ratio']:.1%})")

            # 토픽 내용 샘플 (상위 5개)
            print(f"\n    --- 토픽 내용 (상위 5개, mcs={best['mcs']}) ---")
            sorted_clusters = sorted(best['clusters'].items(),
                                    key=lambda x: len(x[1]), reverse=True)
            for rank, (cid, members) in enumerate(sorted_clusters[:5], 1):
                print(f"\n      토픽 {rank} ({len(members)}건):")
                for idx in members[:3]:
                    title = articles[idx].get("title", "")[:55]
                    press = articles[idx].get("provider", "")
                    print(f"        [{press}] {title}")
                if len(members) > 3:
                    print(f"        ... +{len(members)-3}건")

        # 저장용 (labels/clusters 제외)
        for r in results:
            r.pop("labels", None)
            r.pop("clusters", None)
            all_results.append({
                "category": category,
                "article_count": len(articles),
                **r,
            })

    # 전체 요약 테이블
    print(f"\n\n{'='*90}")
    print(f"  전체 카테고리 최적 mcs 요약")
    print(f"{'='*90}")
    print(f"  {'CATEGORY':<15} {'ARTICLES':>8} {'BEST_MCS':>8} {'CLUST':>6} {'NOISE%':>7} {'SIL':>8}")
    print(f"  {'─'*60}")

    for category in categories:
        cat_results = [r for r in all_results
                      if r['category'] == category and r['silhouette'] is not None]
        if not cat_results:
            continue
        best = max(cat_results, key=lambda x: x['silhouette'])
        print(f"  {category:<15} {best['article_count']:>8} {best['mcs']:>8} "
              f"{best['n_clusters']:>6} {best['noise_ratio']:>6.1%} {best['silhouette']:>8.4f}")

    # 결과 저장
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = RESULTS_DIR / f"realdata_clustering_{ts}.json"

    def convert(obj):
        if isinstance(obj, (np.integer,)): return int(obj)
        if isinstance(obj, (np.floating,)): return float(obj)
        if isinstance(obj, np.ndarray): return obj.tolist()
        return obj

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "date": args.date,
            "mcs_values": mcs_values,
            "results": all_results,
        }, f, ensure_ascii=False, indent=2, default=convert)

    print(f"\n결과 저장: {output_file}")


if __name__ == "__main__":
    main()
