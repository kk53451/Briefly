"""
클러스터링 품질 메트릭

클러스터링 결과의 품질을 평가하는 다양한 메트릭을 제공합니다.
scikit-learn 없이 NumPy만으로 구현되었습니다.

메트릭:
1. Silhouette Score: 클러스터 내 응집도와 클러스터 간 분리도
2. Pairwise Metrics: 쌍별 비교 기반 Precision, Recall, F1
3. Cluster Purity: 클러스터 순도 (Ground Truth 필요)
"""

import numpy as np
from typing import Dict, List, Optional, Tuple


def silhouette_score(
    embeddings: np.ndarray,
    labels: np.ndarray
) -> float:
    """
    Silhouette Score를 계산합니다.

    각 샘플에 대해:
    - a(i): 같은 클러스터 내 다른 샘플과의 평균 거리
    - b(i): 가장 가까운 다른 클러스터 샘플과의 평균 거리
    - s(i) = (b(i) - a(i)) / max(a(i), b(i))

    Args:
        embeddings: (n_samples, n_features) 임베딩 배열
        labels: 클러스터 레이블

    Returns:
        평균 Silhouette Score (-1 ~ 1, 높을수록 좋음)
    """
    n = len(labels)

    if n <= 1:
        return 0.0

    unique_labels = np.unique(labels)
    n_clusters = len(unique_labels)

    if n_clusters <= 1:
        return 0.0

    # 정규화
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    normalized = embeddings / norms

    # 거리 행렬 계산 (코사인 거리 = 1 - 유사도)
    similarity_matrix = np.dot(normalized, normalized.T)
    distance_matrix = 1 - similarity_matrix

    silhouette_values = []

    for i in range(n):
        label_i = labels[i]

        # a(i): 같은 클러스터 내 평균 거리
        same_cluster_mask = (labels == label_i)
        same_cluster_mask[i] = False  # 자기 자신 제외

        if np.sum(same_cluster_mask) == 0:
            # 싱글톤 클러스터
            a_i = 0
        else:
            a_i = np.mean(distance_matrix[i, same_cluster_mask])

        # b(i): 가장 가까운 다른 클러스터와의 평균 거리
        b_i = float('inf')

        for other_label in unique_labels:
            if other_label == label_i:
                continue

            other_cluster_mask = (labels == other_label)
            if np.sum(other_cluster_mask) == 0:
                continue

            avg_dist = np.mean(distance_matrix[i, other_cluster_mask])
            b_i = min(b_i, avg_dist)

        if b_i == float('inf'):
            b_i = 0

        # Silhouette 계산
        if max(a_i, b_i) == 0:
            s_i = 0
        else:
            s_i = (b_i - a_i) / max(a_i, b_i)

        silhouette_values.append(s_i)

    return float(np.mean(silhouette_values))


def pairwise_metrics(
    true_labels: np.ndarray,
    predicted_labels: np.ndarray
) -> Dict[str, float]:
    """
    쌍별 비교 기반 Precision, Recall, F1을 계산합니다.

    True Positive: 같은 클러스터로 예측되어야 하는 쌍이 실제로 같은 클러스터
    False Positive: 다른 클러스터인데 같은 클러스터로 예측
    False Negative: 같은 클러스터인데 다른 클러스터로 예측

    Args:
        true_labels: Ground Truth 라벨
        predicted_labels: 예측 라벨

    Returns:
        precision, recall, f1_score, accuracy 딕셔너리
    """
    n = len(true_labels)

    if n != len(predicted_labels):
        raise ValueError("라벨 길이가 일치하지 않습니다")

    tp = fp = fn = tn = 0

    for i in range(n):
        for j in range(i + 1, n):
            true_same = true_labels[i] == true_labels[j]
            pred_same = predicted_labels[i] == predicted_labels[j]

            if true_same and pred_same:
                tp += 1
            elif not true_same and pred_same:
                fp += 1
            elif true_same and not pred_same:
                fn += 1
            else:
                tn += 1

    # 메트릭 계산
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    total_pairs = n * (n - 1) // 2
    accuracy = (tp + tn) / total_pairs if total_pairs > 0 else 0.0

    return {
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "accuracy": accuracy,
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "true_negatives": tn,
        "total_pairs": total_pairs
    }


def cluster_purity(
    true_labels: np.ndarray,
    predicted_labels: np.ndarray
) -> float:
    """
    클러스터 순도(Purity)를 계산합니다.

    각 클러스터에서 가장 많은 True 라벨의 비율을 계산합니다.

    Args:
        true_labels: Ground Truth 라벨
        predicted_labels: 예측 라벨

    Returns:
        Purity 점수 (0 ~ 1, 높을수록 좋음)
    """
    n = len(true_labels)

    if n != len(predicted_labels):
        raise ValueError("라벨 길이가 일치하지 않습니다")

    if n == 0:
        return 0.0

    unique_pred_labels = np.unique(predicted_labels)
    total_correct = 0

    for pred_label in unique_pred_labels:
        mask = (predicted_labels == pred_label)
        true_labels_in_cluster = true_labels[mask]

        # 가장 많은 True 라벨 카운트
        unique, counts = np.unique(true_labels_in_cluster, return_counts=True)
        max_count = counts.max() if len(counts) > 0 else 0
        total_correct += max_count

    return total_correct / n


def adjusted_rand_index(
    true_labels: np.ndarray,
    predicted_labels: np.ndarray
) -> float:
    """
    Adjusted Rand Index를 계산합니다.

    랜덤 라벨링에 대해 보정된 Rand Index입니다.

    Args:
        true_labels: Ground Truth 라벨
        predicted_labels: 예측 라벨

    Returns:
        ARI 점수 (-1 ~ 1, 높을수록 좋음)
    """
    n = len(true_labels)

    if n != len(predicted_labels):
        raise ValueError("라벨 길이가 일치하지 않습니다")

    if n == 0:
        return 0.0

    # Contingency table 구성
    true_unique = np.unique(true_labels)
    pred_unique = np.unique(predicted_labels)

    contingency = np.zeros((len(true_unique), len(pred_unique)), dtype=int)

    true_label_map = {label: idx for idx, label in enumerate(true_unique)}
    pred_label_map = {label: idx for idx, label in enumerate(pred_unique)}

    for t, p in zip(true_labels, predicted_labels):
        contingency[true_label_map[t], pred_label_map[p]] += 1

    # 행/열 합계
    row_sums = contingency.sum(axis=1)
    col_sums = contingency.sum(axis=0)

    # 조합 계산
    def comb2(n):
        return n * (n - 1) // 2

    # 전체 쌍 수
    total_comb = comb2(n)
    if total_comb == 0:
        return 0.0

    # Index 계산
    sum_comb_nij = sum(comb2(nij) for nij in contingency.flatten())
    sum_comb_ai = sum(comb2(ai) for ai in row_sums)
    sum_comb_bj = sum(comb2(bj) for bj in col_sums)

    # Expected Index
    expected_index = (sum_comb_ai * sum_comb_bj) / total_comb

    # Max Index
    max_index = (sum_comb_ai + sum_comb_bj) / 2

    if max_index == expected_index:
        return 1.0 if sum_comb_nij == expected_index else 0.0

    # Adjusted Rand Index
    ari = (sum_comb_nij - expected_index) / (max_index - expected_index)

    return float(ari)


def normalized_mutual_info(
    true_labels: np.ndarray,
    predicted_labels: np.ndarray
) -> float:
    """
    Normalized Mutual Information을 계산합니다.

    Args:
        true_labels: Ground Truth 라벨
        predicted_labels: 예측 라벨

    Returns:
        NMI 점수 (0 ~ 1, 높을수록 좋음)
    """
    n = len(true_labels)

    if n != len(predicted_labels):
        raise ValueError("라벨 길이가 일치하지 않습니다")

    if n == 0:
        return 0.0

    # 엔트로피 계산
    def entropy(labels):
        unique, counts = np.unique(labels, return_counts=True)
        probs = counts / n
        return -np.sum(probs * np.log(probs + 1e-10))

    h_true = entropy(true_labels)
    h_pred = entropy(predicted_labels)

    if h_true == 0 or h_pred == 0:
        return 0.0

    # Mutual Information 계산
    mi = 0.0
    true_unique = np.unique(true_labels)
    pred_unique = np.unique(predicted_labels)

    for t in true_unique:
        for p in pred_unique:
            mask = (true_labels == t) & (predicted_labels == p)
            count = np.sum(mask)
            if count == 0:
                continue

            p_tp = count / n
            p_t = np.sum(true_labels == t) / n
            p_p = np.sum(predicted_labels == p) / n

            mi += p_tp * np.log(p_tp / (p_t * p_p) + 1e-10)

    # Normalization
    nmi = 2 * mi / (h_true + h_pred)

    return float(nmi)


def calculate_all_quality_metrics(
    embeddings: np.ndarray,
    predicted_labels: np.ndarray,
    true_labels: Optional[np.ndarray] = None
) -> Dict[str, float]:
    """
    모든 품질 메트릭을 계산합니다.

    Args:
        embeddings: 임베딩 배열
        predicted_labels: 예측 라벨
        true_labels: Ground Truth 라벨 (선택)

    Returns:
        모든 품질 메트릭 딕셔너리
    """
    metrics = {}

    # Silhouette Score (Ground Truth 불필요)
    metrics["silhouette_score"] = silhouette_score(embeddings, predicted_labels)

    # 클러스터 통계
    unique_labels = np.unique(predicted_labels)
    n_clusters = len(unique_labels)
    cluster_sizes = [np.sum(predicted_labels == label) for label in unique_labels]

    metrics["n_clusters"] = n_clusters
    metrics["mean_cluster_size"] = float(np.mean(cluster_sizes)) if cluster_sizes else 0
    metrics["max_cluster_size"] = int(max(cluster_sizes)) if cluster_sizes else 0
    metrics["singleton_count"] = sum(1 for s in cluster_sizes if s == 1)

    # Ground Truth가 있으면 추가 메트릭 계산
    if true_labels is not None:
        pairwise = pairwise_metrics(true_labels, predicted_labels)
        metrics["pairwise_precision"] = pairwise["precision"]
        metrics["pairwise_recall"] = pairwise["recall"]
        metrics["pairwise_f1"] = pairwise["f1_score"]
        metrics["pairwise_accuracy"] = pairwise["accuracy"]

        metrics["cluster_purity"] = cluster_purity(true_labels, predicted_labels)
        metrics["adjusted_rand_index"] = adjusted_rand_index(true_labels, predicted_labels)
        metrics["normalized_mutual_info"] = normalized_mutual_info(true_labels, predicted_labels)

    return metrics


# 테스트 코드
if __name__ == "__main__":
    print("품질 메트릭 테스트")
    print("=" * 50)

    np.random.seed(42)

    # 테스트 데이터 생성
    # 3개의 클러스터, 각 10개 샘플
    cluster_1 = np.random.randn(10, 5) + np.array([5, 0, 0, 0, 0])
    cluster_2 = np.random.randn(10, 5) + np.array([0, 5, 0, 0, 0])
    cluster_3 = np.random.randn(10, 5) + np.array([0, 0, 5, 0, 0])

    embeddings = np.vstack([cluster_1, cluster_2, cluster_3])
    true_labels = np.array([0]*10 + [1]*10 + [2]*10)

    # 완벽한 예측
    print("\n[완벽한 예측]")
    metrics = calculate_all_quality_metrics(embeddings, true_labels, true_labels)
    print(f"  Silhouette Score: {metrics['silhouette_score']:.4f}")
    print(f"  Pairwise F1: {metrics.get('pairwise_f1', 'N/A')}")
    print(f"  Cluster Purity: {metrics.get('cluster_purity', 'N/A'):.4f}")
    print(f"  ARI: {metrics.get('adjusted_rand_index', 'N/A'):.4f}")

    # 일부 오류가 있는 예측
    print("\n[일부 오류가 있는 예측]")
    noisy_labels = true_labels.copy()
    noisy_labels[5:8] = 1  # 일부 잘못 분류
    noisy_labels[15:18] = 2

    metrics = calculate_all_quality_metrics(embeddings, noisy_labels, true_labels)
    print(f"  Silhouette Score: {metrics['silhouette_score']:.4f}")
    print(f"  Pairwise F1: {metrics.get('pairwise_f1', 'N/A'):.4f}")
    print(f"  Cluster Purity: {metrics.get('cluster_purity', 'N/A'):.4f}")
    print(f"  ARI: {metrics.get('adjusted_rand_index', 'N/A'):.4f}")
