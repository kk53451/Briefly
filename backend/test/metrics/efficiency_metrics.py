"""
클러스터링 효율성 메트릭

클러스터링 알고리즘의 효율성을 평가하는 메트릭을 제공합니다.

메트릭:
1. 실행 시간: 알고리즘 수행 시간
2. 클러스터 크기 분포: 클러스터 크기 통계
3. 중복 제거율: 원본 대비 감소율
4. 토큰 절약 추정: GPT 토큰 비용 절감 추정
"""

import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime


def calculate_efficiency_metrics(
    n_original: int,
    n_clusters: int,
    cluster_sizes: List[int],
    execution_time: float,
    avg_article_length: int = 1500
) -> Dict[str, Any]:
    """
    효율성 메트릭을 계산합니다.

    Args:
        n_original: 원본 기사 수
        n_clusters: 클러스터 수
        cluster_sizes: 클러스터별 기사 수 리스트
        execution_time: 실행 시간 (초)
        avg_article_length: 평균 기사 길이 (자, 토큰 추정용)

    Returns:
        효율성 메트릭 딕셔너리
    """
    # 기본 통계
    reduction_rate = 1 - (n_clusters / n_original) if n_original > 0 else 0
    articles_per_cluster = n_original / n_clusters if n_clusters > 0 else 0

    # 클러스터 크기 통계
    if cluster_sizes:
        size_array = np.array(cluster_sizes)
        cluster_stats = {
            "mean_size": float(np.mean(size_array)),
            "median_size": float(np.median(size_array)),
            "std_size": float(np.std(size_array)),
            "min_size": int(np.min(size_array)),
            "max_size": int(np.max(size_array)),
            "singleton_count": int(np.sum(size_array == 1)),
            "singleton_ratio": float(np.sum(size_array == 1) / len(size_array)),
            "multi_article_clusters": int(np.sum(size_array > 1)),
            "size_distribution": {
                "1": int(np.sum(size_array == 1)),
                "2-3": int(np.sum((size_array >= 2) & (size_array <= 3))),
                "4-5": int(np.sum((size_array >= 4) & (size_array <= 5))),
                "6-10": int(np.sum((size_array >= 6) & (size_array <= 10))),
                "10+": int(np.sum(size_array > 10))
            }
        }
    else:
        cluster_stats = {}

    # 토큰 비용 절감 추정
    # 가정: 1 한글 글자 ≈ 0.5 토큰, GPT-4o-mini 입력 토큰당 $0.15/1M
    tokens_per_char = 0.5
    cost_per_million_tokens = 0.15  # USD

    original_tokens = n_original * avg_article_length * tokens_per_char
    clustered_tokens = n_clusters * avg_article_length * tokens_per_char

    tokens_saved = original_tokens - clustered_tokens
    cost_saved = (tokens_saved / 1_000_000) * cost_per_million_tokens

    token_savings = {
        "original_tokens": int(original_tokens),
        "clustered_tokens": int(clustered_tokens),
        "tokens_saved": int(tokens_saved),
        "token_reduction_percent": (tokens_saved / original_tokens * 100) if original_tokens > 0 else 0,
        "estimated_cost_saved_usd": round(cost_saved, 4)
    }

    return {
        "n_original": n_original,
        "n_clusters": n_clusters,
        "reduction_rate": reduction_rate,
        "reduction_percent": reduction_rate * 100,
        "articles_per_cluster": articles_per_cluster,
        "execution_time_seconds": execution_time,
        "cluster_statistics": cluster_stats,
        "token_savings": token_savings,
        "timestamp": datetime.now().isoformat()
    }


def compare_algorithms(
    algorithm_results: Dict[str, Dict]
) -> Dict[str, Any]:
    """
    여러 알고리즘의 결과를 비교합니다.

    Args:
        algorithm_results: 알고리즘명 → 메트릭 딕셔너리

    Returns:
        비교 결과 딕셔너리
    """
    if not algorithm_results:
        return {}

    comparison = {
        "algorithms": list(algorithm_results.keys()),
        "metrics_comparison": {},
        "rankings": {},
        "summary": {}
    }

    # 비교할 메트릭 목록
    metrics_to_compare = [
        "n_clusters",
        "reduction_rate",
        "execution_time_seconds",
        "silhouette_score",
        "pairwise_f1",
        "cluster_purity"
    ]

    for metric in metrics_to_compare:
        values = {}
        for algo, results in algorithm_results.items():
            # 중첩된 딕셔너리에서도 값 찾기
            if metric in results:
                values[algo] = results[metric]
            elif "quality_metrics" in results and metric in results["quality_metrics"]:
                values[algo] = results["quality_metrics"][metric]
            elif "efficiency_metrics" in results and metric in results["efficiency_metrics"]:
                values[algo] = results["efficiency_metrics"][metric]

        if values:
            comparison["metrics_comparison"][metric] = values

    # 순위 계산 (높을수록 좋은 메트릭)
    higher_is_better = ["reduction_rate", "silhouette_score", "pairwise_f1", "cluster_purity"]
    lower_is_better = ["execution_time_seconds"]

    for metric, values in comparison["metrics_comparison"].items():
        if not values:
            continue

        sorted_algos = sorted(
            values.keys(),
            key=lambda x: values[x],
            reverse=(metric in higher_is_better)
        )

        comparison["rankings"][metric] = {
            algo: rank + 1
            for rank, algo in enumerate(sorted_algos)
        }

    # 종합 순위 계산
    algo_scores = {algo: 0 for algo in algorithm_results.keys()}

    for metric, rankings in comparison["rankings"].items():
        for algo, rank in rankings.items():
            # 순위를 점수로 변환 (1위 = 3점, 2위 = 2점, 3위 = 1점)
            algo_scores[algo] += len(algorithm_results) - rank + 1

    comparison["overall_ranking"] = dict(
        sorted(algo_scores.items(), key=lambda x: x[1], reverse=True)
    )

    # 요약 생성
    best_algo = max(algo_scores, key=algo_scores.get)
    comparison["summary"] = {
        "best_overall": best_algo,
        "algorithm_scores": algo_scores,
        "comparison_timestamp": datetime.now().isoformat()
    }

    return comparison


def format_comparison_report(comparison: Dict) -> str:
    """
    비교 결과를 읽기 쉬운 형태로 포맷팅합니다.

    Args:
        comparison: compare_algorithms() 결과

    Returns:
        포맷팅된 문자열
    """
    lines = []
    lines.append("=" * 60)
    lines.append("클러스터링 알고리즘 비교 리포트")
    lines.append("=" * 60)
    lines.append("")

    # 알고리즘 목록
    lines.append(f"비교 대상: {', '.join(comparison['algorithms'])}")
    lines.append("")

    # 메트릭별 비교
    lines.append("📊 메트릭별 결과")
    lines.append("-" * 40)

    for metric, values in comparison["metrics_comparison"].items():
        lines.append(f"\n{metric}:")
        for algo, value in values.items():
            if isinstance(value, float):
                lines.append(f"  {algo}: {value:.4f}")
            else:
                lines.append(f"  {algo}: {value}")

    # 순위
    lines.append("\n\n🏆 메트릭별 순위")
    lines.append("-" * 40)

    for metric, rankings in comparison["rankings"].items():
        lines.append(f"\n{metric}:")
        sorted_rankings = sorted(rankings.items(), key=lambda x: x[1])
        for algo, rank in sorted_rankings:
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, "  ")
            lines.append(f"  {medal} {rank}위: {algo}")

    # 종합 순위
    lines.append("\n\n📈 종합 순위")
    lines.append("-" * 40)

    for rank, (algo, score) in enumerate(comparison["overall_ranking"].items(), 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, "  ")
        lines.append(f"{medal} {rank}위: {algo} (점수: {score})")

    # 결론
    lines.append("\n\n💡 결론")
    lines.append("-" * 40)
    lines.append(f"최고 성능 알고리즘: {comparison['summary']['best_overall']}")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)


# 테스트 코드
if __name__ == "__main__":
    print("효율성 메트릭 테스트")
    print("=" * 50)

    # 테스트 데이터
    test_results = {
        "greedy": {
            "n_clusters": 45,
            "cluster_sizes": [1]*20 + [2]*15 + [3]*10,
            "execution_time_seconds": 0.5,
            "silhouette_score": 0.65,
            "pairwise_f1": 0.70
        },
        "union_find": {
            "n_clusters": 35,
            "cluster_sizes": [1]*10 + [2]*10 + [3]*10 + [5]*5,
            "execution_time_seconds": 1.2,
            "silhouette_score": 0.72,
            "pairwise_f1": 0.78
        },
        "hac_average": {
            "n_clusters": 40,
            "cluster_sizes": [1]*15 + [2]*12 + [3]*8 + [4]*5,
            "execution_time_seconds": 2.5,
            "silhouette_score": 0.80,
            "pairwise_f1": 0.85
        }
    }

    # 효율성 메트릭 계산
    print("\n[효율성 메트릭]")
    for algo, result in test_results.items():
        metrics = calculate_efficiency_metrics(
            n_original=100,
            n_clusters=result["n_clusters"],
            cluster_sizes=result["cluster_sizes"],
            execution_time=result["execution_time_seconds"]
        )
        print(f"\n{algo}:")
        print(f"  중복 제거율: {metrics['reduction_percent']:.1f}%")
        print(f"  토큰 절약: {metrics['token_savings']['token_reduction_percent']:.1f}%")

    # 알고리즘 비교
    print("\n\n" + "=" * 50)
    comparison = compare_algorithms(test_results)
    print(format_comparison_report(comparison))
