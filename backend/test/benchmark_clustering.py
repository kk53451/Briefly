"""
클러스터링 알고리즘 벤치마크 메인 스크립트

Master 브랜치(Greedy)와 Backend_v2(Union-Find 2-Pass),
그리고 기술 감사 권장(HAC Average Linkage)를 비교합니다.

사용법:
    # 전체 벤치마크 실행
    python benchmark_clustering.py --category politics --date 2024-01-15

    # 모든 카테고리 실행
    python benchmark_clustering.py --all-categories --date 2024-01-15

    # G-Eval 포함 (비용 발생)
    python benchmark_clustering.py --category economy --date 2024-01-15 --g-eval

출력:
    - results/benchmark_{category}_{date}.json: 상세 결과
    - results/benchmark_summary_{date}.json: 종합 요약
"""

import os
import sys
import json
import argparse
import time
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
import numpy as np

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv()

import openai
from app.utils.dynamo import get_news_by_category_and_date
from app.constants.category_map import CATEGORY_MAP

# 로컬 모듈 임포트
from algorithms import HACClustering, GreedyClustering, UnionFindClustering
from algorithms.hac_numpy import cluster_with_hac
from algorithms.greedy_clustering import cluster_with_greedy
from algorithms.unionfind_clustering import cluster_with_unionfind
from heuristic_labeler import HeuristicLabeler, create_ground_truth
from metrics import calculate_all_quality_metrics, calculate_efficiency_metrics, compare_algorithms
from g_eval import GEval, run_g_eval, format_geval_report

# OpenAI 설정
openai.api_key = os.getenv("OPENAI_API_KEY")

# 결과 저장 경로
RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')


def get_embedding(text: str, max_chars: int = 1000) -> list:
    """텍스트의 임베딩 벡터를 생성합니다."""
    try:
        res = openai.embeddings.create(
            input=[text[:max_chars]],
            model="text-embedding-3-small"
        )
        return res.data[0].embedding
    except Exception as e:
        print(f"⚠️ 임베딩 생성 실패: {e}")
        return []


def load_articles_from_dynamodb(category: str, date: str) -> List[Dict]:
    """DynamoDB에서 기사를 로드합니다."""
    print(f"📥 DynamoDB에서 데이터 로드 중... ({category}, {date})")
    articles = get_news_by_category_and_date(category, date)
    print(f"   ✅ {len(articles)}개 기사 로드됨")
    return articles


def generate_embeddings(articles: List[Dict]) -> Tuple[np.ndarray, List[Dict]]:
    """기사들의 임베딩을 생성합니다."""
    print(f"🔄 임베딩 생성 중... ({len(articles)}개 기사)")

    embeddings = []
    valid_articles = []

    for i, article in enumerate(articles):
        title = article.get("title", "")
        hilight = article.get("hilight", "") or article.get("content", "")[:500]
        text = f"{title} {hilight}"

        if len(text.strip()) < 10:
            continue

        emb = get_embedding(text)
        if emb:
            embeddings.append(emb)
            valid_articles.append(article)

            if (i + 1) % 20 == 0:
                print(f"   진행률: {i + 1}/{len(articles)} ({(i+1)/len(articles)*100:.1f}%)")

    print(f"   ✅ {len(embeddings)}개 임베딩 생성 완료")
    return np.array(embeddings), valid_articles


def run_single_algorithm(
    name: str,
    embeddings: np.ndarray,
    **kwargs
) -> Tuple[np.ndarray, Dict[int, List[int]], Dict]:
    """단일 알고리즘을 실행합니다."""
    print(f"\n🔧 {name} 알고리즘 실행 중...")

    start_time = time.time()

    if name == "greedy":
        labels, clusters, info = cluster_with_greedy(
            embeddings,
            similarity_threshold=kwargs.get("threshold", 0.75)
        )
    elif name == "union_find":
        labels, clusters, info = cluster_with_unionfind(
            embeddings,
            similarity_threshold=kwargs.get("threshold", 0.85),
            enable_outlier_filter=kwargs.get("enable_outlier_filter", True)
        )
    elif name == "hac_average":
        labels, clusters, info = cluster_with_hac(
            embeddings,
            similarity_threshold=kwargs.get("threshold", 0.55),
            linkage="average"
        )
    else:
        raise ValueError(f"알 수 없는 알고리즘: {name}")

    execution_time = time.time() - start_time
    info["total_execution_time"] = execution_time

    print(f"   ✅ 완료: {info['n_clusters']}개 클러스터, {execution_time:.2f}초")

    return labels, clusters, info


def run_benchmark(
    category: str,
    date: str,
    run_g_eval_flag: bool = False,
    thresholds: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    벤치마크를 실행합니다.

    Args:
        category: 카테고리 (영문)
        date: 날짜 (YYYY-MM-DD)
        run_g_eval_flag: G-Eval 실행 여부
        thresholds: 알고리즘별 임계값 오버라이드

    Returns:
        벤치마크 결과 딕셔너리
    """
    print("\n" + "=" * 60)
    print(f"🏁 클러스터링 벤치마크 시작")
    print(f"   카테고리: {category}")
    print(f"   날짜: {date}")
    print("=" * 60)

    # 기본 임계값
    default_thresholds = {
        "greedy": 0.75,      # Master 브랜치 기본값
        "union_find": 0.85,  # Backend_v2 기본값
        "hac_average": 0.55  # 권장값 (0.4-0.6 범위)
    }

    if thresholds:
        default_thresholds.update(thresholds)

    benchmark_start = time.time()

    # 1. 데이터 로드
    articles = load_articles_from_dynamodb(category, date)
    if len(articles) < 10:
        return {"error": f"기사 수 부족: {len(articles)}개"}

    # 2. 임베딩 생성
    embeddings, valid_articles = generate_embeddings(articles)
    if len(embeddings) < 10:
        return {"error": f"유효한 임베딩 부족: {len(embeddings)}개"}

    # 3. 휴리스틱 Ground Truth 생성
    print("\n📋 휴리스틱 Ground Truth 생성 중...")
    gt_labels, gt_clusters, gt_stats = create_ground_truth(
        valid_articles,
        title_threshold=0.90
    )
    print(f"   ✅ {gt_stats['total_clusters']}개 클러스터, {gt_stats['duplicate_pairs']}개 중복 쌍")

    # 4. 각 알고리즘 실행
    algorithm_results = {}

    for algo_name in ["greedy", "union_find", "hac_average"]:
        try:
            labels, clusters, algo_info = run_single_algorithm(
                algo_name,
                embeddings,
                threshold=default_thresholds[algo_name]
            )

            # 품질 메트릭 계산
            quality_metrics = calculate_all_quality_metrics(
                embeddings,
                labels,
                true_labels=gt_labels
            )

            # 효율성 메트릭 계산
            cluster_sizes = [len(m) for m in clusters.values()]
            efficiency_metrics = calculate_efficiency_metrics(
                n_original=len(valid_articles),
                n_clusters=len(clusters),
                cluster_sizes=cluster_sizes,
                execution_time=algo_info.get("total_execution_time", 0)
            )

            algorithm_results[algo_name] = {
                "labels": labels.tolist(),
                "n_clusters": len(clusters),
                "cluster_sizes": cluster_sizes,
                "algo_info": algo_info,
                "quality_metrics": quality_metrics,
                "efficiency_metrics": efficiency_metrics,
                "threshold": default_thresholds[algo_name]
            }

        except Exception as e:
            print(f"   ❌ {algo_name} 실패: {e}")
            algorithm_results[algo_name] = {"error": str(e)}

    # 5. G-Eval 실행 (옵션)
    geval_results = {}
    if run_g_eval_flag:
        print("\n🤖 G-Eval LLM 평가 실행 중...")
        for algo_name, result in algorithm_results.items():
            if "error" in result:
                continue

            # 클러스터 재구성
            labels = np.array(result["labels"])
            clusters = {}
            for i, label in enumerate(labels):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(i)

            # G-Eval 실행 (상위 5개 클러스터만)
            geval_result = run_g_eval(clusters, valid_articles, sample_size=5)
            geval_results[algo_name] = geval_result
            print(f"   {algo_name}: 일관성={geval_result['avg_coherence']:.2f}, 노이즈={geval_result['avg_noise']:.2f}")

    # 6. 알고리즘 비교
    comparison = compare_algorithms(algorithm_results)

    # 7. 결과 구성
    benchmark_time = time.time() - benchmark_start

    result = {
        "metadata": {
            "category": category,
            "date": date,
            "n_articles": len(valid_articles),
            "n_embeddings": len(embeddings),
            "benchmark_time_seconds": benchmark_time,
            "thresholds": default_thresholds,
            "timestamp": datetime.now().isoformat()
        },
        "ground_truth": {
            "n_clusters": gt_stats["total_clusters"],
            "n_duplicate_pairs": gt_stats["duplicate_pairs"],
            "cluster_sizes": [len(m) for m in gt_clusters.values()]
        },
        "algorithm_results": algorithm_results,
        "geval_results": geval_results if geval_results else None,
        "comparison": comparison
    }

    # 8. 결과 저장
    os.makedirs(RESULTS_DIR, exist_ok=True)
    filename = f"benchmark_{category}_{date}.json"
    filepath = os.path.join(RESULTS_DIR, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        # numpy 타입 변환
        def convert_numpy(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, (np.int64, np.int32)):
                return int(obj)
            elif isinstance(obj, (np.float64, np.float32)):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: convert_numpy(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy(v) for v in obj]
            return obj

        json.dump(convert_numpy(result), f, ensure_ascii=False, indent=2)

    print(f"\n💾 결과 저장됨: {filepath}")

    return result


def print_benchmark_report(result: Dict[str, Any]):
    """벤치마크 결과를 출력합니다."""
    print("\n" + "=" * 60)
    print("📊 벤치마크 결과 리포트")
    print("=" * 60)

    meta = result["metadata"]
    print(f"\n📋 메타데이터")
    print(f"   카테고리: {meta['category']}")
    print(f"   날짜: {meta['date']}")
    print(f"   기사 수: {meta['n_articles']}")
    print(f"   실행 시간: {meta['benchmark_time_seconds']:.1f}초")

    print(f"\n📌 Ground Truth (휴리스틱)")
    gt = result["ground_truth"]
    print(f"   클러스터 수: {gt['n_clusters']}")
    print(f"   중복 쌍: {gt['n_duplicate_pairs']}")

    print(f"\n🔬 알고리즘별 결과")
    print("-" * 50)

    for algo_name, algo_result in result["algorithm_results"].items():
        if "error" in algo_result:
            print(f"\n❌ {algo_name}: {algo_result['error']}")
            continue

        print(f"\n📍 {algo_name} (threshold={algo_result['threshold']})")
        print(f"   클러스터 수: {algo_result['n_clusters']}")

        qm = algo_result["quality_metrics"]
        print(f"   Silhouette Score: {qm.get('silhouette_score', 0):.4f}")
        print(f"   Pairwise F1: {qm.get('pairwise_f1', 0):.4f}")
        print(f"   Cluster Purity: {qm.get('cluster_purity', 0):.4f}")
        print(f"   ARI: {qm.get('adjusted_rand_index', 0):.4f}")

        em = algo_result["efficiency_metrics"]
        print(f"   중복 제거율: {em['reduction_percent']:.1f}%")
        print(f"   실행 시간: {em['execution_time_seconds']:.2f}초")

    # G-Eval 결과
    if result.get("geval_results"):
        print(f"\n🤖 G-Eval 결과")
        print("-" * 50)
        for algo_name, geval in result["geval_results"].items():
            print(f"   {algo_name}:")
            print(f"      일관성: {geval['avg_coherence']:.2f}/5")
            print(f"      노이즈: {geval['avg_noise']:.2f}/5 (낮을수록 좋음)")

    # 종합 순위
    comp = result["comparison"]
    print(f"\n🏆 종합 순위")
    print("-" * 50)
    for rank, (algo, score) in enumerate(comp["overall_ranking"].items(), 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, "  ")
        print(f"   {medal} {rank}위: {algo} (점수: {score})")

    print("\n" + "=" * 60)


def run_all_categories(
    date: str,
    run_g_eval_flag: bool = False
) -> Dict[str, Any]:
    """모든 카테고리에 대해 벤치마크를 실행합니다."""
    all_results = {}

    for ko_name, category_info in CATEGORY_MAP.items():
        category = category_info["api_name"]

        print(f"\n{'#' * 60}")
        print(f"# 카테고리: {ko_name} ({category})")
        print(f"{'#' * 60}")

        try:
            result = run_benchmark(category, date, run_g_eval_flag)
            all_results[category] = result
        except Exception as e:
            print(f"❌ {category} 벤치마크 실패: {e}")
            all_results[category] = {"error": str(e)}

    # 종합 요약 저장
    summary_path = os.path.join(RESULTS_DIR, f"benchmark_summary_{date}.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n💾 종합 요약 저장됨: {summary_path}")

    return all_results


def main():
    parser = argparse.ArgumentParser(
        description="클러스터링 알고리즘 벤치마크",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
    # 특정 카테고리 벤치마크
    python benchmark_clustering.py --category politics --date 2024-01-15

    # 모든 카테고리 벤치마크
    python benchmark_clustering.py --all-categories --date 2024-01-15

    # G-Eval 포함 (OpenAI API 비용 발생)
    python benchmark_clustering.py --category economy --g-eval

    # 임계값 조정
    python benchmark_clustering.py --category tech --threshold-greedy 0.70 --threshold-hac 0.50
        """
    )

    parser.add_argument(
        "--category",
        type=str,
        help="벤치마크할 카테고리 (영문)"
    )
    parser.add_argument(
        "--all-categories",
        action="store_true",
        help="모든 카테고리 벤치마크"
    )
    parser.add_argument(
        "--date",
        type=str,
        default=datetime.now().strftime("%Y-%m-%d"),
        help="벤치마크할 날짜 (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--g-eval",
        action="store_true",
        help="G-Eval LLM 평가 포함 (API 비용 발생)"
    )
    parser.add_argument(
        "--threshold-greedy",
        type=float,
        default=0.75,
        help="Greedy 알고리즘 임계값"
    )
    parser.add_argument(
        "--threshold-unionfind",
        type=float,
        default=0.85,
        help="Union-Find 알고리즘 임계값"
    )
    parser.add_argument(
        "--threshold-hac",
        type=float,
        default=0.55,
        help="HAC 알고리즘 임계값"
    )

    args = parser.parse_args()

    thresholds = {
        "greedy": args.threshold_greedy,
        "union_find": args.threshold_unionfind,
        "hac_average": args.threshold_hac
    }

    if args.all_categories:
        results = run_all_categories(args.date, args.g_eval)
    elif args.category:
        result = run_benchmark(
            args.category,
            args.date,
            args.g_eval,
            thresholds
        )
        print_benchmark_report(result)
    else:
        parser.print_help()
        print("\n❌ --category 또는 --all-categories 옵션이 필요합니다.")
        sys.exit(1)


if __name__ == "__main__":
    main()
