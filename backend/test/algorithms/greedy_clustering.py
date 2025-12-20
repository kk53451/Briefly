"""
Greedy Clustering (Master 브랜치 방식)

Master 브랜치에서 사용하던 단순 그리디 클러스터링입니다.

특징:
- 첫 번째 매칭 방식 (First-match)
- 순차적으로 기사를 순회하며 기존 클러스터와 비교
- threshold 이상이면 해당 클러스터에 추가
- threshold 미만이면 새 클러스터 생성
- 전이적 폐쇄(Transitive Closure) 없음

장점:
- O(n * k) 복잡도로 빠름 (k = 클러스터 수)
- 구현이 단순함

단점:
- 처리 순서에 따라 결과가 달라짐
- 간접적으로 유사한 기사들을 연결하지 못함
- 초기 기사가 클러스터의 특성을 결정함
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
import time


class GreedyClustering:
    """
    Greedy First-Match 클러스터링

    사용법:
        clusterer = GreedyClustering(similarity_threshold=0.75)
        labels, clusters = clusterer.fit(embeddings)
    """

    def __init__(self, similarity_threshold: float = 0.75):
        """
        Args:
            similarity_threshold: 같은 클러스터로 판단할 유사도 임계값
                                 (기본값 0.75 = Master 브랜치 설정)
        """
        self.similarity_threshold = similarity_threshold
        self.n_clusters_ = 0
        self.labels_ = None
        self.clusters_ = None
        self.cluster_centroids_ = None
        self.execution_time_ = 0.0

    def fit(self, embeddings: np.ndarray) -> Tuple[np.ndarray, Dict[int, List[int]]]:
        """
        임베딩에 대해 Greedy 클러스터링을 수행합니다.

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

        # 클러스터 초기화
        clusters = {}  # cluster_id -> [member_indices]
        centroids = []  # 각 클러스터의 대표 임베딩 (첫 번째 멤버)
        labels = np.full(n, -1, dtype=int)
        current_cluster_id = 0

        for i in range(n):
            emb = normalized[i]
            assigned = False

            # 기존 클러스터와 비교
            for cluster_id, members in clusters.items():
                # 클러스터의 첫 번째 멤버(대표)와 비교
                representative_idx = members[0]
                representative_emb = normalized[representative_idx]

                similarity = np.dot(emb, representative_emb)

                if similarity >= self.similarity_threshold:
                    # 이 클러스터에 추가
                    clusters[cluster_id].append(i)
                    labels[i] = cluster_id
                    assigned = True
                    break  # First-match: 첫 번째 매칭 클러스터에 추가

            if not assigned:
                # 새 클러스터 생성
                clusters[current_cluster_id] = [i]
                centroids.append(emb)
                labels[i] = current_cluster_id
                current_cluster_id += 1

        self.labels_ = labels
        self.clusters_ = clusters
        self.cluster_centroids_ = centroids
        self.n_clusters_ = len(clusters)
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
            "mean_cluster_size": np.mean(cluster_sizes) if cluster_sizes else 0,
            "max_cluster_size": max(cluster_sizes) if cluster_sizes else 0,
            "singleton_count": sum(1 for s in cluster_sizes if s == 1),
            "execution_time": self.execution_time_,
            "similarity_threshold": self.similarity_threshold,
            "algorithm": "greedy_first_match"
        }


class GreedyCentroidClustering:
    """
    Greedy Centroid-based 클러스터링

    첫 번째 멤버 대신 클러스터 중심(centroid)과 비교하는 변형입니다.
    """

    def __init__(self, similarity_threshold: float = 0.75):
        self.similarity_threshold = similarity_threshold
        self.n_clusters_ = 0
        self.labels_ = None
        self.clusters_ = None
        self.execution_time_ = 0.0

    def fit(self, embeddings: np.ndarray) -> Tuple[np.ndarray, Dict[int, List[int]]]:
        """Centroid 기반 Greedy 클러스터링을 수행합니다."""
        start_time = time.time()

        n = len(embeddings)
        if n == 0:
            self.labels_ = np.array([])
            self.clusters_ = {}
            return self.labels_, self.clusters_

        normalized = self._normalize(embeddings)

        clusters = {}
        centroids = {}  # cluster_id -> centroid_embedding
        labels = np.full(n, -1, dtype=int)
        current_cluster_id = 0

        for i in range(n):
            emb = normalized[i]
            best_cluster = None
            best_similarity = -1

            # 모든 클러스터와 비교하여 가장 유사한 것 찾기
            for cluster_id, centroid in centroids.items():
                similarity = np.dot(emb, centroid)
                if similarity >= self.similarity_threshold and similarity > best_similarity:
                    best_similarity = similarity
                    best_cluster = cluster_id

            if best_cluster is not None:
                # 가장 유사한 클러스터에 추가
                clusters[best_cluster].append(i)
                labels[i] = best_cluster

                # Centroid 업데이트 (평균)
                member_embeddings = normalized[clusters[best_cluster]]
                new_centroid = np.mean(member_embeddings, axis=0)
                centroids[best_cluster] = new_centroid / np.linalg.norm(new_centroid)
            else:
                # 새 클러스터 생성
                clusters[current_cluster_id] = [i]
                centroids[current_cluster_id] = emb
                labels[i] = current_cluster_id
                current_cluster_id += 1

        self.labels_ = labels
        self.clusters_ = clusters
        self.n_clusters_ = len(clusters)
        self.execution_time_ = time.time() - start_time

        return self.labels_, self.clusters_

    def _normalize(self, embeddings: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        return embeddings / norms

    def get_cluster_info(self) -> Dict:
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
            "similarity_threshold": self.similarity_threshold,
            "algorithm": "greedy_centroid"
        }


def cluster_with_greedy(
    embeddings: np.ndarray,
    similarity_threshold: float = 0.75,
    use_centroid: bool = False
) -> Tuple[np.ndarray, Dict[int, List[int]], Dict]:
    """
    편의 함수: Greedy 클러스터링 수행

    Args:
        embeddings: 임베딩 배열
        similarity_threshold: 유사도 임계값
        use_centroid: True면 centroid 기반, False면 first-match 기반

    Returns:
        labels: 클러스터 레이블
        clusters: 클러스터 딕셔너리
        info: 클러스터링 정보
    """
    if use_centroid:
        clusterer = GreedyCentroidClustering(similarity_threshold=similarity_threshold)
    else:
        clusterer = GreedyClustering(similarity_threshold=similarity_threshold)

    labels, clusters = clusterer.fit(embeddings)
    info = clusterer.get_cluster_info()

    return labels, clusters, info


# 테스트 코드
if __name__ == "__main__":
    print("Greedy Clustering 테스트")
    print("=" * 40)

    np.random.seed(42)
    embeddings = np.random.randn(10, 3)

    # 일부 샘플을 유사하게 만들기
    embeddings[0] = embeddings[1] + np.random.randn(3) * 0.1
    embeddings[2] = embeddings[3] + np.random.randn(3) * 0.1

    # First-match 방식
    print("\n[First-Match 방식]")
    labels1, clusters1, info1 = cluster_with_greedy(
        embeddings, similarity_threshold=0.5, use_centroid=False
    )
    print(f"  클러스터 수: {info1['n_clusters']}")
    print(f"  클러스터 크기: {info1['cluster_sizes']}")

    # Centroid 방식
    print("\n[Centroid 방식]")
    labels2, clusters2, info2 = cluster_with_greedy(
        embeddings, similarity_threshold=0.5, use_centroid=True
    )
    print(f"  클러스터 수: {info2['n_clusters']}")
    print(f"  클러스터 크기: {info2['cluster_sizes']}")
