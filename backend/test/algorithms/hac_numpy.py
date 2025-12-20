"""
HAC (Hierarchical Agglomerative Clustering) NumPy 구현

Lambda 크기 제약(250MB)을 고려하여 scikit-learn 없이
NumPy만으로 구현한 Average Linkage 클러스터링입니다.

기술 감사 보고서 권장:
- Average Linkage: 두 클러스터 내 모든 기사 간의 평균 거리를 기준
- 노이즈(스팸/이상치)에 강함
- 주제가 조금씩 변하더라도 전체적인 맥락이 유지될 때만 병합

장점:
- Union-Find의 체이닝 효과 방지
- 클러스터 품질이 더 높음
- O(n²) 복잡도지만 800건 수준에서는 문제없음 (수 초 내 처리)
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
import time


class HACClustering:
    """
    NumPy 기반 HAC Average Linkage 클러스터링

    사용법:
        clusterer = HACClustering(distance_threshold=0.5)
        labels, clusters = clusterer.fit(embeddings)
    """

    def __init__(self, distance_threshold: float = 0.5, linkage: str = "average"):
        """
        Args:
            distance_threshold: 병합 중단 거리 임계값 (1 - similarity)
                               0.5 = 유사도 50% 이상만 병합
            linkage: 연결 기준 ("average" 또는 "ward")
        """
        self.distance_threshold = distance_threshold
        self.linkage = linkage
        self.n_clusters_ = 0
        self.labels_ = None
        self.clusters_ = None
        self.execution_time_ = 0.0

    def fit(self, embeddings: np.ndarray) -> Tuple[np.ndarray, Dict[int, List[int]]]:
        """
        임베딩에 대해 HAC 클러스터링을 수행합니다.

        Args:
            embeddings: (n_samples, n_features) 형태의 임베딩 배열

        Returns:
            labels: 각 샘플의 클러스터 레이블 (n_samples,)
            clusters: 클러스터 ID → 멤버 인덱스 리스트 딕셔너리
        """
        start_time = time.time()

        n = len(embeddings)
        if n == 0:
            self.labels_ = np.array([])
            self.clusters_ = {}
            return self.labels_, self.clusters_

        if n == 1:
            self.labels_ = np.array([0])
            self.clusters_ = {0: [0]}
            self.n_clusters_ = 1
            return self.labels_, self.clusters_

        # 1. 정규화 및 거리 행렬 계산
        normalized = self._normalize(embeddings)
        similarity_matrix = np.dot(normalized, normalized.T)
        distance_matrix = 1 - similarity_matrix  # 코사인 거리

        # 2. 클러스터 초기화 (각 샘플이 하나의 클러스터)
        clusters = {i: [i] for i in range(n)}
        active_clusters = set(range(n))

        # 3. 클러스터 간 거리 행렬 초기화
        cluster_distances = distance_matrix.copy()

        # 4. 계층적 병합 수행
        while len(active_clusters) > 1:
            # 가장 가까운 두 클러스터 찾기
            min_dist, merge_i, merge_j = self._find_closest_clusters(
                cluster_distances, active_clusters
            )

            # 임계값을 넘으면 병합 중단
            if min_dist > self.distance_threshold:
                break

            # 클러스터 병합
            clusters[merge_i].extend(clusters[merge_j])
            del clusters[merge_j]
            active_clusters.remove(merge_j)

            # 병합된 클러스터와 다른 클러스터 간의 거리 업데이트
            self._update_distances(
                cluster_distances, clusters, distance_matrix,
                merge_i, merge_j, active_clusters
            )

        # 5. 결과 정리
        self.labels_ = np.zeros(n, dtype=int)
        self.clusters_ = {}

        for new_id, (old_id, members) in enumerate(clusters.items()):
            self.clusters_[new_id] = members
            for member in members:
                self.labels_[member] = new_id

        self.n_clusters_ = len(self.clusters_)
        self.execution_time_ = time.time() - start_time

        return self.labels_, self.clusters_

    def _normalize(self, embeddings: np.ndarray) -> np.ndarray:
        """임베딩 벡터를 정규화합니다."""
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)  # 0으로 나누기 방지
        return embeddings / norms

    def _find_closest_clusters(
        self,
        cluster_distances: np.ndarray,
        active_clusters: set
    ) -> Tuple[float, int, int]:
        """가장 가까운 두 클러스터를 찾습니다."""
        min_dist = float('inf')
        merge_i, merge_j = -1, -1

        active_list = list(active_clusters)
        for idx_i, ci in enumerate(active_list):
            for cj in active_list[idx_i + 1:]:
                dist = cluster_distances[ci, cj]
                if dist < min_dist:
                    min_dist = dist
                    merge_i, merge_j = ci, cj

        return min_dist, merge_i, merge_j

    def _update_distances(
        self,
        cluster_distances: np.ndarray,
        clusters: Dict[int, List[int]],
        distance_matrix: np.ndarray,
        merged_id: int,
        removed_id: int,
        active_clusters: set
    ):
        """병합된 클러스터의 거리를 업데이트합니다."""
        merged_members = clusters[merged_id]

        for other_id in active_clusters:
            if other_id == merged_id:
                continue

            other_members = clusters[other_id]

            if self.linkage == "average":
                # Average Linkage: 모든 쌍의 평균 거리
                total_dist = 0.0
                count = 0
                for a in merged_members:
                    for b in other_members:
                        total_dist += distance_matrix[a, b]
                        count += 1
                avg_dist = total_dist / count if count > 0 else float('inf')
                cluster_distances[merged_id, other_id] = avg_dist
                cluster_distances[other_id, merged_id] = avg_dist

            elif self.linkage == "ward":
                # Ward's Method: 분산 증가 최소화 (간소화 버전)
                # 실제 Ward는 더 복잡하지만, 여기서는 Average와 유사하게 처리
                total_dist = 0.0
                count = 0
                for a in merged_members:
                    for b in other_members:
                        total_dist += distance_matrix[a, b] ** 2
                        count += 1
                ward_dist = np.sqrt(total_dist / count) if count > 0 else float('inf')
                cluster_distances[merged_id, other_id] = ward_dist
                cluster_distances[other_id, merged_id] = ward_dist

    def get_cluster_info(self) -> Dict:
        """클러스터링 결과 정보를 반환합니다."""
        if self.clusters_ is None:
            return {}

        cluster_sizes = [len(members) for members in self.clusters_.values()]

        return {
            "n_clusters": self.n_clusters_,
            "cluster_sizes": cluster_sizes,
            "mean_cluster_size": np.mean(cluster_sizes) if cluster_sizes else 0,
            "max_cluster_size": max(cluster_sizes) if cluster_sizes else 0,
            "singleton_count": sum(1 for s in cluster_sizes if s == 1),
            "execution_time": self.execution_time_,
            "distance_threshold": self.distance_threshold,
            "linkage": self.linkage
        }


def cluster_with_hac(
    embeddings: np.ndarray,
    similarity_threshold: float = 0.5,
    linkage: str = "average"
) -> Tuple[np.ndarray, Dict[int, List[int]], Dict]:
    """
    편의 함수: HAC 클러스터링 수행

    Args:
        embeddings: 임베딩 배열
        similarity_threshold: 유사도 임계값 (0.5 = 50% 유사도)
        linkage: 연결 기준 ("average" 또는 "ward")

    Returns:
        labels: 클러스터 레이블
        clusters: 클러스터 딕셔너리
        info: 클러스터링 정보
    """
    # 유사도 임계값을 거리 임계값으로 변환
    distance_threshold = 1 - similarity_threshold

    clusterer = HACClustering(
        distance_threshold=distance_threshold,
        linkage=linkage
    )

    labels, clusters = clusterer.fit(embeddings)
    info = clusterer.get_cluster_info()

    return labels, clusters, info


# 테스트 코드
if __name__ == "__main__":
    # 간단한 테스트
    print("HAC NumPy 구현 테스트")
    print("=" * 40)

    # 랜덤 임베딩 생성 (10개 샘플, 3차원)
    np.random.seed(42)
    embeddings = np.random.randn(10, 3)

    # 일부 샘플을 유사하게 만들기
    embeddings[0] = embeddings[1] + np.random.randn(3) * 0.1
    embeddings[2] = embeddings[3] + np.random.randn(3) * 0.1

    # 클러스터링 수행
    labels, clusters, info = cluster_with_hac(
        embeddings,
        similarity_threshold=0.5,
        linkage="average"
    )

    print(f"\n결과:")
    print(f"  클러스터 수: {info['n_clusters']}")
    print(f"  클러스터 크기: {info['cluster_sizes']}")
    print(f"  레이블: {labels}")
    print(f"  실행 시간: {info['execution_time']:.4f}초")
