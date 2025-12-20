"""
Union-Find 2-Pass Clustering (Backend_v2 브랜치 방식)

Backend_v2 브랜치에서 사용하는 Union-Find 기반 클러스터링입니다.

특징:
- Pass 1: Union-Find 중복 제거 (threshold=0.85)
  - 모든 쌍 비교 O(n²/2)
  - 간접 연결 발견 (A→B, B→C → A-B-C 병합)
  - 경로 압축으로 효율성 확보

- Pass 2: Hybrid 이상치 필터링
  - Centroid-based: 카테고리 중심과의 거리 (threshold < 0.30)
  - Isolation-based: 다른 기사와의 최대 유사도 (threshold < 0.25)
  - AND 조건: 둘 다 만족해야 제거

장점:
- 간접적으로 연결된 기사들도 하나의 클러스터로 통합
- 광고/스팸 기사 필터링 가능

단점:
- 체이닝 효과 (Single Linkage와 유사)
- 주제가 drift되어도 연결되면 병합됨
- 하나의 bridge article이 다른 두 토픽을 연결할 수 있음
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
import time


class UnionFind:
    """Union-Find 자료구조 (경로 압축 포함)"""

    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        """경로 압축을 적용한 find"""
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: int, y: int) -> bool:
        """랭크 기반 union, 병합 시 True 반환"""
        root_x = self.find(x)
        root_y = self.find(y)

        if root_x == root_y:
            return False

        # 랭크 기반 union
        if self.rank[root_x] < self.rank[root_y]:
            root_x, root_y = root_y, root_x

        self.parent[root_y] = root_x

        if self.rank[root_x] == self.rank[root_y]:
            self.rank[root_x] += 1

        return True


class UnionFindClustering:
    """
    Union-Find 기반 클러스터링

    사용법:
        clusterer = UnionFindClustering(similarity_threshold=0.85)
        labels, clusters = clusterer.fit(embeddings)
    """

    def __init__(
        self,
        similarity_threshold: float = 0.85,
        enable_outlier_filter: bool = True,
        centroid_threshold: float = 0.30,
        isolation_threshold: float = 0.25
    ):
        """
        Args:
            similarity_threshold: 같은 클러스터로 판단할 유사도 임계값
            enable_outlier_filter: Pass 2 이상치 필터링 활성화 여부
            centroid_threshold: Centroid 거리 임계값 (미만이면 이상치 후보)
            isolation_threshold: 고립도 임계값 (미만이면 이상치 후보)
        """
        self.similarity_threshold = similarity_threshold
        self.enable_outlier_filter = enable_outlier_filter
        self.centroid_threshold = centroid_threshold
        self.isolation_threshold = isolation_threshold

        self.n_clusters_ = 0
        self.labels_ = None
        self.clusters_ = None
        self.outliers_ = []
        self.merge_count_ = 0
        self.execution_time_ = 0.0
        self.similarity_matrix_ = None

    def fit(self, embeddings: np.ndarray) -> Tuple[np.ndarray, Dict[int, List[int]]]:
        """
        임베딩에 대해 Union-Find 클러스터링을 수행합니다.

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

        # 정규화
        normalized = self._normalize(embeddings)

        # 유사도 행렬 계산 (한 번만 계산하여 캐시)
        self.similarity_matrix_ = np.dot(normalized, normalized.T)

        # Pass 1: Union-Find 클러스터링
        uf = UnionFind(n)
        self.merge_count_ = 0

        for i in range(n):
            for j in range(i + 1, n):
                similarity = self.similarity_matrix_[i, j]
                if similarity >= self.similarity_threshold:
                    if uf.union(i, j):
                        self.merge_count_ += 1

        # 클러스터 그룹화
        clusters_dict = {}
        for i in range(n):
            root = uf.find(i)
            if root not in clusters_dict:
                clusters_dict[root] = []
            clusters_dict[root].append(i)

        # 클러스터 ID 재정렬
        clusters = {}
        labels = np.zeros(n, dtype=int)

        for new_id, (old_id, members) in enumerate(clusters_dict.items()):
            clusters[new_id] = members
            for member in members:
                labels[member] = new_id

        # Pass 2: 이상치 필터링 (옵션)
        if self.enable_outlier_filter:
            labels, clusters = self._filter_outliers(
                labels, clusters, normalized, self.similarity_matrix_
            )

        self.labels_ = labels
        self.clusters_ = clusters
        self.n_clusters_ = len(clusters)
        self.execution_time_ = time.time() - start_time

        return self.labels_, self.clusters_

    def _normalize(self, embeddings: np.ndarray) -> np.ndarray:
        """임베딩 벡터를 정규화합니다."""
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        return embeddings / norms

    def _filter_outliers(
        self,
        labels: np.ndarray,
        clusters: Dict[int, List[int]],
        normalized: np.ndarray,
        similarity_matrix: np.ndarray
    ) -> Tuple[np.ndarray, Dict[int, List[int]]]:
        """
        Hybrid 방식으로 이상치를 필터링합니다.

        조건 (AND):
        1. 카테고리 중심(centroid)에서 멀리 떨어진 것
        2. 다른 모든 기사와도 동떨어진 것
        """
        n = len(labels)
        outliers = []

        # 전체 centroid 계산
        centroid = np.mean(normalized, axis=0)
        centroid = centroid / np.linalg.norm(centroid)

        # 각 샘플 검사
        for i in range(n):
            # 조건 1: centroid와의 유사도
            centroid_sim = np.dot(normalized[i], centroid)

            # 조건 2: 다른 모든 샘플과의 최대 유사도
            similarities = similarity_matrix[i].copy()
            similarities[i] = -1  # 자기 자신 제외
            max_sim = np.max(similarities)

            # AND 조건: 둘 다 낮으면 이상치
            if centroid_sim < self.centroid_threshold and max_sim < self.isolation_threshold:
                outliers.append(i)

        self.outliers_ = outliers

        # 이상치가 없으면 원본 반환
        if not outliers:
            return labels, clusters

        # 이상치 제거 후 클러스터 재구성
        outlier_set = set(outliers)
        new_clusters = {}
        new_labels = labels.copy()

        for cluster_id, members in clusters.items():
            # 이상치가 아닌 멤버만 유지
            valid_members = [m for m in members if m not in outlier_set]

            if valid_members:
                new_clusters[cluster_id] = valid_members

        # 이상치는 레이블 -1로 표시
        for outlier_idx in outliers:
            new_labels[outlier_idx] = -1

        # 클러스터 ID 재정렬
        final_clusters = {}
        for new_id, (old_id, members) in enumerate(new_clusters.items()):
            final_clusters[new_id] = members
            for member in members:
                new_labels[member] = new_id

        return new_labels, final_clusters

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
            "merge_count": self.merge_count_,
            "outlier_count": len(self.outliers_),
            "execution_time": self.execution_time_,
            "similarity_threshold": self.similarity_threshold,
            "enable_outlier_filter": self.enable_outlier_filter,
            "algorithm": "union_find_2pass"
        }


def cluster_with_unionfind(
    embeddings: np.ndarray,
    similarity_threshold: float = 0.85,
    enable_outlier_filter: bool = True,
    centroid_threshold: float = 0.30,
    isolation_threshold: float = 0.25
) -> Tuple[np.ndarray, Dict[int, List[int]], Dict]:
    """
    편의 함수: Union-Find 클러스터링 수행

    Args:
        embeddings: 임베딩 배열
        similarity_threshold: 유사도 임계값
        enable_outlier_filter: 이상치 필터링 활성화
        centroid_threshold: Centroid 거리 임계값
        isolation_threshold: 고립도 임계값

    Returns:
        labels: 클러스터 레이블
        clusters: 클러스터 딕셔너리
        info: 클러스터링 정보
    """
    clusterer = UnionFindClustering(
        similarity_threshold=similarity_threshold,
        enable_outlier_filter=enable_outlier_filter,
        centroid_threshold=centroid_threshold,
        isolation_threshold=isolation_threshold
    )

    labels, clusters = clusterer.fit(embeddings)
    info = clusterer.get_cluster_info()

    return labels, clusters, info


# 테스트 코드
if __name__ == "__main__":
    print("Union-Find Clustering 테스트")
    print("=" * 40)

    np.random.seed(42)
    embeddings = np.random.randn(10, 3)

    # 일부 샘플을 유사하게 만들기
    embeddings[0] = embeddings[1] + np.random.randn(3) * 0.1
    embeddings[2] = embeddings[3] + np.random.randn(3) * 0.1

    # 체이닝 테스트: 0-1-2를 연결
    embeddings[1] = (embeddings[0] + embeddings[2]) / 2 + np.random.randn(3) * 0.1

    # 이상치 생성
    embeddings[9] = np.array([100, 100, 100])  # 멀리 떨어진 점

    # 이상치 필터링 없이
    print("\n[이상치 필터링 OFF]")
    labels1, clusters1, info1 = cluster_with_unionfind(
        embeddings, similarity_threshold=0.5, enable_outlier_filter=False
    )
    print(f"  클러스터 수: {info1['n_clusters']}")
    print(f"  병합 횟수: {info1['merge_count']}")
    print(f"  클러스터 크기: {info1['cluster_sizes']}")

    # 이상치 필터링 포함
    print("\n[이상치 필터링 ON]")
    labels2, clusters2, info2 = cluster_with_unionfind(
        embeddings, similarity_threshold=0.5, enable_outlier_filter=True
    )
    print(f"  클러스터 수: {info2['n_clusters']}")
    print(f"  이상치 수: {info2['outlier_count']}")
    print(f"  클러스터 크기: {info2['cluster_sizes']}")
