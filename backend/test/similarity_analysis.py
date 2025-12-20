"""
유사도 분포 분석 스크립트

text-embedding-3-small 모델의 코사인 유사도 분포를 분석하여
최적의 클러스터링 임계값을 탐색합니다.

기술 감사 보고서 제언:
- text-embedding-3-small은 ada-002와 벡터 공간 특성이 다름
- 관련 없는 문서 간 유사도가 0에 가깝게 분포
- 기존 0.85 임계값은 너무 높을 수 있음 (파편화 위험)
- 0.4 ~ 0.6 범위에서 새로운 임계값 탐색 필요

사용법:
    python similarity_analysis.py --category politics --date 2024-01-15
    python similarity_analysis.py --all-categories --date 2024-01-15
"""

import os
import sys
import json
import argparse
import numpy as np
from datetime import datetime
from collections import defaultdict

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv()

import openai
from app.utils.dynamo import get_news_by_category_and_date
from app.constants.category_map import CATEGORY_MAP

# OpenAI 설정
openai.api_key = os.getenv("OPENAI_API_KEY")

# 결과 저장 경로
RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')


def get_embedding(text: str, max_chars: int = 1000) -> list:
    """
    텍스트의 임베딩 벡터를 생성합니다.

    Args:
        text: 임베딩할 텍스트
        max_chars: 최대 문자 수 (토큰 제한용)

    Returns:
        임베딩 벡터 리스트 (1536차원) 또는 빈 리스트
    """
    try:
        res = openai.embeddings.create(
            input=[text[:max_chars]],
            model="text-embedding-3-small"
        )
        return res.data[0].embedding
    except Exception as e:
        print(f"⚠️ 임베딩 생성 실패: {e}")
        return []


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    두 벡터 간의 코사인 유사도를 계산합니다.
    """
    if len(vec1) == 0 or len(vec2) == 0:
        return 0.0
    return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))


def compute_similarity_matrix(embeddings: list[np.ndarray]) -> np.ndarray:
    """
    임베딩 리스트에서 모든 쌍의 코사인 유사도 행렬을 계산합니다.

    Args:
        embeddings: 임베딩 벡터 리스트

    Returns:
        n x n 유사도 행렬
    """
    n = len(embeddings)
    matrix = np.zeros((n, n))

    # 정규화된 임베딩
    normalized = []
    for emb in embeddings:
        norm = np.linalg.norm(emb)
        if norm > 0:
            normalized.append(emb / norm)
        else:
            normalized.append(emb)
    normalized = np.array(normalized)

    # 행렬 곱으로 한 번에 계산 (효율적)
    matrix = np.dot(normalized, normalized.T)

    return matrix


def analyze_similarity_distribution(similarity_matrix: np.ndarray) -> dict:
    """
    유사도 행렬의 분포 통계를 분석합니다.

    Args:
        similarity_matrix: n x n 유사도 행렬

    Returns:
        분포 통계 딕셔너리
    """
    n = len(similarity_matrix)

    # 상삼각 행렬만 추출 (대각선 제외, 중복 쌍 제거)
    upper_triangle_indices = np.triu_indices(n, k=1)
    similarities = similarity_matrix[upper_triangle_indices]

    # 기본 통계
    stats = {
        "count": len(similarities),
        "mean": float(np.mean(similarities)),
        "std": float(np.std(similarities)),
        "min": float(np.min(similarities)),
        "max": float(np.max(similarities)),
        "median": float(np.median(similarities)),
        "percentiles": {
            "5%": float(np.percentile(similarities, 5)),
            "10%": float(np.percentile(similarities, 10)),
            "25%": float(np.percentile(similarities, 25)),
            "50%": float(np.percentile(similarities, 50)),
            "75%": float(np.percentile(similarities, 75)),
            "90%": float(np.percentile(similarities, 90)),
            "95%": float(np.percentile(similarities, 95)),
        }
    }

    # 히스토그램 빈 (0.0 ~ 1.0, 0.05 단위)
    bins = np.arange(0, 1.05, 0.05)
    hist, _ = np.histogram(similarities, bins=bins)
    stats["histogram"] = {
        "bins": [f"{bins[i]:.2f}-{bins[i+1]:.2f}" for i in range(len(bins)-1)],
        "counts": hist.tolist()
    }

    # 임계값별 클러스터링 영향 분석
    thresholds = [0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90]
    threshold_analysis = {}
    for threshold in thresholds:
        above_threshold = np.sum(similarities >= threshold)
        percentage = (above_threshold / len(similarities)) * 100 if len(similarities) > 0 else 0
        threshold_analysis[f"{threshold:.2f}"] = {
            "pairs_above": int(above_threshold),
            "percentage": round(percentage, 2)
        }
    stats["threshold_analysis"] = threshold_analysis

    return stats


def generate_histogram_ascii(histogram: dict, width: int = 50) -> str:
    """
    히스토그램을 ASCII 그래프로 출력합니다.
    """
    bins = histogram["bins"]
    counts = histogram["counts"]
    max_count = max(counts) if counts else 1

    lines = []
    lines.append("\n📊 유사도 분포 히스토그램")
    lines.append("=" * (width + 20))

    for i, (bin_range, count) in enumerate(zip(bins, counts)):
        bar_length = int((count / max_count) * width) if max_count > 0 else 0
        bar = "█" * bar_length
        lines.append(f"{bin_range} | {bar} ({count})")

    lines.append("=" * (width + 20))
    return "\n".join(lines)


def fetch_articles_from_dynamodb(category: str, date: str) -> list[dict]:
    """
    DynamoDB에서 기사를 가져옵니다.

    Args:
        category: 영문 카테고리명 (politics, economy 등)
        date: 날짜 (YYYY-MM-DD)

    Returns:
        기사 딕셔너리 리스트
    """
    try:
        articles = get_news_by_category_and_date(category, date)
        print(f"✅ {category} 카테고리에서 {len(articles)}개 기사 조회됨")
        return articles
    except Exception as e:
        print(f"❌ DynamoDB 조회 실패: {e}")
        return []


def prepare_article_texts(articles: list[dict]) -> tuple[list[str], list[dict]]:
    """
    기사에서 임베딩용 텍스트를 추출합니다.

    Args:
        articles: 기사 딕셔너리 리스트

    Returns:
        (텍스트 리스트, 유효한 기사 메타데이터 리스트)
    """
    texts = []
    valid_articles = []

    for article in articles:
        title = article.get("title", "")
        hilight = article.get("hilight", "") or article.get("content", "")[:500]

        # 제목 + 하이라이트를 합쳐서 임베딩 텍스트 생성
        text = f"{title} {hilight}"

        if len(text.strip()) > 10:  # 최소 길이 체크
            texts.append(text)
            valid_articles.append({
                "news_id": article.get("news_id"),
                "title": title[:100],  # 로그용 축약
                "provider": article.get("provider", "")
            })

    return texts, valid_articles


def run_similarity_analysis(category: str, date: str, save_results: bool = True) -> dict:
    """
    특정 카테고리의 유사도 분포를 분석합니다.

    Args:
        category: 영문 카테고리명
        date: 날짜 (YYYY-MM-DD)
        save_results: 결과 저장 여부

    Returns:
        분석 결과 딕셔너리
    """
    print(f"\n{'='*60}")
    print(f"📊 유사도 분포 분석 시작")
    print(f"   카테고리: {category}")
    print(f"   날짜: {date}")
    print(f"{'='*60}\n")

    # 1. 데이터 로드
    articles = fetch_articles_from_dynamodb(category, date)
    if not articles:
        return {"error": "기사를 찾을 수 없습니다"}

    # 2. 텍스트 추출
    texts, valid_articles = prepare_article_texts(articles)
    print(f"📝 유효한 텍스트: {len(texts)}개")

    if len(texts) < 2:
        return {"error": "분석에 필요한 기사가 부족합니다 (최소 2개 필요)"}

    # 3. 임베딩 생성
    print(f"\n🔄 임베딩 생성 중... (약 {len(texts)}회 API 호출)")
    embeddings = []
    for i, text in enumerate(texts):
        emb = get_embedding(text)
        if emb:
            embeddings.append(np.array(emb))
            if (i + 1) % 10 == 0:
                print(f"   진행률: {i + 1}/{len(texts)} ({(i+1)/len(texts)*100:.1f}%)")
        else:
            print(f"   ⚠️ 임베딩 실패: {valid_articles[i]['title'][:30]}...")

    if len(embeddings) < 2:
        return {"error": "유효한 임베딩이 부족합니다"}

    print(f"✅ 임베딩 생성 완료: {len(embeddings)}개")

    # 4. 유사도 행렬 계산
    print("\n🔄 유사도 행렬 계산 중...")
    similarity_matrix = compute_similarity_matrix(embeddings)
    print(f"✅ {len(embeddings)} x {len(embeddings)} 유사도 행렬 생성")

    # 5. 분포 분석
    print("\n📊 분포 통계 분석 중...")
    stats = analyze_similarity_distribution(similarity_matrix)

    # 6. 결과 구성
    result = {
        "category": category,
        "date": date,
        "article_count": len(embeddings),
        "pair_count": stats["count"],
        "statistics": stats,
        "analyzed_at": datetime.now().isoformat()
    }

    # 7. 결과 출력
    print("\n" + "="*60)
    print("📈 분석 결과")
    print("="*60)
    print(f"   기사 수: {len(embeddings)}개")
    print(f"   비교 쌍 수: {stats['count']}개")
    print(f"\n📊 유사도 통계:")
    print(f"   평균: {stats['mean']:.4f}")
    print(f"   표준편차: {stats['std']:.4f}")
    print(f"   최소: {stats['min']:.4f}")
    print(f"   최대: {stats['max']:.4f}")
    print(f"   중앙값: {stats['median']:.4f}")

    print(f"\n📈 백분위수:")
    for pct, val in stats["percentiles"].items():
        print(f"   {pct}: {val:.4f}")

    # 히스토그램 출력
    print(generate_histogram_ascii(stats["histogram"]))

    # 임계값 분석 출력
    print("\n🎯 임계값별 분석:")
    print("-" * 40)
    for threshold, data in stats["threshold_analysis"].items():
        print(f"   {threshold}: {data['pairs_above']:,}쌍 ({data['percentage']:.1f}%)")

    # 권장 임계값 제안
    print("\n💡 권장 임계값 제안:")
    optimal_threshold = suggest_optimal_threshold(stats)
    print(f"   현재 설정: 0.85")
    print(f"   권장 임계값: {optimal_threshold:.2f}")

    result["suggested_threshold"] = optimal_threshold

    # 8. 결과 저장
    if save_results:
        os.makedirs(RESULTS_DIR, exist_ok=True)
        filename = f"similarity_analysis_{category}_{date}.json"
        filepath = os.path.join(RESULTS_DIR, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n💾 결과 저장됨: {filepath}")

    return result


def suggest_optimal_threshold(stats: dict) -> float:
    """
    분포 통계를 기반으로 최적 임계값을 제안합니다.

    기준:
    - 상위 5-10%의 유사도 쌍만 동일 클러스터로 묶이도록
    - 너무 높으면 파편화, 너무 낮으면 체이닝

    Args:
        stats: 분포 통계 딕셔너리

    Returns:
        권장 임계값
    """
    # 90번째 백분위수 근처가 적절한 임계값
    # (상위 10%만 같은 클러스터로)
    p90 = stats["percentiles"]["90%"]
    p95 = stats["percentiles"]["95%"]

    # 90%와 95% 사이에서 선택
    suggested = (p90 + p95) / 2

    # 최소 0.4, 최대 0.8 범위로 제한
    suggested = max(0.40, min(0.80, suggested))

    return round(suggested, 2)


def run_all_categories_analysis(date: str) -> dict:
    """
    모든 카테고리에 대해 유사도 분석을 수행합니다.
    """
    all_results = {}

    for ko_name, category_info in CATEGORY_MAP.items():
        category = category_info["api_name"]
        print(f"\n{'#'*60}")
        print(f"# 카테고리: {ko_name} ({category})")
        print(f"{'#'*60}")

        result = run_similarity_analysis(category, date, save_results=True)
        all_results[category] = result

    # 종합 요약
    print("\n" + "="*60)
    print("📋 전체 카테고리 종합 요약")
    print("="*60)

    for category, result in all_results.items():
        if "error" not in result:
            print(f"\n{category}:")
            print(f"   기사 수: {result['article_count']}")
            print(f"   평균 유사도: {result['statistics']['mean']:.4f}")
            print(f"   권장 임계값: {result['suggested_threshold']:.2f}")

    # 전체 종합 결과 저장
    os.makedirs(RESULTS_DIR, exist_ok=True)
    summary_path = os.path.join(RESULTS_DIR, f"similarity_analysis_summary_{date}.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n💾 종합 결과 저장됨: {summary_path}")

    return all_results


def main():
    parser = argparse.ArgumentParser(
        description="text-embedding-3-small 유사도 분포 분석",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
    # 특정 카테고리 분석
    python similarity_analysis.py --category politics --date 2024-01-15

    # 모든 카테고리 분석
    python similarity_analysis.py --all-categories --date 2024-01-15

    # 오늘 날짜로 분석 (기본값)
    python similarity_analysis.py --category economy
        """
    )

    parser.add_argument(
        "--category",
        type=str,
        help="분석할 카테고리 (영문: politics, economy, society, culture, international, local, sports, tech)"
    )
    parser.add_argument(
        "--all-categories",
        action="store_true",
        help="모든 카테고리 분석"
    )
    parser.add_argument(
        "--date",
        type=str,
        default=datetime.now().strftime("%Y-%m-%d"),
        help="분석할 날짜 (YYYY-MM-DD, 기본값: 오늘)"
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="결과 파일 저장 안 함"
    )

    args = parser.parse_args()

    if args.all_categories:
        run_all_categories_analysis(args.date)
    elif args.category:
        run_similarity_analysis(args.category, args.date, save_results=not args.no_save)
    else:
        parser.print_help()
        print("\n❌ --category 또는 --all-categories 옵션이 필요합니다.")
        sys.exit(1)


if __name__ == "__main__":
    main()
