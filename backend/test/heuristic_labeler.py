"""
휴리스틱 기반 Ground Truth 라벨러

수동 라벨링 없이 휴리스틱 규칙으로 중복 기사를 자동 식별합니다.
클러스터링 알고리즘의 성능 평가를 위한 기준 라벨을 생성합니다.

휴리스틱 규칙:
1. 제목 유사도: 90% 이상 (SequenceMatcher 기반)
2. 시간 근접성: 24시간 이내 게시
3. 언론사(byline) 일치: 같은 언론사의 유사 제목
4. 숫자/고유명사 일치: 핵심 정보 일치 여부

사용법:
    labeler = HeuristicLabeler()
    labels = labeler.label(articles)
"""

import re
import numpy as np
from typing import List, Dict, Tuple, Set, Optional
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from collections import defaultdict


class HeuristicLabeler:
    """
    휴리스틱 기반 중복 기사 라벨러

    사용법:
        labeler = HeuristicLabeler(
            title_threshold=0.90,
            time_window_hours=24,
            consider_provider=True
        )
        labels, clusters, stats = labeler.label(articles)
    """

    def __init__(
        self,
        title_threshold: float = 0.90,
        time_window_hours: int = 24,
        consider_provider: bool = True,
        consider_numbers: bool = True,
        strict_mode: bool = False
    ):
        """
        Args:
            title_threshold: 제목 유사도 임계값 (0.90 = 90%)
            time_window_hours: 시간 근접성 윈도우 (시간 단위)
            consider_provider: 언론사 정보 고려 여부
            consider_numbers: 숫자/고유명사 일치 고려 여부
            strict_mode: True면 모든 조건 만족 필요, False면 제목만으로 충분
        """
        self.title_threshold = title_threshold
        self.time_window_hours = time_window_hours
        self.consider_provider = consider_provider
        self.consider_numbers = consider_numbers
        self.strict_mode = strict_mode

    def label(
        self,
        articles: List[Dict]
    ) -> Tuple[np.ndarray, Dict[int, List[int]], Dict]:
        """
        기사 리스트에 대해 휴리스틱 라벨링을 수행합니다.

        Args:
            articles: 기사 딕셔너리 리스트
                필수 필드: title
                선택 필드: published_at, provider, byline

        Returns:
            labels: 각 기사의 클러스터 레이블 (n_articles,)
            clusters: 클러스터 ID → 멤버 인덱스 리스트
            stats: 라벨링 통계
        """
        n = len(articles)
        if n == 0:
            return np.array([]), {}, {"total": 0}

        # 1. 제목 추출 및 정규화
        titles = [self._normalize_title(a.get("title", "")) for a in articles]

        # 2. 시간 정보 추출
        timestamps = [self._parse_timestamp(a.get("published_at")) for a in articles]

        # 3. 언론사 정보 추출
        providers = [
            a.get("provider", "") or a.get("byline", "")
            for a in articles
        ]

        # 4. Union-Find로 클러스터링 (휴리스틱 기반)
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

        # 5. 모든 쌍 비교
        match_details = []

        for i in range(n):
            for j in range(i + 1, n):
                is_duplicate, reason = self._is_duplicate(
                    titles[i], titles[j],
                    timestamps[i], timestamps[j],
                    providers[i], providers[j]
                )

                if is_duplicate:
                    union(i, j)
                    match_details.append({
                        "i": i, "j": j,
                        "reason": reason,
                        "title_i": titles[i][:50],
                        "title_j": titles[j][:50]
                    })

        # 6. 클러스터 그룹화
        clusters_dict = defaultdict(list)
        for i in range(n):
            root = find(i)
            clusters_dict[root].append(i)

        # 7. 클러스터 ID 재정렬
        clusters = {}
        labels = np.zeros(n, dtype=int)

        for new_id, (old_id, members) in enumerate(clusters_dict.items()):
            clusters[new_id] = members
            for member in members:
                labels[member] = new_id

        # 8. 통계 계산
        cluster_sizes = [len(m) for m in clusters.values()]
        stats = {
            "total_articles": n,
            "total_clusters": len(clusters),
            "duplicate_pairs": len(match_details),
            "cluster_sizes": cluster_sizes,
            "singleton_count": sum(1 for s in cluster_sizes if s == 1),
            "duplicate_count": sum(1 for s in cluster_sizes if s > 1),
            "largest_cluster": max(cluster_sizes) if cluster_sizes else 0,
            "match_details": match_details[:20],  # 상위 20개만
            "parameters": {
                "title_threshold": self.title_threshold,
                "time_window_hours": self.time_window_hours,
                "consider_provider": self.consider_provider,
                "strict_mode": self.strict_mode
            }
        }

        return labels, clusters, stats

    def _normalize_title(self, title: str) -> str:
        """제목을 정규화합니다."""
        if not title:
            return ""

        # 소문자 변환
        normalized = title.lower()

        # 특수문자 제거 (한글, 영문, 숫자만 유지)
        normalized = re.sub(r'[^\w\s가-힣]', ' ', normalized)

        # 연속 공백 제거
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        return normalized

    def _parse_timestamp(self, timestamp_str: Optional[str]) -> Optional[datetime]:
        """타임스탬프 문자열을 파싱합니다."""
        if not timestamp_str:
            return None

        # 여러 형식 시도
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d",
            "%Y%m%d%H%M%S",
            "%Y%m%d"
        ]

        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str[:len(fmt.replace("%", "").replace("-", "").replace(":", "").replace("T", "").replace(" ", "")) + 10], fmt)
            except ValueError:
                continue

        return None

    def _extract_numbers(self, text: str) -> Set[str]:
        """텍스트에서 숫자를 추출합니다."""
        # 숫자 패턴: 연속된 숫자 (금액, 퍼센트, 날짜 등)
        numbers = re.findall(r'\d+(?:\.\d+)?', text)
        return set(numbers)

    def _title_similarity(self, title1: str, title2: str) -> float:
        """
        두 제목 간의 유사도를 계산합니다.
        SequenceMatcher 사용 (LCS 기반)
        """
        if not title1 or not title2:
            return 0.0

        return SequenceMatcher(None, title1, title2).ratio()

    def _is_time_proximate(
        self,
        ts1: Optional[datetime],
        ts2: Optional[datetime]
    ) -> bool:
        """두 타임스탬프가 시간 윈도우 내에 있는지 확인합니다."""
        if ts1 is None or ts2 is None:
            return True  # 시간 정보 없으면 통과

        delta = abs((ts1 - ts2).total_seconds()) / 3600  # 시간 단위
        return delta <= self.time_window_hours

    def _is_duplicate(
        self,
        title1: str, title2: str,
        ts1: Optional[datetime], ts2: Optional[datetime],
        provider1: str, provider2: str
    ) -> Tuple[bool, str]:
        """
        두 기사가 중복인지 판단합니다.

        Returns:
            (is_duplicate, reason)
        """
        # 조건 1: 제목 유사도
        title_sim = self._title_similarity(title1, title2)
        title_match = title_sim >= self.title_threshold

        if not title_match:
            return False, ""

        # Strict 모드가 아니면 제목만으로 충분
        if not self.strict_mode:
            return True, f"title_sim={title_sim:.2f}"

        # Strict 모드: 추가 조건 확인
        reasons = [f"title_sim={title_sim:.2f}"]

        # 조건 2: 시간 근접성
        time_match = self._is_time_proximate(ts1, ts2)
        if not time_match:
            return False, ""
        reasons.append("time_proximate")

        # 조건 3: 언론사 일치 (옵션)
        if self.consider_provider and provider1 and provider2:
            if provider1 == provider2:
                reasons.append("same_provider")

        # 조건 4: 숫자 일치 (옵션)
        if self.consider_numbers:
            nums1 = self._extract_numbers(title1)
            nums2 = self._extract_numbers(title2)
            if nums1 and nums2:
                common = nums1 & nums2
                if len(common) >= 1:
                    reasons.append(f"common_nums={common}")

        return True, ", ".join(reasons)

    def evaluate_against_clustering(
        self,
        heuristic_labels: np.ndarray,
        predicted_labels: np.ndarray
    ) -> Dict:
        """
        휴리스틱 라벨과 예측 라벨을 비교하여 성능을 평가합니다.

        Args:
            heuristic_labels: 휴리스틱 기반 Ground Truth
            predicted_labels: 클러스터링 알고리즘 예측 라벨

        Returns:
            평가 메트릭 딕셔너리
        """
        n = len(heuristic_labels)

        if n != len(predicted_labels):
            raise ValueError("라벨 길이가 일치하지 않습니다")

        # Pairwise 평가
        true_positives = 0  # 둘 다 같은 클러스터로 예측
        false_positives = 0  # 다른데 같다고 예측
        false_negatives = 0  # 같은데 다르다고 예측
        true_negatives = 0  # 둘 다 다른 클러스터로 예측

        for i in range(n):
            for j in range(i + 1, n):
                heuristic_same = heuristic_labels[i] == heuristic_labels[j]
                predicted_same = predicted_labels[i] == predicted_labels[j]

                if heuristic_same and predicted_same:
                    true_positives += 1
                elif not heuristic_same and predicted_same:
                    false_positives += 1
                elif heuristic_same and not predicted_same:
                    false_negatives += 1
                else:
                    true_negatives += 1

        # 메트릭 계산
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        total_pairs = n * (n - 1) // 2
        accuracy = (true_positives + true_negatives) / total_pairs if total_pairs > 0 else 0

        return {
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "accuracy": accuracy,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "true_negatives": true_negatives,
            "total_pairs": total_pairs
        }


def create_ground_truth(
    articles: List[Dict],
    title_threshold: float = 0.90,
    strict_mode: bool = False
) -> Tuple[np.ndarray, Dict[int, List[int]], Dict]:
    """
    편의 함수: Ground Truth 라벨 생성

    Args:
        articles: 기사 리스트
        title_threshold: 제목 유사도 임계값
        strict_mode: 엄격 모드 여부

    Returns:
        labels, clusters, stats
    """
    labeler = HeuristicLabeler(
        title_threshold=title_threshold,
        strict_mode=strict_mode
    )

    return labeler.label(articles)


# 테스트 코드
if __name__ == "__main__":
    print("휴리스틱 라벨러 테스트")
    print("=" * 50)

    # 테스트 데이터
    test_articles = [
        {"title": "삼성전자 3분기 영업이익 10조원 달성", "provider": "연합뉴스", "published_at": "2024-01-15 09:00:00"},
        {"title": "삼성전자, 3분기 영업익 10조원 기록", "provider": "조선일보", "published_at": "2024-01-15 09:30:00"},
        {"title": "삼성전자 3분기 실적 발표... 영업이익 10조", "provider": "MBC", "published_at": "2024-01-15 10:00:00"},
        {"title": "애플 아이폰 16 출시 임박", "provider": "연합뉴스", "published_at": "2024-01-15 11:00:00"},
        {"title": "애플, 아이폰16 다음달 출시 예정", "provider": "SBS", "published_at": "2024-01-15 11:30:00"},
        {"title": "현대차 전기차 판매량 역대 최고", "provider": "한경", "published_at": "2024-01-15 12:00:00"},
    ]

    # 라벨링 수행
    labeler = HeuristicLabeler(title_threshold=0.85)
    labels, clusters, stats = labeler.label(test_articles)

    print(f"\n기사 수: {stats['total_articles']}")
    print(f"클러스터 수: {stats['total_clusters']}")
    print(f"중복 쌍 수: {stats['duplicate_pairs']}")

    print("\n클러스터 결과:")
    for cluster_id, members in clusters.items():
        print(f"\n  클러스터 {cluster_id}:")
        for member_idx in members:
            title = test_articles[member_idx]["title"][:40]
            print(f"    - {title}...")

    print("\n매칭 상세:")
    for match in stats["match_details"]:
        print(f"  {match['i']}-{match['j']}: {match['reason']}")
