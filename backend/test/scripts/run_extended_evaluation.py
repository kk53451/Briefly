# backend/test/scripts/run_extended_evaluation.py

"""
클러스터링 확장 평가 스크립트

목적: 기존 Silhouette Score 외에 다양한 평가 지표 추가 측정

평가 지표:
1. Internal Metrics
   - Silhouette Score (기존)
   - Calinski-Harabasz Index
   - Davies-Bouldin Index

2. Contextual/Semantic Metrics
   - Intra-cluster Similarity (클러스터 내 평균 유사도)
   - Inter-cluster Distance (클러스터 간 평균 거리)
   - Title Overlap Score (제목 bigram Jaccard 유사도)

3. Distribution Metrics
   - Cluster Size Entropy
   - Singleton Ratio
   - Giant Cluster Ratio
   - Gini Coefficient

사용법:
    cd backend
    python -m test.scripts.run_extended_evaluation
"""

import os
import sys
import json
import time
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict, field
import re

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score

# ============================================================
# 설정
# ============================================================

DATA_DIR = Path(__file__).parent.parent / "data"
RESULTS_DIR = Path(__file__).parent.parent / "results"
EMBEDDINGS_FILE = DATA_DIR / "embeddings_2025-11-30.npz"
RAW_DATA_FILE = DATA_DIR / "news_raw_2025-11-30.jsonl"
OUTPUT_FILE = RESULTS_DIR / "extended_metrics_2025-12-02.json"
REPORT_FILE = RESULTS_DIR / "EXTENDED_EVALUATION_REPORT.md"

# 알고리즘별 파라미터 (주요 설정만)
THRESHOLDS = [0.5, 0.6, 0.7, 0.8]
DBSCAN_CONFIGS = [
    {"eps": 0.3, "min_samples": 2},
    {"eps": 0.4, "min_samples": 2},
    {"eps": 0.5, "min_samples": 2},
]

# ============================================================
# 데이터 클래스
# ============================================================

@dataclass
class ExtendedMetrics:
    algorithm: str
    parameters: Dict[str, Any]
    category: str
    input_count: int
    cluster_count: int

    # Internal Metrics
    silhouette: float
    calinski_harabasz: float
    davies_bouldin: float

    # Contextual Metrics
    intra_cluster_similarity: float
    inter_cluster_distance: float
    title_overlap_score: float

    # Distribution Metrics
    cluster_size_entropy: float
    singleton_ratio: float
    giant_cluster_ratio: float
    gini_coefficient: float

    # 추가 정보
    noise_count: int = 0
    cluster_sizes: List[int] = field(default_factory=list)


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
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normalized = embeddings / np.maximum(norms, 1e-10)
    similarity_matrix = np.dot(normalized, normalized.T)
    similarity_matrix = np.clip(similarity_matrix, -1.0, 1.0)
    distance_matrix = 1 - similarity_matrix
    distance_matrix = np.maximum(distance_matrix, 0)
    np.fill_diagonal(distance_matrix, 0)
    return distance_matrix


def cosine_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    """코사인 유사도 행렬 계산"""
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normalized = embeddings / np.maximum(norms, 1e-10)
    similarity_matrix = np.dot(normalized, normalized.T)
    return np.clip(similarity_matrix, -1.0, 1.0)


def get_bigrams(text: str) -> set:
    """텍스트에서 bigram 추출"""
    # 한글, 영문, 숫자만 남기고 공백으로 분리
    tokens = re.findall(r'[\w가-힣]+', text.lower())
    if len(tokens) < 2:
        return set(tokens)
    return set(zip(tokens[:-1], tokens[1:]))


def jaccard_similarity(set1: set, set2: set) -> float:
    """Jaccard 유사도 계산"""
    if not set1 and not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0


# ============================================================
# 클러스터링 알고리즘 (기존 재사용)
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

    labels = [find(i) for i in range(n)]
    unique_labels = list(set(labels))
    label_map = {old: new for new, old in enumerate(unique_labels)}
    return [label_map[l] for l in labels]


def cluster_greedy(embeddings: np.ndarray, threshold: float) -> List[int]:
    """Greedy 클러스터링"""
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

    distance_matrix = cosine_distance_matrix(embeddings)
    condensed = squareform(distance_matrix, checks=False)
    Z = linkage(condensed, method='average')
    distance_threshold = 1 - threshold
    labels = fcluster(Z, t=distance_threshold, criterion='distance')
    return [l - 1 for l in labels]


def cluster_dbscan(embeddings: np.ndarray, eps: float, min_samples: int) -> List[int]:
    """DBSCAN 클러스터링"""
    distance_matrix = cosine_distance_matrix(embeddings)
    clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='precomputed')
    labels = clustering.fit_predict(distance_matrix)
    return labels.tolist()


# ============================================================
# 평가 지표 계산
# ============================================================

def calculate_internal_metrics(
    embeddings: np.ndarray,
    labels: List[int]
) -> Tuple[float, float, float]:
    """Internal Metrics 계산: Silhouette, Calinski-Harabasz, Davies-Bouldin"""

    # 노이즈(-1) 제외
    valid_mask = np.array(labels) != -1
    valid_embeddings = embeddings[valid_mask]
    valid_labels = [l for l in labels if l != -1]

    n_clusters = len(set(valid_labels))

    # 클러스터가 2개 미만이면 계산 불가
    if n_clusters < 2 or len(valid_labels) < 2:
        return -1.0, -1.0, -1.0

    try:
        silhouette = silhouette_score(valid_embeddings, valid_labels, metric='cosine')
    except Exception:
        silhouette = -1.0

    try:
        calinski = calinski_harabasz_score(valid_embeddings, valid_labels)
    except Exception:
        calinski = -1.0

    try:
        davies = davies_bouldin_score(valid_embeddings, valid_labels)
    except Exception:
        davies = -1.0

    return silhouette, calinski, davies


def calculate_intra_cluster_similarity(
    embeddings: np.ndarray,
    labels: List[int],
    sim_matrix: Optional[np.ndarray] = None
) -> float:
    """클러스터 내 평균 유사도 계산"""
    if sim_matrix is None:
        sim_matrix = cosine_similarity_matrix(embeddings)

    valid_labels = [l for l in labels if l != -1]
    if not valid_labels:
        return 0.0

    cluster_ids = set(valid_labels)
    total_sim = 0.0
    total_pairs = 0

    for cluster_id in cluster_ids:
        indices = [i for i, l in enumerate(labels) if l == cluster_id]
        if len(indices) < 2:
            continue

        for i in range(len(indices)):
            for j in range(i + 1, len(indices)):
                total_sim += sim_matrix[indices[i], indices[j]]
                total_pairs += 1

    return total_sim / total_pairs if total_pairs > 0 else 0.0


def calculate_inter_cluster_distance(
    embeddings: np.ndarray,
    labels: List[int]
) -> float:
    """클러스터 간 평균 거리 계산 (중심점 기반)"""
    valid_labels = [l for l in labels if l != -1]
    if not valid_labels:
        return 0.0

    cluster_ids = list(set(valid_labels))
    if len(cluster_ids) < 2:
        return 0.0

    # 각 클러스터의 중심점 계산
    centroids = {}
    for cluster_id in cluster_ids:
        indices = [i for i, l in enumerate(labels) if l == cluster_id]
        centroids[cluster_id] = np.mean(embeddings[indices], axis=0)

    # 중심점 간 거리 계산
    total_dist = 0.0
    total_pairs = 0

    for i, c1 in enumerate(cluster_ids):
        for c2 in cluster_ids[i+1:]:
            dist = 1 - cosine_similarity(centroids[c1], centroids[c2])
            total_dist += dist
            total_pairs += 1

    return total_dist / total_pairs if total_pairs > 0 else 0.0


def calculate_title_overlap(
    titles: List[str],
    labels: List[int]
) -> float:
    """클러스터 내 제목 Bigram Jaccard 유사도 평균"""
    valid_labels = [l for l in labels if l != -1]
    if not valid_labels:
        return 0.0

    cluster_ids = set(valid_labels)
    total_sim = 0.0
    total_pairs = 0

    # 제목별 bigram 캐시
    title_bigrams = [get_bigrams(t) for t in titles]

    for cluster_id in cluster_ids:
        indices = [i for i, l in enumerate(labels) if l == cluster_id]
        if len(indices) < 2:
            continue

        for i in range(len(indices)):
            for j in range(i + 1, len(indices)):
                sim = jaccard_similarity(
                    title_bigrams[indices[i]],
                    title_bigrams[indices[j]]
                )
                total_sim += sim
                total_pairs += 1

    return total_sim / total_pairs if total_pairs > 0 else 0.0


def calculate_distribution_metrics(labels: List[int]) -> Tuple[float, float, float, float]:
    """Distribution Metrics 계산: Entropy, Singleton Ratio, Giant Ratio, Gini"""
    valid_labels = [l for l in labels if l != -1]
    if not valid_labels:
        return 0.0, 0.0, 0.0, 0.0

    label_counts = Counter(valid_labels)
    sizes = list(label_counts.values())
    n_total = sum(sizes)
    n_clusters = len(sizes)

    # 1. Shannon Entropy (정규화)
    probs = np.array(sizes) / n_total
    entropy = -np.sum(probs * np.log2(probs + 1e-10))
    max_entropy = np.log2(n_clusters) if n_clusters > 1 else 1
    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0

    # 2. Singleton Ratio
    singletons = sum(1 for s in sizes if s == 1)
    singleton_ratio = singletons / n_clusters if n_clusters > 0 else 0

    # 3. Giant Cluster Ratio
    giant_ratio = max(sizes) / n_total if n_total > 0 else 0

    # 4. Gini Coefficient
    sorted_sizes = sorted(sizes)
    n = len(sorted_sizes)
    cumulative = np.cumsum(sorted_sizes)
    gini = (2 * np.sum((np.arange(1, n + 1) * sorted_sizes))) / (n * np.sum(sorted_sizes)) - (n + 1) / n
    gini = max(0, gini)  # 음수 방지

    return normalized_entropy, singleton_ratio, giant_ratio, gini


# ============================================================
# 실험 실행
# ============================================================

def run_single_evaluation(
    embeddings: np.ndarray,
    titles: List[str],
    algorithm: str,
    parameters: Dict[str, Any],
    category: str,
    sim_matrix: np.ndarray
) -> ExtendedMetrics:
    """단일 설정에 대한 모든 지표 계산"""
    n = len(embeddings)

    # 클러스터링 수행
    if algorithm == "union_find":
        labels = cluster_union_find(embeddings, parameters["threshold"])
    elif algorithm == "greedy":
        labels = cluster_greedy(embeddings, parameters["threshold"])
    elif algorithm == "hac":
        labels = cluster_hac(embeddings, parameters["threshold"])
    elif algorithm == "dbscan":
        labels = cluster_dbscan(embeddings, parameters["eps"], parameters["min_samples"])
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")

    # 기본 통계
    noise_count = labels.count(-1)
    valid_labels = [l for l in labels if l != -1]
    cluster_count = len(set(valid_labels)) if valid_labels else 0

    label_counts = Counter(l for l in labels if l != -1)
    cluster_sizes = sorted(label_counts.values(), reverse=True)[:10]

    # Internal Metrics
    silhouette, calinski, davies = calculate_internal_metrics(embeddings, labels)

    # Contextual Metrics
    intra_sim = calculate_intra_cluster_similarity(embeddings, labels, sim_matrix)
    inter_dist = calculate_inter_cluster_distance(embeddings, labels)
    title_overlap = calculate_title_overlap(titles, labels)

    # Distribution Metrics
    entropy, singleton, giant, gini = calculate_distribution_metrics(labels)

    return ExtendedMetrics(
        algorithm=algorithm,
        parameters=parameters,
        category=category,
        input_count=n,
        cluster_count=cluster_count,
        silhouette=round(silhouette, 4),
        calinski_harabasz=round(calinski, 2),
        davies_bouldin=round(davies, 4),
        intra_cluster_similarity=round(intra_sim, 4),
        inter_cluster_distance=round(inter_dist, 4),
        title_overlap_score=round(title_overlap, 4),
        cluster_size_entropy=round(entropy, 4),
        singleton_ratio=round(singleton, 4),
        giant_cluster_ratio=round(giant, 4),
        gini_coefficient=round(gini, 4),
        noise_count=noise_count,
        cluster_sizes=cluster_sizes
    )


def run_category_experiments(
    embeddings: np.ndarray,
    titles: List[str],
    category: str
) -> List[ExtendedMetrics]:
    """카테고리별 모든 실험 실행"""
    results = []

    # 유사도 행렬 미리 계산 (재사용)
    print(f"      Computing similarity matrix...", flush=True)
    sim_matrix = cosine_similarity_matrix(embeddings)

    # 1. Union-Find
    for threshold in THRESHOLDS:
        result = run_single_evaluation(
            embeddings, titles, "union_find", {"threshold": threshold},
            category, sim_matrix
        )
        results.append(result)
        print(f"      union_find(t={threshold}): clusters={result.cluster_count}, "
              f"CH={result.calinski_harabasz:.1f}, DB={result.davies_bouldin:.3f}", flush=True)

    # 2. Greedy
    for threshold in THRESHOLDS:
        result = run_single_evaluation(
            embeddings, titles, "greedy", {"threshold": threshold},
            category, sim_matrix
        )
        results.append(result)
        print(f"      greedy(t={threshold}): clusters={result.cluster_count}, "
              f"CH={result.calinski_harabasz:.1f}, DB={result.davies_bouldin:.3f}", flush=True)

    # 3. HAC
    for threshold in THRESHOLDS:
        result = run_single_evaluation(
            embeddings, titles, "hac", {"threshold": threshold},
            category, sim_matrix
        )
        results.append(result)
        print(f"      hac(t={threshold}): clusters={result.cluster_count}, "
              f"CH={result.calinski_harabasz:.1f}, DB={result.davies_bouldin:.3f}", flush=True)

    # 4. DBSCAN
    for config in DBSCAN_CONFIGS:
        result = run_single_evaluation(
            embeddings, titles, "dbscan", config,
            category, sim_matrix
        )
        results.append(result)
        print(f"      dbscan(eps={config['eps']}): clusters={result.cluster_count}, "
              f"noise={result.noise_count}, CH={result.calinski_harabasz:.1f}", flush=True)

    return results


# ============================================================
# 보고서 생성
# ============================================================

def generate_report(all_results: List[ExtendedMetrics], total_articles: int):
    """마크다운 보고서 생성"""

    report = []
    report.append("# 클러스터링 종합 평가 보고서")
    report.append("")
    report.append(f"**실험 일시**: 2025-12-02")
    report.append(f"**분석 대상**: BigKinds API 뉴스 데이터 {total_articles:,}건")
    report.append("")
    report.append("---")
    report.append("")

    # 1. 실험 개요
    report.append("## 1. 실험 개요")
    report.append("")
    report.append("### 1.1 평가 지표 설명")
    report.append("")
    report.append("#### Internal Metrics")
    report.append("| 지표 | 설명 | 해석 |")
    report.append("|------|------|------|")
    report.append("| Silhouette Score | 클러스터 응집도 vs 분리도 | -1~1, 높을수록 좋음 |")
    report.append("| Calinski-Harabasz | 클러스터 간 분산 / 클러스터 내 분산 | 높을수록 좋음 |")
    report.append("| Davies-Bouldin | 클러스터 간 유사도 평균 | 낮을수록 좋음 |")
    report.append("")
    report.append("#### Contextual Metrics")
    report.append("| 지표 | 설명 | 해석 |")
    report.append("|------|------|------|")
    report.append("| Intra-cluster Similarity | 클러스터 내 평균 코사인 유사도 | 높을수록 응집도 좋음 |")
    report.append("| Inter-cluster Distance | 클러스터 중심점 간 평균 거리 | 높을수록 분리 잘 됨 |")
    report.append("| Title Overlap Score | 제목 bigram Jaccard 유사도 | 높을수록 의미적 유사 |")
    report.append("")
    report.append("#### Distribution Metrics")
    report.append("| 지표 | 설명 | 해석 |")
    report.append("|------|------|------|")
    report.append("| Entropy | 클러스터 크기 분포 엔트로피 | 높을수록 균등 분포 |")
    report.append("| Singleton Ratio | 크기 1 클러스터 비율 | 너무 높으면 under-clustering |")
    report.append("| Giant Cluster Ratio | 최대 클러스터 비율 | 50% 이상이면 문제 |")
    report.append("| Gini Coefficient | 클러스터 크기 불균등도 | 0에 가까울수록 균등 |")
    report.append("")
    report.append("---")
    report.append("")

    # 2. Internal Metrics 결과
    report.append("## 2. Internal Metrics 결과")
    report.append("")

    # 알고리즘별 평균 계산
    algo_metrics = defaultdict(lambda: defaultdict(list))
    for r in all_results:
        key = f"{r.algorithm}"
        if r.algorithm in ['union_find', 'greedy', 'hac']:
            key = f"{r.algorithm}(t={r.parameters.get('threshold')})"
        elif r.algorithm == 'dbscan':
            key = f"dbscan(eps={r.parameters.get('eps')})"

        if r.silhouette != -1:
            algo_metrics[key]['silhouette'].append(r.silhouette)
        if r.calinski_harabasz != -1:
            algo_metrics[key]['calinski'].append(r.calinski_harabasz)
        if r.davies_bouldin != -1:
            algo_metrics[key]['davies'].append(r.davies_bouldin)

    report.append("### 2.1 알고리즘별 평균 점수")
    report.append("")
    report.append("| 알고리즘 | Silhouette ↑ | Calinski-Harabasz ↑ | Davies-Bouldin ↓ |")
    report.append("|----------|-------------|---------------------|------------------|")

    for key in sorted(algo_metrics.keys()):
        metrics = algo_metrics[key]
        sil = np.mean(metrics['silhouette']) if metrics['silhouette'] else -1
        cal = np.mean(metrics['calinski']) if metrics['calinski'] else -1
        dav = np.mean(metrics['davies']) if metrics['davies'] else -1
        report.append(f"| {key} | {sil:.4f} | {cal:.1f} | {dav:.4f} |")

    report.append("")
    report.append("---")
    report.append("")

    # 3. Contextual Metrics 결과
    report.append("## 3. Contextual/Semantic Metrics 결과")
    report.append("")

    context_metrics = defaultdict(lambda: defaultdict(list))
    for r in all_results:
        key = f"{r.algorithm}"
        if r.algorithm in ['union_find', 'greedy', 'hac']:
            key = f"{r.algorithm}(t={r.parameters.get('threshold')})"
        elif r.algorithm == 'dbscan':
            key = f"dbscan(eps={r.parameters.get('eps')})"

        context_metrics[key]['intra'].append(r.intra_cluster_similarity)
        context_metrics[key]['inter'].append(r.inter_cluster_distance)
        context_metrics[key]['title'].append(r.title_overlap_score)

    report.append("### 3.1 알고리즘별 평균 점수")
    report.append("")
    report.append("| 알고리즘 | Intra-Similarity ↑ | Inter-Distance ↑ | Title Overlap ↑ |")
    report.append("|----------|-------------------|------------------|-----------------|")

    for key in sorted(context_metrics.keys()):
        metrics = context_metrics[key]
        intra = np.mean(metrics['intra'])
        inter = np.mean(metrics['inter'])
        title = np.mean(metrics['title'])
        report.append(f"| {key} | {intra:.4f} | {inter:.4f} | {title:.4f} |")

    report.append("")
    report.append("---")
    report.append("")

    # 4. Distribution Metrics 결과
    report.append("## 4. Distribution Metrics 결과")
    report.append("")

    dist_metrics = defaultdict(lambda: defaultdict(list))
    for r in all_results:
        key = f"{r.algorithm}"
        if r.algorithm in ['union_find', 'greedy', 'hac']:
            key = f"{r.algorithm}(t={r.parameters.get('threshold')})"
        elif r.algorithm == 'dbscan':
            key = f"dbscan(eps={r.parameters.get('eps')})"

        dist_metrics[key]['entropy'].append(r.cluster_size_entropy)
        dist_metrics[key]['singleton'].append(r.singleton_ratio)
        dist_metrics[key]['giant'].append(r.giant_cluster_ratio)
        dist_metrics[key]['gini'].append(r.gini_coefficient)

    report.append("### 4.1 알고리즘별 평균 점수")
    report.append("")
    report.append("| 알고리즘 | Entropy ↑ | Singleton% | Giant% ↓ | Gini ↓ |")
    report.append("|----------|-----------|------------|----------|--------|")

    for key in sorted(dist_metrics.keys()):
        metrics = dist_metrics[key]
        entropy = np.mean(metrics['entropy'])
        singleton = np.mean(metrics['singleton']) * 100
        giant = np.mean(metrics['giant']) * 100
        gini = np.mean(metrics['gini'])
        report.append(f"| {key} | {entropy:.4f} | {singleton:.1f}% | {giant:.1f}% | {gini:.4f} |")

    report.append("")
    report.append("---")
    report.append("")

    # 5. 종합 분석
    report.append("## 5. 종합 분석")
    report.append("")

    # 각 지표별 최고 알고리즘 찾기
    report.append("### 5.1 지표별 최적 알고리즘")
    report.append("")

    best_by_metric = {}

    # Silhouette (높을수록 좋음)
    best_sil_key = max(algo_metrics.keys(),
                       key=lambda k: np.mean(algo_metrics[k]['silhouette']) if algo_metrics[k]['silhouette'] else -999)
    best_by_metric['Silhouette'] = (best_sil_key, np.mean(algo_metrics[best_sil_key]['silhouette']))

    # Calinski (높을수록 좋음)
    best_cal_key = max(algo_metrics.keys(),
                       key=lambda k: np.mean(algo_metrics[k]['calinski']) if algo_metrics[k]['calinski'] else -999)
    best_by_metric['Calinski-Harabasz'] = (best_cal_key, np.mean(algo_metrics[best_cal_key]['calinski']))

    # Davies (낮을수록 좋음)
    best_dav_key = min(algo_metrics.keys(),
                       key=lambda k: np.mean(algo_metrics[k]['davies']) if algo_metrics[k]['davies'] else 999)
    best_by_metric['Davies-Bouldin'] = (best_dav_key, np.mean(algo_metrics[best_dav_key]['davies']))

    # Intra-similarity (높을수록 좋음)
    best_intra_key = max(context_metrics.keys(),
                         key=lambda k: np.mean(context_metrics[k]['intra']))
    best_by_metric['Intra-Similarity'] = (best_intra_key, np.mean(context_metrics[best_intra_key]['intra']))

    # Inter-distance (높을수록 좋음)
    best_inter_key = max(context_metrics.keys(),
                         key=lambda k: np.mean(context_metrics[k]['inter']))
    best_by_metric['Inter-Distance'] = (best_inter_key, np.mean(context_metrics[best_inter_key]['inter']))

    # Title overlap (높을수록 좋음)
    best_title_key = max(context_metrics.keys(),
                         key=lambda k: np.mean(context_metrics[k]['title']))
    best_by_metric['Title Overlap'] = (best_title_key, np.mean(context_metrics[best_title_key]['title']))

    # Giant ratio (낮을수록 좋음, 단 0은 제외)
    valid_giant = {k: np.mean(v['giant']) for k, v in dist_metrics.items() if np.mean(v['giant']) > 0}
    if valid_giant:
        best_giant_key = min(valid_giant.keys(), key=lambda k: valid_giant[k])
        best_by_metric['Giant Ratio'] = (best_giant_key, valid_giant[best_giant_key])

    report.append("| 지표 | 최적 알고리즘 | 값 |")
    report.append("|------|-------------|-----|")
    for metric, (algo, value) in best_by_metric.items():
        if metric in ['Giant Ratio']:
            report.append(f"| {metric} ↓ | {algo} | {value*100:.1f}% |")
        elif metric == 'Davies-Bouldin':
            report.append(f"| {metric} ↓ | {algo} | {value:.4f} |")
        elif metric == 'Calinski-Harabasz':
            report.append(f"| {metric} ↑ | {algo} | {value:.1f} |")
        else:
            report.append(f"| {metric} ↑ | {algo} | {value:.4f} |")

    report.append("")

    # 알고리즘별 순위 점수 계산
    report.append("### 5.2 알고리즘별 종합 순위")
    report.append("")
    report.append("> 각 지표에서의 순위를 합산 (낮을수록 좋음)")
    report.append("")

    all_keys = set(algo_metrics.keys())
    algo_ranks = {k: 0 for k in all_keys}

    # 각 지표별로 순위 매기기
    def rank_by_metric(metric_dict, metric_name, higher_better=True):
        values = {k: np.mean(v[metric_name]) if v[metric_name] else (-999 if higher_better else 999)
                  for k, v in metric_dict.items()}
        sorted_keys = sorted(values.keys(), key=lambda k: values[k], reverse=higher_better)
        for rank, key in enumerate(sorted_keys, 1):
            algo_ranks[key] += rank

    rank_by_metric(algo_metrics, 'silhouette', higher_better=True)
    rank_by_metric(algo_metrics, 'calinski', higher_better=True)
    rank_by_metric(algo_metrics, 'davies', higher_better=False)
    rank_by_metric(context_metrics, 'intra', higher_better=True)
    rank_by_metric(context_metrics, 'inter', higher_better=True)
    rank_by_metric(context_metrics, 'title', higher_better=True)
    rank_by_metric(dist_metrics, 'giant', higher_better=False)

    sorted_algos = sorted(algo_ranks.keys(), key=lambda k: algo_ranks[k])

    report.append("| 순위 | 알고리즘 | 총점 (낮을수록 좋음) |")
    report.append("|------|----------|---------------------|")
    for i, key in enumerate(sorted_algos, 1):
        report.append(f"| {i} | {key} | {algo_ranks[key]} |")

    report.append("")
    report.append("---")
    report.append("")

    # 6. 결론
    report.append("## 6. 결론 및 권장사항")
    report.append("")

    winner = sorted_algos[0]
    report.append(f"### 종합 평가 결과: **{winner}** 권장")
    report.append("")
    report.append("다양한 평가 지표를 종합적으로 고려했을 때의 결과입니다.")
    report.append("")
    report.append("#### 주요 발견사항:")
    report.append("")
    report.append(f"1. **Internal Metrics 기준**: {best_by_metric['Silhouette'][0]}가 Silhouette에서 최고")
    report.append(f"2. **Contextual Metrics 기준**: {best_by_metric['Intra-Similarity'][0]}가 클러스터 내 응집도 최고")
    report.append(f"3. **Distribution Metrics 기준**: 거대 클러스터 문제는 {best_by_metric.get('Giant Ratio', ('N/A', 0))[0]}가 가장 적음")
    report.append("")

    return "\n".join(report)


# ============================================================
# 메인 실행
# ============================================================

def main():
    total_start = time.time()

    print("=" * 60, flush=True)
    print("Extended Clustering Evaluation", flush=True)
    print("=" * 60, flush=True)

    # 결과 디렉토리 생성
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. 임베딩 로드
    print("\n[1/4] Loading embeddings...", flush=True)

    if not EMBEDDINGS_FILE.exists():
        print(f"Error: Embeddings file not found: {EMBEDDINGS_FILE}", flush=True)
        return

    data = np.load(EMBEDDINGS_FILE, allow_pickle=True)
    embeddings = data["embeddings"]
    article_ids = data["article_ids"]
    categories = data["categories"]

    print(f"   Loaded: {len(embeddings)} embeddings", flush=True)

    # 2. 제목 로드
    print("\n[2/4] Loading titles...", flush=True)

    id_to_title = {}
    with open(RAW_DATA_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            article = json.loads(line)
            # 'id' 또는 'news_id' 키 모두 지원
            article_id = article.get('id') or article.get('news_id')
            if article_id:
                id_to_title[article_id] = article.get('title', '')

    print(f"   Loaded: {len(id_to_title)} titles", flush=True)

    # 3. 카테고리별 분리
    print("\n[3/4] Organizing by category...", flush=True)

    category_data = defaultdict(lambda: {"embeddings": [], "ids": [], "titles": []})
    for i, cat in enumerate(categories):
        category_data[cat]["embeddings"].append(embeddings[i])
        category_data[cat]["ids"].append(article_ids[i])
        category_data[cat]["titles"].append(id_to_title.get(article_ids[i], ''))

    for cat in category_data:
        category_data[cat]["embeddings"] = np.array(category_data[cat]["embeddings"])
        print(f"   {cat}: {len(category_data[cat]['embeddings'])} articles", flush=True)

    # 4. 실험 실행
    print("\n[4/4] Running extended evaluation...", flush=True)

    all_results = []

    for cat in sorted(category_data.keys()):
        print(f"\n   [{cat}] ({len(category_data[cat]['embeddings'])} articles)", flush=True)

        cat_embeddings = category_data[cat]["embeddings"]
        cat_titles = category_data[cat]["titles"]

        results = run_category_experiments(cat_embeddings, cat_titles, cat)
        all_results.extend(results)

    # 5. 결과 저장
    print("\n" + "=" * 60, flush=True)
    print("Saving results...", flush=True)

    results_dict = {
        "experiment_date": "2025-12-02",
        "total_articles": len(embeddings),
        "categories": list(category_data.keys()),
        "algorithms": ["union_find", "greedy", "hac", "dbscan"],
        "metrics": [
            "silhouette", "calinski_harabasz", "davies_bouldin",
            "intra_cluster_similarity", "inter_cluster_distance", "title_overlap_score",
            "cluster_size_entropy", "singleton_ratio", "giant_cluster_ratio", "gini_coefficient"
        ],
        "results": [asdict(r) for r in all_results]
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results_dict, f, ensure_ascii=False, indent=2)

    print(f"   Saved: {OUTPUT_FILE}", flush=True)

    # 6. 보고서 생성
    print("Generating report...", flush=True)

    report = generate_report(all_results, len(embeddings))

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"   Saved: {REPORT_FILE}", flush=True)

    total_time = time.time() - total_start

    print("=" * 60, flush=True)
    print("Evaluation Complete!", flush=True)
    print("=" * 60, flush=True)
    print(f"Total experiments: {len(all_results)}", flush=True)
    print(f"Total time: {total_time:.1f}s ({total_time/60:.1f} min)", flush=True)
    print("=" * 60, flush=True)


if __name__ == "__main__":
    main()
