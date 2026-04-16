"""
HDBSCAN Clustering

밀도 기반 계층적 클러스터링으로, eps 파라미터 없이 자동으로
최적 클러스터를 찾습니다.

특징:
- min_cluster_size 하나만 지정하면 됨
- 밀도가 다른 클러스터도 동시에 발견
- 노이즈 포인트를 자동으로 label=-1 로 분리
- 카테고리/도메인 무관하게 안정적으로 동작

장점:
- 파라미터 튜닝이 거의 불필요
- 체이닝 문제 없음 (Union-Find 대비)
- 클러스터 수를 사전에 지정할 필요 없음 (KMeans 대비)

단점:
- 계산 비용이 Union-Find 보다 높음 (O(n²) ~ O(n² log n))
- min_cluster_size 가 너무 크면 소규모 토픽을 놓칠 수 있음
"""

import numpy as np
from typing import Dict, List, Tuple
import time


class HDBSCANClustering:
    """
    HDBSCAN 기반 클러스터링

    사용법:
        clusterer = HDBSCANClustering(min_cluster_size=3)
        labels, clusters = clusterer.fit(embeddings)
    """

    def __init__(
        self,
        min_cluster_size: int = 3,
        min_samples: int = None,
        metric: str = "cosine",
    ):
        """
        Args:
            min_cluster_size: 클러스터로 인정할 최소 포인트 수 (기본 3)
            min_samples: 코어 포인트 판정 기준 (None이면 min_cluster_size와 동일)
            metric: 거리 메트릭 ("cosine", "euclidean" 등)
        """
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples
        self.metric = metric

        self.n_clusters_ = 0
        self.labels_ = None
        self.clusters_ = None
        self.noise_count_ = 0
        self.execution_time_ = 0.0

    def fit(self, embeddings: np.ndarray) -> Tuple[np.ndarray, Dict[int, List[int]]]:
        """
        임베딩에 대해 HDBSCAN 클러스터링을 수행합니다.

        Args:
            embeddings: (n_samples, n_features) 형태의 임베딩 배열

        Returns:
            labels: 각 샘플의 클러스터 레이블 (노이즈 = -1)
            clusters: 클러스터 ID -> 멤버 인덱스 리스트 (노이즈 제외)
        """
        import hdbscan

        start_time = time.time()

        n = len(embeddings)
        if n == 0:
            self.labels_ = np.array([])
            self.clusters_ = {}
            return self.labels_, self.clusters_

        # 정규화 (cosine metric 사용 시 권장)
        normalized = self._normalize(embeddings)

        # 코사인 거리 행렬 사전 계산 (cosine distance = 1 - cosine similarity)
        normalized = normalized.astype(np.float64)  # hdbscan C 확장은 float64 필요
        similarity_matrix = np.dot(normalized, normalized.T)
        np.clip(similarity_matrix, -1, 1, out=similarity_matrix)
        distance_matrix = 1.0 - similarity_matrix

        # HDBSCAN 실행 (사전 계산된 거리 행렬 사용)
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=self.min_cluster_size,
            min_samples=self.min_samples,
            metric="precomputed",
            cluster_selection_method="eom",
        )
        labels = clusterer.fit_predict(distance_matrix)

        # 클러스터 딕셔너리 구성 (노이즈=-1 제외)
        clusters = {}
        for idx, label in enumerate(labels):
            if label == -1:
                continue
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(idx)

        # 클러스터 ID 재정렬 (크기 내림차순)
        sorted_clusters = sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True)
        final_clusters = {}
        label_map = {}
        for new_id, (old_id, members) in enumerate(sorted_clusters):
            final_clusters[new_id] = members
            label_map[old_id] = new_id

        # 레이블 재매핑
        final_labels = np.full(n, -1, dtype=int)
        for idx, label in enumerate(labels):
            if label != -1:
                final_labels[idx] = label_map[label]

        self.labels_ = final_labels
        self.clusters_ = final_clusters
        self.n_clusters_ = len(final_clusters)
        self.noise_count_ = int(np.sum(labels == -1))
        self.execution_time_ = time.time() - start_time

        return self.labels_, self.clusters_

    def _normalize(self, embeddings: np.ndarray) -> np.ndarray:
        """임베딩 벡터를 정규화합니다."""
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        return embeddings / norms

    def get_cluster_info(self) -> Dict:
        """클러스터링 결과 정보를 반환합니다."""
        if self.clusters_ is None:
            return {}

        cluster_sizes = [len(members) for members in self.clusters_.values()]

        return {
            "n_clusters": self.n_clusters_,
            "cluster_sizes": cluster_sizes,
            "mean_cluster_size": float(np.mean(cluster_sizes)) if cluster_sizes else 0,
            "max_cluster_size": max(cluster_sizes) if cluster_sizes else 0,
            "singleton_count": sum(1 for s in cluster_sizes if s == 1),
            "noise_count": self.noise_count_,
            "noise_ratio": self.noise_count_ / len(self.labels_) if len(self.labels_) > 0 else 0,
            "execution_time": self.execution_time_,
            "min_cluster_size": self.min_cluster_size,
            "metric": self.metric,
            "algorithm": "hdbscan"
        }


def cluster_with_hdbscan(
    embeddings: np.ndarray,
    min_cluster_size: int = 3,
    min_samples: int = None,
    metric: str = "cosine",
) -> Tuple[np.ndarray, Dict[int, List[int]], Dict]:
    """
    편의 함수: HDBSCAN 클러스터링 수행

    Returns:
        labels, clusters, info
    """
    clusterer = HDBSCANClustering(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric=metric,
    )
    labels, clusters = clusterer.fit(embeddings)
    info = clusterer.get_cluster_info()
    return labels, clusters, info


if __name__ == "__main__":
    print("HDBSCAN Clustering 테스트")
    print("=" * 40)

    np.random.seed(42)

    # 3개 클러스터 + 노이즈 생성
    cluster1 = np.random.randn(10, 3) * 0.3 + np.array([2, 0, 0])
    cluster2 = np.random.randn(8, 3) * 0.3 + np.array([0, 2, 0])
    cluster3 = np.random.randn(5, 3) * 0.3 + np.array([0, 0, 2])
    noise = np.random.randn(3, 3) * 3  # 노이즈

    embeddings = np.vstack([cluster1, cluster2, cluster3, noise])

    labels, clusters, info = cluster_with_hdbscan(embeddings, min_cluster_size=3)

    print(f"  클러스터 수: {info['n_clusters']}")
    print(f"  노이즈 수: {info['noise_count']}")
    print(f"  클러스터 크기: {info['cluster_sizes']}")
    print(f"  실행 시간: {info['execution_time']:.4f}초")
