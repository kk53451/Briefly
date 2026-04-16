"""
Multi-pass DBSCAN Clustering (반복 DBSCAN)

DBSCAN 을 여러 번 돌려서 점진적으로 클러스터를 발견하는 방식입니다.

전략:
  1차 DBSCAN (eps=0.25, 엄격) → 확실한 클러스터 발견
  2차 DBSCAN (eps=0.35, 중간) → 1차 노이즈에서 추가 클러스터 발견
  3차 DBSCAN (eps=0.45, 느슨) → 2차 노이즈에서 마지막 클러스터 수거
  남은 노이즈 → 진짜 이상치로 판정

장점:
- 각 단계가 명확하여 디버깅/해석이 쉬움
- 엄격 → 느슨 순서라 고확신 클러스터부터 먼저 확정
- 노이즈를 점진적으로 수거하여 놓치는 기사가 적음
- eps 를 단계별로 제어 가능 (카테고리별 튜닝에 유리)

단점:
- HDBSCAN 대비 파라미터가 더 많음 (eps_list)
- 밀도가 매우 불균일한 데이터에서는 HDBSCAN 이 우세
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from sklearn.cluster import DBSCAN
import time


class MultiDBSCANClustering:
    """
    Multi-pass DBSCAN 클러스터링

    여러 eps 값으로 DBSCAN 을 반복 실행하여
    노이즈를 점진적으로 수거합니다.

    사용법:
        clusterer = MultiDBSCANClustering(eps_list=[0.25, 0.35, 0.45])
        labels, clusters = clusterer.fit(embeddings)
    """

    def __init__(
        self,
        eps_list: List[float] = None,
        min_samples: int = 3,
        metric: str = "cosine",
    ):
        """
        Args:
            eps_list: DBSCAN 을 반복할 eps 값 리스트 (엄격 → 느슨 순)
                      None 이면 기본값 [0.25, 0.35, 0.45] 사용
                      cosine 거리 기준: 0 = 동일, 1 = 직교, 2 = 반대
            min_samples: 코어 포인트 판정 최소 이웃 수
            metric: 거리 메트릭
        """
        self.eps_list = eps_list or [0.25, 0.35, 0.45]
        self.min_samples = min_samples
        self.metric = metric

        self.n_clusters_ = 0
        self.labels_ = None
        self.clusters_ = None
        self.noise_count_ = 0
        self.execution_time_ = 0.0
        self.pass_stats_ = []

    def fit(self, embeddings: np.ndarray) -> Tuple[np.ndarray, Dict[int, List[int]]]:
        """
        Multi-pass DBSCAN 클러스터링을 수행합니다.

        Args:
            embeddings: (n_samples, n_features) 형태의 임베딩 배열

        Returns:
            labels: 각 샘플의 클러스터 레이블 (노이즈 = -1)
            clusters: 클러스터 ID -> 멤버 인덱스 리스트
        """
        start_time = time.time()

        n = len(embeddings)
        if n == 0:
            self.labels_ = np.array([])
            self.clusters_ = {}
            return self.labels_, self.clusters_

        # 정규화
        normalized = self._normalize(embeddings)

        # 전체 레이블 배열 (-1 = 아직 미할당)
        final_labels = np.full(n, -1, dtype=int)
        next_cluster_id = 0
        self.pass_stats_ = []

        # 현재 노이즈 인덱스 (처음에는 전체)
        remaining_indices = np.arange(n)

        for pass_num, eps in enumerate(self.eps_list):
            if len(remaining_indices) < self.min_samples:
                break

            # 현재 남은 포인트에 대해 DBSCAN 실행
            remaining_embeddings = normalized[remaining_indices]

            dbscan = DBSCAN(
                eps=eps,
                min_samples=self.min_samples,
                metric=self.metric,
            )
            pass_labels = dbscan.fit_predict(remaining_embeddings)

            # 이번 pass 에서 발견된 클러스터 수
            unique_labels = set(pass_labels)
            unique_labels.discard(-1)
            n_found = len(unique_labels)

            # 발견된 클러스터를 전체 레이블에 반영
            new_noise_indices = []
            for local_idx, label in enumerate(pass_labels):
                global_idx = remaining_indices[local_idx]
                if label == -1:
                    new_noise_indices.append(global_idx)
                else:
                    final_labels[global_idx] = next_cluster_id + label

            next_cluster_id += n_found

            # pass 통계 기록
            self.pass_stats_.append({
                "pass": pass_num + 1,
                "eps": eps,
                "input_count": len(remaining_indices),
                "clusters_found": n_found,
                "noise_count": len(new_noise_indices),
                "clustered_count": len(remaining_indices) - len(new_noise_indices),
            })

            # 다음 pass 의 입력은 이번 pass 의 노이즈만
            remaining_indices = np.array(new_noise_indices)

        # 클러스터 딕셔너리 구성
        clusters = {}
        for idx, label in enumerate(final_labels):
            if label == -1:
                continue
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(idx)

        # 크기 내림차순 재정렬
        sorted_clusters = sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True)
        final_clusters = {}
        label_map = {}
        for new_id, (old_id, members) in enumerate(sorted_clusters):
            final_clusters[new_id] = members
            label_map[old_id] = new_id

        # 레이블 재매핑
        remapped_labels = np.full(n, -1, dtype=int)
        for idx, label in enumerate(final_labels):
            if label != -1:
                remapped_labels[idx] = label_map[label]

        self.labels_ = remapped_labels
        self.clusters_ = final_clusters
        self.n_clusters_ = len(final_clusters)
        self.noise_count_ = int(np.sum(remapped_labels == -1))
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
            "eps_list": self.eps_list,
            "min_samples": self.min_samples,
            "pass_stats": self.pass_stats_,
            "algorithm": "multi_dbscan"
        }


def cluster_with_multi_dbscan(
    embeddings: np.ndarray,
    eps_list: List[float] = None,
    min_samples: int = 3,
    metric: str = "cosine",
) -> Tuple[np.ndarray, Dict[int, List[int]], Dict]:
    """
    편의 함수: Multi-pass DBSCAN 클러스터링 수행

    Returns:
        labels, clusters, info
    """
    clusterer = MultiDBSCANClustering(
        eps_list=eps_list,
        min_samples=min_samples,
        metric=metric,
    )
    labels, clusters = clusterer.fit(embeddings)
    info = clusterer.get_cluster_info()
    return labels, clusters, info


if __name__ == "__main__":
    print("Multi-pass DBSCAN Clustering 테스트")
    print("=" * 40)

    np.random.seed(42)

    # 3개 클러스터 (밀도 다름) + 노이즈
    tight_cluster = np.random.randn(10, 3) * 0.1 + np.array([2, 0, 0])   # 밀집
    medium_cluster = np.random.randn(8, 3) * 0.3 + np.array([0, 2, 0])   # 중간
    loose_cluster = np.random.randn(5, 3) * 0.5 + np.array([0, 0, 2])    # 느슨
    noise = np.random.randn(4, 3) * 3

    embeddings = np.vstack([tight_cluster, medium_cluster, loose_cluster, noise])

    labels, clusters, info = cluster_with_multi_dbscan(
        embeddings,
        eps_list=[0.25, 0.40, 0.60],
        min_samples=3,
    )

    print(f"\n  클러스터 수: {info['n_clusters']}")
    print(f"  노이즈 수: {info['noise_count']}")
    print(f"  클러스터 크기: {info['cluster_sizes']}")
    print(f"  실행 시간: {info['execution_time']:.4f}초")

    print(f"\n  === Pass별 통계 ===")
    for ps in info["pass_stats"]:
        print(f"  Pass {ps['pass']} (eps={ps['eps']}): "
              f"입력 {ps['input_count']}개 -> "
              f"클러스터 {ps['clusters_found']}개 + "
              f"노이즈 {ps['noise_count']}개")
