# backend/test/scripts/run_clustering_experiment.py

"""
클러스터링 실험 스크립트

목적: 다양한 클러스터링 알고리즘과 파라미터 조합을 실험하고 결과 비교

알고리즘:
- No Clustering (Baseline)
- Union-Find (threshold: 0.5, 0.6, 0.7, 0.8)
- Greedy (threshold: 0.5, 0.6, 0.7, 0.8)
- HAC Average Linkage (threshold: 0.5, 0.6, 0.7, 0.8)
- DBSCAN (eps: 0.3, 0.4, 0.5 / min_samples: 2, 3)

사용법:
    cd backend
    python -m test.scripts.run_clustering_experiment
"""

import os
import sys
import json
import time
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Any
from collections import defaultdict
from dataclasses import dataclass, asdict

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import pdist, squareform
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score

# ============================================================
# 설정
# ============================================================

DATA_DIR = Path(__file__).parent.parent / "data"
RESULTS_DIR = Path(__file__).parent.parent / "results"
EMBEDDINGS_FILE = DATA_DIR / "embeddings_2025-11-30.npz"
RAW_DATA_FILE = DATA_DIR / "news_raw_2025-11-30.jsonl"
OUTPUT_FILE = RESULTS_DIR / "clustering_experiment_2025-11-30.json"

# 알고리즘별 파라미터
THRESHOLDS = [0.5, 0.6, 0.7, 0.8]
DBSCAN_EPS = [0.3, 0.4, 0.5]
DBSCAN_MIN_SAMPLES = [2, 3]

# ============================================================
# 데이터 클래스
# ============================================================

@dataclass
class ClusteringResult:
    algorithm: str
    parameters: Dict[str, Any]
    category: str
    input_count: int
    cluster_count: int
    compression_rate: float
    noise_count: int  # DBSCAN용
    silhouette: float
    execution_time: float
    cluster_sizes: List[int]


# ============================================================
# 유틸리티 함수
# ============================================================

def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """코사인 유사도 계산"""
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(vec1, vec2) / (norm1 * norm2))


def cosine_distance_matrix(embeddings: np.ndarray) -> np.ndarray:
    """코사인 거리 행렬 계산 (1 - similarity)"""
    # 정규화
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normalized = embeddings / np.maximum(norms, 1e-10)

    # 코사인 유사도 행렬
    similarity_matrix = np.dot(normalized, normalized.T)

    # 부동소수점 오차로 인해 1을 초과할 수 있으므로 클리핑
    similarity_matrix = np.clip(similarity_matrix, -1.0, 1.0)

    # 거리 = 1 - 유사도
    distance_matrix = 1 - similarity_matrix

    # 부동소수점 오차로 인한 음수 방지
    distance_matrix = np.maximum(distance_matrix, 0)

    # 대각선은 0으로
    np.fill_diagonal(distance_matrix, 0)

    return distance_matrix


# ============================================================
# 클러스터링 알고리즘
# ============================================================

def cluster_union_find(embeddings: np.ndarray, threshold: float) -> List[int]:
    """Union-Find 클러스터링"""
    n = len(embeddings)
    parent = list(range(n))

    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(x, y):
        root_x = find(x)
        root_y = find(y)
        if root_x != root_y:
            parent[root_y] = root_x
            return True
        return False

    # 모든 쌍 비교
    for i in range(n):
        for j in range(i + 1, n):
            sim = cosine_similarity(embeddings[i], embeddings[j])
            if sim > threshold:
                union(i, j)

    # 클러스터 라벨 생성
    labels = [find(i) for i in range(n)]

    # 라벨 정규화 (0부터 시작)
    unique_labels = list(set(labels))
    label_map = {old: new for new, old in enumerate(unique_labels)}
    return [label_map[l] for l in labels]


def cluster_greedy(embeddings: np.ndarray, threshold: float) -> List[int]:
    """Greedy 클러스터링 (순차 병합)"""
    n = len(embeddings)
    labels = [-1] * n
    current_cluster = 0

    for i in range(n):
        if labels[i] != -1:
            continue

        labels[i] = current_cluster

        for j in range(i + 1, n):
            if labels[j] != -1:
                continue

            sim = cosine_similarity(embeddings[i], embeddings[j])
            if sim > threshold:
                labels[j] = current_cluster

        current_cluster += 1

    return labels


def cluster_hac(embeddings: np.ndarray, threshold: float) -> List[int]:
    """HAC (Average Linkage) 클러스터링"""
    if len(embeddings) < 2:
        return [0] * len(embeddings)

    # 코사인 거리로 변환
    distance_matrix = cosine_distance_matrix(embeddings)

    # condensed distance matrix
    condensed = squareform(distance_matrix, checks=False)

    # HAC 수행
    Z = linkage(condensed, method='average')

    # threshold를 거리로 변환 (1 - similarity)
    distance_threshold = 1 - threshold

    # 클러스터 할당
    labels = fcluster(Z, t=distance_threshold, criterion='distance')

    # 0부터 시작하도록 변환
    return [l - 1 for l in labels]


def cluster_dbscan(embeddings: np.ndarray, eps: float, min_samples: int) -> List[int]:
    """DBSCAN 클러스터링"""
    # 코사인 거리 행렬
    distance_matrix = cosine_distance_matrix(embeddings)

    # DBSCAN (precomputed)
    clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='precomputed')
    labels = clustering.fit_predict(distance_matrix)

    return labels.tolist()


# ============================================================
# 실험 실행
# ============================================================

def run_single_experiment(
    embeddings: np.ndarray,
    algorithm: str,
    parameters: Dict[str, Any],
    category: str
) -> ClusteringResult:
    """단일 실험 실행"""
    start_time = time.time()
    n = len(embeddings)

    # 클러스터링 수행
    if algorithm == "no_clustering":
        labels = list(range(n))  # 각 기사가 독립 클러스터

    elif algorithm == "union_find":
        labels = cluster_union_find(embeddings, parameters["threshold"])

    elif algorithm == "greedy":
        labels = cluster_greedy(embeddings, parameters["threshold"])

    elif algorithm == "hac":
        labels = cluster_hac(embeddings, parameters["threshold"])

    elif algorithm == "dbscan":
        labels = cluster_dbscan(embeddings, parameters["eps"], parameters["min_samples"])

    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")

    execution_time = time.time() - start_time

    # 통계 계산
    labels_array = np.array(labels)
    unique_labels = set(labels)

    # DBSCAN 노이즈 (-1) 처리
    noise_count = list(labels).count(-1) if -1 in labels else 0
    valid_labels = [l for l in labels if l != -1]
    cluster_count = len(set(valid_labels)) if valid_labels else 0

    # 클러스터 크기 분포
    from collections import Counter
    label_counts = Counter(l for l in labels if l != -1)
    cluster_sizes = sorted(label_counts.values(), reverse=True)

    # 압축률
    compression_rate = 1 - (cluster_count / n) if n > 0 else 0

    # Silhouette Score (클러스터가 2개 이상이고 노이즈가 전체가 아닌 경우)
    silhouette = -1.0
    if cluster_count >= 2 and len(valid_labels) >= 2:
        # 노이즈 제외하고 계산
        valid_indices = [i for i, l in enumerate(labels) if l != -1]
        if len(set([labels[i] for i in valid_indices])) >= 2:
            try:
                valid_embeddings = embeddings[valid_indices]
                valid_label_list = [labels[i] for i in valid_indices]
                silhouette = silhouette_score(valid_embeddings, valid_label_list, metric='cosine')
            except Exception:
                silhouette = -1.0

    return ClusteringResult(
        algorithm=algorithm,
        parameters=parameters,
        category=category,
        input_count=n,
        cluster_count=cluster_count,
        compression_rate=round(compression_rate, 4),
        noise_count=noise_count,
        silhouette=round(silhouette, 4),
        execution_time=round(execution_time, 4),
        cluster_sizes=cluster_sizes[:10]  # 상위 10개만
    )


def run_category_experiments(
    embeddings: np.ndarray,
    category: str
) -> List[ClusteringResult]:
    """카테고리별 모든 실험 실행"""
    results = []

    # 1. No Clustering (Baseline)
    result = run_single_experiment(
        embeddings, "no_clustering", {}, category
    )
    results.append(result)
    print(f"      no_clustering: clusters={result.cluster_count}", flush=True)

    # 2. Union-Find
    for threshold in THRESHOLDS:
        result = run_single_experiment(
            embeddings, "union_find", {"threshold": threshold}, category
        )
        results.append(result)
        print(f"      union_find(t={threshold}): clusters={result.cluster_count}, "
              f"silhouette={result.silhouette:.3f}", flush=True)

    # 3. Greedy
    for threshold in THRESHOLDS:
        result = run_single_experiment(
            embeddings, "greedy", {"threshold": threshold}, category
        )
        results.append(result)
        print(f"      greedy(t={threshold}): clusters={result.cluster_count}, "
              f"silhouette={result.silhouette:.3f}", flush=True)

    # 4. HAC
    for threshold in THRESHOLDS:
        result = run_single_experiment(
            embeddings, "hac", {"threshold": threshold}, category
        )
        results.append(result)
        print(f"      hac(t={threshold}): clusters={result.cluster_count}, "
              f"silhouette={result.silhouette:.3f}", flush=True)

    # 5. DBSCAN
    for eps in DBSCAN_EPS:
        for min_samples in DBSCAN_MIN_SAMPLES:
            result = run_single_experiment(
                embeddings, "dbscan",
                {"eps": eps, "min_samples": min_samples}, category
            )
            results.append(result)
            print(f"      dbscan(eps={eps}, min={min_samples}): clusters={result.cluster_count}, "
                  f"noise={result.noise_count}, silhouette={result.silhouette:.3f}", flush=True)

    return results


# ============================================================
# 메인 실행
# ============================================================

def main():
    total_start = time.time()

    print("=" * 60, flush=True)
    print("Clustering Experiment", flush=True)
    print("=" * 60, flush=True)

    # 결과 디렉토리 생성
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. 임베딩 로드
    print("\n[1/3] Loading embeddings...", flush=True)

    if not EMBEDDINGS_FILE.exists():
        print(f"Error: Embeddings file not found: {EMBEDDINGS_FILE}", flush=True)
        print("Please run generate_embeddings.py first.", flush=True)
        return

    data = np.load(EMBEDDINGS_FILE, allow_pickle=True)
    embeddings = data["embeddings"]
    article_ids = data["article_ids"]
    categories = data["categories"]

    print(f"   Loaded: {len(embeddings)} embeddings", flush=True)
    print(f"   Dimension: {embeddings.shape[1]}", flush=True)

    # 2. 카테고리별 분리
    print("\n[2/3] Organizing by category...", flush=True)

    category_data = defaultdict(lambda: {"embeddings": [], "ids": []})
    for i, cat in enumerate(categories):
        category_data[cat]["embeddings"].append(embeddings[i])
        category_data[cat]["ids"].append(article_ids[i])

    for cat in category_data:
        category_data[cat]["embeddings"] = np.array(category_data[cat]["embeddings"])
        print(f"   {cat}: {len(category_data[cat]['embeddings'])} articles", flush=True)

    # 3. 실험 실행
    print("\n[3/3] Running experiments...", flush=True)

    all_results = []

    for cat in sorted(category_data.keys()):
        print(f"\n   [{cat}] ({len(category_data[cat]['embeddings'])} articles)", flush=True)

        cat_embeddings = category_data[cat]["embeddings"]
        results = run_category_experiments(cat_embeddings, cat)
        all_results.extend(results)

    # 4. 결과 저장
    print("\n" + "=" * 60, flush=True)
    print("Saving results...", flush=True)

    results_dict = {
        "experiment_date": "2025-11-30",
        "total_articles": len(embeddings),
        "categories": list(category_data.keys()),
        "algorithms": ["no_clustering", "union_find", "greedy", "hac", "dbscan"],
        "thresholds": THRESHOLDS,
        "dbscan_eps": DBSCAN_EPS,
        "dbscan_min_samples": DBSCAN_MIN_SAMPLES,
        "results": [asdict(r) for r in all_results]
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results_dict, f, ensure_ascii=False, indent=2)

    total_time = time.time() - total_start

    print("=" * 60, flush=True)
    print("Experiment Complete!", flush=True)
    print("=" * 60, flush=True)
    print(f"Total experiments: {len(all_results)}", flush=True)
    print(f"Total time: {total_time:.1f}s ({total_time/60:.1f} min)", flush=True)
    print(f"Output: {OUTPUT_FILE}", flush=True)
    print("=" * 60, flush=True)

    # 요약 통계
    print("\nBest Silhouette Score by Algorithm:", flush=True)
    print("-" * 50, flush=True)

    algo_best = defaultdict(lambda: {"score": -2, "params": None, "category": None})
    for r in all_results:
        if r.silhouette > algo_best[r.algorithm]["score"]:
            algo_best[r.algorithm] = {
                "score": r.silhouette,
                "params": r.parameters,
                "category": r.category
            }

    for algo in ["union_find", "greedy", "hac", "dbscan"]:
        info = algo_best[algo]
        print(f"  {algo:15s}: {info['score']:.4f} ({info['params']}, {info['category']})", flush=True)


if __name__ == "__main__":
    main()
