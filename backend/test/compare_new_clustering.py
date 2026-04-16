"""
HDBSCAN vs Multi-DBSCAN vs Union-Find 클러스터링 비교 실험

두 가지 모드:
  1. --synthetic: 합성 데이터로 즉시 실행 (의존성 없음)
  2. --dynamodb:  실제 DynamoDB 기사로 실행 (AWS 자격증명 필요)

사용법:
    cd backend/test
    pip install hdbscan scikit-learn

    # 합성 데이터 (즉시 실행)
    python compare_new_clustering.py --synthetic

    # 실제 데이터
    python compare_new_clustering.py --dynamodb --category economy --date 2025-11-30

출력:
    results/new_clustering_comparison_{timestamp}.json
    터미널에 비교 테이블 출력
"""

import os
import sys
import json
import time
import argparse
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from algorithms.hdbscan_clustering import cluster_with_hdbscan
from algorithms.multi_dbscan_clustering import cluster_with_multi_dbscan
from algorithms.unionfind_clustering import cluster_with_unionfind

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


# ============================================================
# 합성 데이터 생성
# ============================================================

def generate_synthetic_news_embeddings(
    n_topics: int = 12,
    articles_per_topic: tuple = (3, 15),
    n_noise: int = 10,
    dim: int = 128,  # 1024는 고차원 저주로 합성 데이터에 부적합. 128로 축소.
    seed: int = 42,
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    뉴스 클러스터링을 시뮬레이션하는 합성 임베딩 생성.

    실제 뉴스 데이터의 특성을 반영:
    - 토픽마다 기사 수가 다름 (대형 이슈 vs 단독 기사)
    - 토픽 내 기사는 유사하지만 동일하지 않음 (다른 관점/언론사)
    - 노이즈 (광고, 후원 기사 등)

    Returns:
        embeddings: (n_samples, dim) 임베딩 배열
        true_labels: 정답 레이블 (-1 = 노이즈)
        topic_names: 토픽 이름 리스트 (시각화용)
    """
    rng = np.random.RandomState(seed)

    topic_names = [
        "삼성전자 실적 발표", "한국은행 금리 동결", "전기차 보조금 개편",
        "코스피 2700선 회복", "원달러 환율 하락", "반도체 수출 증가",
        "부동산 정책 발표", "유가 상승 전망", "스타트업 투자 동향",
        "무역수지 흑자", "가상화폐 규제", "고용 시장 동향",
    ][:n_topics]

    all_embeddings = []
    all_labels = []

    for topic_id in range(n_topics):
        # 토픽 중심 벡터
        center = rng.randn(dim)
        center = center / np.linalg.norm(center)

        # 토픽당 기사 수 (불균일하게)
        n_articles = rng.randint(articles_per_topic[0], articles_per_topic[1] + 1)

        # 토픽 내 분산 (밀도가 다른 클러스터 시뮬레이션)
        spread = rng.uniform(0.05, 0.25)

        for _ in range(n_articles):
            noise = rng.randn(dim) * spread
            vec = center + noise
            vec = vec / np.linalg.norm(vec)
            all_embeddings.append(vec)
            all_labels.append(topic_id)

    # 노이즈 추가 (광고, 후원 기사 등)
    for _ in range(n_noise):
        vec = rng.randn(dim)
        vec = vec / np.linalg.norm(vec)
        all_embeddings.append(vec)
        all_labels.append(-1)

    embeddings = np.array(all_embeddings)
    true_labels = np.array(all_labels)

    # 셔플
    perm = rng.permutation(len(embeddings))
    embeddings = embeddings[perm]
    true_labels = true_labels[perm]

    return embeddings, true_labels, topic_names


# ============================================================
# 메트릭 계산
# ============================================================

def calculate_metrics(
    pred_labels: np.ndarray,
    true_labels: np.ndarray,
    embeddings: np.ndarray,
    info: Dict,
) -> Dict:
    """클러스터링 품질 메트릭을 계산합니다."""
    from sklearn.metrics import (
        adjusted_rand_score,
        normalized_mutual_info_score,
        silhouette_score,
    )

    metrics = {}

    # 기본 통계
    metrics["n_clusters"] = info.get("n_clusters", 0)
    metrics["noise_count"] = info.get("noise_count", info.get("outlier_count", 0))
    metrics["noise_ratio"] = metrics["noise_count"] / len(pred_labels) if len(pred_labels) > 0 else 0
    metrics["execution_time"] = info.get("execution_time", 0)

    cluster_sizes = info.get("cluster_sizes", [])
    metrics["cluster_sizes"] = cluster_sizes
    metrics["mean_cluster_size"] = float(np.mean(cluster_sizes)) if cluster_sizes else 0
    metrics["max_cluster_size"] = max(cluster_sizes) if cluster_sizes else 0
    metrics["singleton_clusters"] = sum(1 for s in cluster_sizes if s == 1)

    # 정답 레이블이 있을 때만 외부 메트릭 계산
    if true_labels is not None:
        # 노이즈(-1)를 제외한 포인트만으로 비교
        mask = (pred_labels != -1) & (true_labels != -1)
        if mask.sum() > 1:
            metrics["adjusted_rand_index"] = float(adjusted_rand_score(
                true_labels[mask], pred_labels[mask]
            ))
            metrics["normalized_mutual_info"] = float(normalized_mutual_info_score(
                true_labels[mask], pred_labels[mask]
            ))

        # 노이즈 탐지 정확도
        true_noise = (true_labels == -1)
        pred_noise = (pred_labels == -1)
        if true_noise.sum() > 0:
            metrics["noise_recall"] = float((true_noise & pred_noise).sum() / true_noise.sum())
        if pred_noise.sum() > 0:
            metrics["noise_precision"] = float((true_noise & pred_noise).sum() / pred_noise.sum())

    # 내부 메트릭 (정답 없이도 계산 가능)
    non_noise_mask = pred_labels != -1
    n_non_noise = non_noise_mask.sum()
    n_unique = len(set(pred_labels[non_noise_mask]))
    if n_non_noise > 1 and 2 <= n_unique < n_non_noise:
        try:
            metrics["silhouette_score"] = float(silhouette_score(
                embeddings[non_noise_mask],
                pred_labels[non_noise_mask],
                metric="cosine",
            ))
        except ValueError:
            pass  # 엣지 케이스 무시

    return metrics


# ============================================================
# 실험 실행
# ============================================================

def run_comparison(
    embeddings: np.ndarray,
    true_labels: np.ndarray = None,
    topic_names: List[str] = None,
) -> List[Dict]:
    """모든 알고리즘을 비교 실행합니다."""
    results = []

    # === 1. HDBSCAN (여러 min_cluster_size) ===
    for mcs in [3, 4, 5]:
        print(f"\n{'='*60}")
        print(f"HDBSCAN (min_cluster_size={mcs})")
        print(f"{'='*60}")

        labels, clusters, info = cluster_with_hdbscan(
            embeddings, min_cluster_size=mcs
        )
        metrics = calculate_metrics(labels, true_labels, embeddings, info)
        metrics["algorithm"] = f"hdbscan_mcs{mcs}"
        metrics["parameters"] = {"min_cluster_size": mcs}
        print_result(metrics)
        results.append(metrics)

    # === 2. Multi-DBSCAN (여러 eps 전략) ===
    eps_strategies = {
        "conservative": [0.20, 0.30, 0.40],
        "moderate": [0.25, 0.35, 0.45],
        "aggressive": [0.30, 0.40, 0.55],
    }

    for strategy_name, eps_list in eps_strategies.items():
        print(f"\n{'='*60}")
        print(f"Multi-DBSCAN ({strategy_name}: eps={eps_list})")
        print(f"{'='*60}")

        labels, clusters, info = cluster_with_multi_dbscan(
            embeddings, eps_list=eps_list, min_samples=3
        )
        metrics = calculate_metrics(labels, true_labels, embeddings, info)
        metrics["algorithm"] = f"multi_dbscan_{strategy_name}"
        metrics["parameters"] = {"eps_list": eps_list, "min_samples": 3}
        metrics["pass_stats"] = info.get("pass_stats", [])
        print_result(metrics)

        if info.get("pass_stats"):
            print(f"  Pass 상세:")
            for ps in info["pass_stats"]:
                print(f"    Pass {ps['pass']} (eps={ps['eps']}): "
                      f"{ps['input_count']}개 -> "
                      f"클러스터 {ps['clusters_found']}개 + "
                      f"노이즈 {ps['noise_count']}개")

        results.append(metrics)

    # === 3. Union-Find (기존, 비교용) ===
    for threshold in [0.70, 0.80, 0.85]:
        print(f"\n{'='*60}")
        print(f"Union-Find (threshold={threshold})")
        print(f"{'='*60}")

        labels, clusters, info = cluster_with_unionfind(
            embeddings,
            similarity_threshold=threshold,
            enable_outlier_filter=True,
        )
        metrics = calculate_metrics(labels, true_labels, embeddings, info)
        metrics["algorithm"] = f"unionfind_t{threshold}"
        metrics["parameters"] = {"similarity_threshold": threshold}
        print_result(metrics)
        results.append(metrics)

    return results


def print_result(metrics: Dict):
    """결과를 보기 좋게 출력합니다."""
    print(f"  Clusters: {metrics['n_clusters']}")
    print(f"  Noise: {metrics['noise_count']} ({metrics['noise_ratio']:.1%})")
    print(f"  Cluster sizes: {metrics.get('cluster_sizes', [])[:10]}{'...' if len(metrics.get('cluster_sizes',[])) > 10 else ''}")
    print(f"  Mean size: {metrics['mean_cluster_size']:.1f}, Max: {metrics['max_cluster_size']}")
    print(f"  Singletons: {metrics['singleton_clusters']}")
    print(f"  Time: {metrics['execution_time']:.4f}s")

    if "adjusted_rand_index" in metrics:
        print(f"  ARI: {metrics['adjusted_rand_index']:.4f}")
        print(f"  NMI: {metrics['normalized_mutual_info']:.4f}")
    if "silhouette_score" in metrics:
        print(f"  Silhouette: {metrics['silhouette_score']:.4f}")
    if "noise_recall" in metrics:
        print(f"  Noise recall: {metrics['noise_recall']:.2%}")
    if "noise_precision" in metrics:
        print(f"  Noise precision: {metrics['noise_precision']:.2%}")


def print_summary_table(results: List[Dict]):
    """최종 비교 테이블을 출력합니다."""
    print(f"\n\n{'='*90}")
    print(f"{'ALGORITHM':<30} {'CLUST':>5} {'NOISE':>5} {'ARI':>7} {'NMI':>7} {'SIL':>7} {'TIME':>8}")
    print(f"{'='*90}")

    for r in sorted(results, key=lambda x: x.get("adjusted_rand_index", 0), reverse=True):
        ari = f"{r['adjusted_rand_index']:.4f}" if "adjusted_rand_index" in r else "  N/A"
        nmi = f"{r['normalized_mutual_info']:.4f}" if "normalized_mutual_info" in r else "  N/A"
        sil = f"{r['silhouette_score']:.4f}" if "silhouette_score" in r else "  N/A"
        print(f"{r['algorithm']:<30} {r['n_clusters']:>5} {r['noise_count']:>5} {ari:>7} {nmi:>7} {sil:>7} {r['execution_time']:>7.3f}s")

    print(f"{'='*90}")
    print(f"\nARI = Adjusted Rand Index (1.0 = perfect, higher is better)")
    print(f"NMI = Normalized Mutual Information (1.0 = perfect, higher is better)")
    print(f"SIL = Silhouette Score (-1~1, higher is better)")


# ============================================================
# 메인
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="HDBSCAN vs Multi-DBSCAN vs Union-Find 비교")
    parser.add_argument("--synthetic", action="store_true", help="합성 데이터로 실행")
    parser.add_argument("--dynamodb", action="store_true", help="DynamoDB 기사로 실행")
    parser.add_argument("--category", default="economy", help="카테고리 (dynamodb 모드)")
    parser.add_argument("--date", default="2025-11-30", help="날짜 (dynamodb 모드)")
    parser.add_argument("--n-topics", type=int, default=12, help="합성 토픽 수")
    parser.add_argument("--n-noise", type=int, default=10, help="합성 노이즈 수")
    args = parser.parse_args()

    if not args.synthetic and not args.dynamodb:
        args.synthetic = True
        print("모드 미지정 -> --synthetic 으로 실행합니다.\n")

    if args.synthetic:
        print(f"=== 합성 데이터 모드 ===")
        print(f"토픽 {args.n_topics}개 + 노이즈 {args.n_noise}개 생성\n")

        embeddings, true_labels, topic_names = generate_synthetic_news_embeddings(
            n_topics=args.n_topics,
            n_noise=args.n_noise,
        )
        print(f"총 {len(embeddings)}개 벡터 생성 (dim={embeddings.shape[1]})")
        print(f"정답 토픽: {topic_names}")

        results = run_comparison(embeddings, true_labels, topic_names)

    elif args.dynamodb:
        print(f"=== DynamoDB 모드 ===")
        print(f"카테고리: {args.category}, 날짜: {args.date}\n")

        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent.parent / ".env")

        from app.utils.dynamo import get_news_by_category_and_date

        articles = get_news_by_category_and_date(args.category, args.date)
        if not articles:
            print(f"기사가 없습니다. 카테고리/날짜를 확인하세요.")
            return

        print(f"기사 {len(articles)}개 로드됨. 임베딩 생성 중...")

        # TODO: KURE-v1 로컬 임베딩으로 교체
        from openai import OpenAI
        client = OpenAI()
        texts = [(a.get("title", "") + " " + a.get("content", ""))[:1000] for a in articles]

        emb_list = []
        for i, text in enumerate(texts):
            res = client.embeddings.create(input=[text], model="text-embedding-3-small")
            emb_list.append(res.data[0].embedding)
            if (i + 1) % 50 == 0:
                print(f"  {i+1}/{len(texts)} 완료")

        embeddings = np.array(emb_list)
        print(f"임베딩 완료: {embeddings.shape}")

        results = run_comparison(embeddings, true_labels=None)

    # 비교 테이블 출력
    print_summary_table(results)

    # 결과 저장
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = RESULTS_DIR / f"new_clustering_comparison_{ts}.json"

    # numpy 타입을 JSON 직렬화 가능하게 변환
    def convert(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=convert)

    print(f"\n결과 저장: {output_file}")


if __name__ == "__main__":
    main()
