# backend/test/scripts/run_geval.py

"""
G-Eval 평가 스크립트

목적: GPT-4o를 사용하여 클러스터링 품질을 LLM 기반으로 평가

평가 항목:
1. 클러스터 품질: Coherence, Separation, Representative
2. 요약 품질: Relevance, Consistency, Fluency, Coverage
3. 대본 품질: Information Density, Narrative Flow, Completeness

사용법:
    cd backend
    python -m test.scripts.run_geval
"""

import os
import sys
import json
import time
import random
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI

# ============================================================
# 설정
# ============================================================

DATA_DIR = Path(__file__).parent.parent / "data"
RESULTS_DIR = Path(__file__).parent.parent / "results"
EMBEDDINGS_FILE = DATA_DIR / "embeddings_2025-11-30.npz"
RAW_DATA_FILE = DATA_DIR / "news_raw_2025-11-30.jsonl"
EXPERIMENT_FILE = RESULTS_DIR / "clustering_experiment_2025-11-30.json"
OUTPUT_FILE = RESULTS_DIR / "geval_results_2025-11-30.json"

# GPT-4o 설정
EVAL_MODEL = "gpt-4o"
MAX_ARTICLES_PER_CLUSTER = 5  # 클러스터당 최대 평가 기사 수
CONTENT_PREVIEW_LENGTH = 500  # 평가용 본문 미리보기 길이

# 평가할 알고리즘/파라미터 조합 (상위 결과만 선택)
EVAL_CONFIGS = [
    {"algorithm": "union_find", "threshold": 0.5},
    {"algorithm": "union_find", "threshold": 0.6},
    {"algorithm": "union_find", "threshold": 0.7},
    {"algorithm": "union_find", "threshold": 0.8},
    {"algorithm": "greedy", "threshold": 0.6},
    {"algorithm": "hac", "threshold": 0.6},
    {"algorithm": "dbscan", "eps": 0.4, "min_samples": 2},
]

# 샘플링 설정
CLUSTERS_PER_CONFIG = 5  # 설정당 평가할 클러스터 수
CATEGORIES_TO_EVAL = ["politics", "economy", "society", "tech"]  # 평가할 카테고리

# OpenAI 클라이언트
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ============================================================
# G-Eval 프롬프트
# ============================================================

COHERENCE_PROMPT = """You are evaluating the coherence of a news article cluster.

[Task]: Rate how well the articles in this cluster belong to the SAME topic/event.

[Cluster Articles]:
{articles}

[Evaluation Criteria]:
1 = Very Poor: Articles are completely unrelated, covering entirely different topics
2 = Poor: Articles have only superficial connections, mostly different topics
3 = Fair: Articles share a general theme but cover different specific events
4 = Good: Articles cover related events within the same topic area
5 = Excellent: Articles all cover the exact same news event/story

[Output]: Return ONLY a single number (1-5)."""

SEPARATION_PROMPT = """You are evaluating how well a cluster is separated from another cluster.

[Task]: Rate how distinct these two clusters are from each other.

[Cluster A Articles]:
{cluster_a}

[Cluster B Articles]:
{cluster_b}

[Evaluation Criteria]:
1 = Very Poor: The two clusters cover the exact same topic and should be merged
2 = Poor: Clusters have significant overlap in topic coverage
3 = Fair: Clusters have some thematic overlap but different focuses
4 = Good: Clusters cover clearly different topics with minimal overlap
5 = Excellent: Clusters are completely distinct with no topical relationship

[Output]: Return ONLY a single number (1-5)."""

REPRESENTATIVE_PROMPT = """You are evaluating how well a representative article represents its cluster.

[Task]: Rate how well the representative article captures the main theme of the cluster.

[Representative Article]:
Title: {rep_title}
Content: {rep_content}

[Other Cluster Articles]:
{other_articles}

[Evaluation Criteria]:
1 = Very Poor: Representative is completely unrelated to other articles
2 = Poor: Representative covers a minor aspect not central to the cluster
3 = Fair: Representative captures some but not all key themes
4 = Good: Representative captures the main theme well
5 = Excellent: Representative perfectly captures the central theme of all articles

[Output]: Return ONLY a single number (1-5)."""

SUMMARY_RELEVANCE_PROMPT = """You are evaluating the relevance of a news summary.

[Task]: Rate how well the summary reflects the content of the original articles.

[Summary]:
{summary}

[Original Articles]:
{articles}

[Evaluation Criteria]:
1 = Very Poor: Summary contains information not in the original articles
2 = Poor: Summary misrepresents or distorts the original content
3 = Fair: Summary captures some points but misses or misrepresents others
4 = Good: Summary accurately reflects most of the original content
5 = Excellent: Summary perfectly captures all key points from the original articles

[Output]: Return ONLY a single number (1-5)."""

SUMMARY_CONSISTENCY_PROMPT = """You are evaluating the factual consistency of a news summary.

[Task]: Rate if the summary contains any factual errors or contradictions.

[Summary]:
{summary}

[Original Articles]:
{articles}

[Evaluation Criteria]:
1 = Very Poor: Summary contains multiple factual errors
2 = Poor: Summary has significant factual inaccuracies
3 = Fair: Summary has minor factual inconsistencies
4 = Good: Summary is mostly factually accurate with trivial issues
5 = Excellent: Summary is completely factually consistent with sources

[Output]: Return ONLY a single number (1-5)."""

SUMMARY_FLUENCY_PROMPT = """You are evaluating the fluency of a Korean news summary.

[Task]: Rate how natural and readable the summary is.

[Summary]:
{summary}

[Evaluation Criteria]:
1 = Very Poor: Text is incomprehensible or severely broken
2 = Poor: Text has major grammatical issues affecting readability
3 = Fair: Text is understandable but awkward in places
4 = Good: Text reads naturally with minor issues
5 = Excellent: Text is perfectly natural, fluent Korean

[Output]: Return ONLY a single number (1-5)."""

SUMMARY_COVERAGE_PROMPT = """You are evaluating the coverage of a news summary.

[Task]: Rate how comprehensively the summary covers the key information.

[Summary]:
{summary}

[Original Articles]:
{articles}

[Evaluation Criteria]:
1 = Very Poor: Summary misses almost all key information
2 = Poor: Summary covers only a small fraction of important points
3 = Fair: Summary covers about half of the key information
4 = Good: Summary covers most key information with minor omissions
5 = Excellent: Summary comprehensively covers all important information

[Output]: Return ONLY a single number (1-5)."""


# ============================================================
# 클러스터링 함수 (실험 스크립트에서 복사)
# ============================================================

def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(vec1, vec2) / (norm1 * norm2))


def cluster_union_find(embeddings: np.ndarray, threshold: float) -> List[int]:
    n = len(embeddings)
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

    for i in range(n):
        for j in range(i + 1, n):
            sim = cosine_similarity(embeddings[i], embeddings[j])
            if sim > threshold:
                union(i, j)

    labels = [find(i) for i in range(n)]
    unique_labels = list(set(labels))
    label_map = {old: new for new, old in enumerate(unique_labels)}
    return [label_map[l] for l in labels]


def cluster_greedy(embeddings: np.ndarray, threshold: float) -> List[int]:
    n = len(embeddings)
    labels = [-1] * n
    current_cluster = 0

    for i in range(n):
        if labels[i] != -1:
            continue
        labels[i] = current_cluster
        for j in range(i + 1, n):
            if labels[j] != -1:
                continue
            sim = cosine_similarity(embeddings[i], embeddings[j])
            if sim > threshold:
                labels[j] = current_cluster
        current_cluster += 1

    return labels


def cluster_hac(embeddings: np.ndarray, threshold: float) -> List[int]:
    from scipy.cluster.hierarchy import linkage, fcluster
    from scipy.spatial.distance import squareform

    if len(embeddings) < 2:
        return [0] * len(embeddings)

    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normalized = embeddings / np.maximum(norms, 1e-10)
    similarity_matrix = np.dot(normalized, normalized.T)

    # 부동소수점 오차로 인해 1을 초과할 수 있으므로 클리핑
    similarity_matrix = np.clip(similarity_matrix, -1.0, 1.0)

    distance_matrix = 1 - similarity_matrix

    # 부동소수점 오차로 인한 음수 방지
    distance_matrix = np.maximum(distance_matrix, 0)

    np.fill_diagonal(distance_matrix, 0)

    condensed = squareform(distance_matrix, checks=False)
    Z = linkage(condensed, method='average')
    distance_threshold = 1 - threshold
    labels = fcluster(Z, t=distance_threshold, criterion='distance')

    return [l - 1 for l in labels]


def cluster_dbscan(embeddings: np.ndarray, eps: float, min_samples: int) -> List[int]:
    from sklearn.cluster import DBSCAN

    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normalized = embeddings / np.maximum(norms, 1e-10)
    similarity_matrix = np.dot(normalized, normalized.T)

    # 부동소수점 오차로 인해 1을 초과할 수 있으므로 클리핑
    similarity_matrix = np.clip(similarity_matrix, -1.0, 1.0)

    distance_matrix = 1 - similarity_matrix

    # 부동소수점 오차로 인한 음수 방지
    distance_matrix = np.maximum(distance_matrix, 0)

    np.fill_diagonal(distance_matrix, 0)

    clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='precomputed')
    labels = clustering.fit_predict(distance_matrix)

    return labels.tolist()


# ============================================================
# G-Eval 함수
# ============================================================

def call_gpt4o(prompt: str, max_retries: int = 3) -> int:
    """GPT-4o 호출하여 점수 반환"""
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=EVAL_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=10
            )
            result = response.choices[0].message.content.strip()

            # 숫자만 추출
            score = int(''.join(filter(str.isdigit, result)))
            if 1 <= score <= 5:
                return score
            return 3  # 기본값

        except Exception as e:
            print(f"   GPT-4o call failed (attempt {attempt + 1}): {e}", flush=True)
            time.sleep(1)

    return 3  # 실패 시 기본값


def format_articles(articles: List[Dict], max_count: int = 5) -> str:
    """기사 목록을 평가용 문자열로 포맷"""
    lines = []
    for i, article in enumerate(articles[:max_count], 1):
        title = article.get("title", "")
        content = article.get("content", "")[:CONTENT_PREVIEW_LENGTH]
        lines.append(f"{i}. [{title}]\n   {content}...")
    return "\n\n".join(lines)


def evaluate_coherence(cluster_articles: List[Dict]) -> int:
    """클러스터 일관성 평가"""
    if len(cluster_articles) < 2:
        return 5  # 단일 기사 클러스터는 완벽한 일관성

    prompt = COHERENCE_PROMPT.format(
        articles=format_articles(cluster_articles)
    )
    return call_gpt4o(prompt)


def evaluate_separation(cluster_a: List[Dict], cluster_b: List[Dict]) -> int:
    """클러스터 분리도 평가"""
    prompt = SEPARATION_PROMPT.format(
        cluster_a=format_articles(cluster_a, max_count=3),
        cluster_b=format_articles(cluster_b, max_count=3)
    )
    return call_gpt4o(prompt)


def evaluate_representative(rep_article: Dict, other_articles: List[Dict]) -> int:
    """대표 기사 대표성 평가"""
    if len(other_articles) == 0:
        return 5  # 단일 기사는 완벽한 대표성

    prompt = REPRESENTATIVE_PROMPT.format(
        rep_title=rep_article.get("title", ""),
        rep_content=rep_article.get("content", "")[:CONTENT_PREVIEW_LENGTH],
        other_articles=format_articles(other_articles, max_count=4)
    )
    return call_gpt4o(prompt)


def evaluate_summary(summary: str, original_articles: List[Dict]) -> Dict[str, int]:
    """요약 품질 평가 (4개 메트릭)"""
    articles_text = format_articles(original_articles)

    relevance = call_gpt4o(SUMMARY_RELEVANCE_PROMPT.format(
        summary=summary, articles=articles_text
    ))

    consistency = call_gpt4o(SUMMARY_CONSISTENCY_PROMPT.format(
        summary=summary, articles=articles_text
    ))

    fluency = call_gpt4o(SUMMARY_FLUENCY_PROMPT.format(
        summary=summary
    ))

    coverage = call_gpt4o(SUMMARY_COVERAGE_PROMPT.format(
        summary=summary, articles=articles_text
    ))

    return {
        "relevance": relevance,
        "consistency": consistency,
        "fluency": fluency,
        "coverage": coverage
    }


# ============================================================
# 요약 생성 (openai_service 간소화 버전)
# ============================================================

def generate_cluster_summary(articles: List[Dict], category: str) -> str:
    """클러스터 기사들을 요약"""
    articles_text = "\n\n".join([
        f"제목: {a.get('title', '')}\n내용: {a.get('content', '')[:800]}"
        for a in articles[:5]
    ])

    prompt = f"""다음은 '{category}' 카테고리의 관련 뉴스 기사들입니다.
이 기사들의 핵심 내용을 500-700자로 통합 요약해주세요.

기사들:
{articles_text}

통합 요약:"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"   Summary generation failed: {e}", flush=True)
        return ""


# ============================================================
# 메인 평가 로직
# ============================================================

def run_evaluation(
    embeddings: np.ndarray,
    articles: List[Dict],
    article_id_to_idx: Dict[str, int],
    category: str,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """단일 설정에 대한 G-Eval 평가 실행"""
    algorithm = config["algorithm"]

    # 클러스터링 수행
    if algorithm == "union_find":
        labels = cluster_union_find(embeddings, config["threshold"])
    elif algorithm == "greedy":
        labels = cluster_greedy(embeddings, config["threshold"])
    elif algorithm == "hac":
        labels = cluster_hac(embeddings, config["threshold"])
    elif algorithm == "dbscan":
        labels = cluster_dbscan(embeddings, config["eps"], config["min_samples"])
    else:
        return {}

    # 클러스터별 기사 그룹화
    clusters = defaultdict(list)
    for idx, label in enumerate(labels):
        if label != -1:  # DBSCAN 노이즈 제외
            clusters[label].append(idx)

    # 평가할 클러스터 샘플링 (크기 2 이상인 클러스터만)
    valid_clusters = [
        (label, indices) for label, indices in clusters.items()
        if len(indices) >= 2
    ]

    if len(valid_clusters) < 2:
        return {
            "config": config,
            "category": category,
            "cluster_count": len(clusters),
            "valid_cluster_count": len(valid_clusters),
            "scores": {},
            "error": "Not enough valid clusters"
        }

    # 랜덤 샘플링
    sample_clusters = random.sample(
        valid_clusters,
        min(CLUSTERS_PER_CONFIG, len(valid_clusters))
    )

    # 평가 수행
    coherence_scores = []
    separation_scores = []
    representative_scores = []
    summary_scores = []

    for i, (label, indices) in enumerate(sample_clusters):
        cluster_articles = [articles[idx] for idx in indices]

        # 1. Coherence
        coherence = evaluate_coherence(cluster_articles)
        coherence_scores.append(coherence)

        # 2. Representative (첫 번째 기사를 대표로)
        rep_article = cluster_articles[0]
        other_articles = cluster_articles[1:]
        representative = evaluate_representative(rep_article, other_articles)
        representative_scores.append(representative)

        # 3. Summary 평가 (요약 생성 후)
        summary = generate_cluster_summary(cluster_articles, category)
        if summary:
            summary_eval = evaluate_summary(summary, cluster_articles)
            summary_scores.append(summary_eval)

        print(f"      Cluster {i+1}/{len(sample_clusters)}: "
              f"coherence={coherence}, representative={representative}", flush=True)

    # 4. Separation (랜덤 클러스터 쌍)
    if len(sample_clusters) >= 2:
        for _ in range(min(3, len(sample_clusters) - 1)):
            pair = random.sample(sample_clusters, 2)
            cluster_a_articles = [articles[idx] for idx in pair[0][1]]
            cluster_b_articles = [articles[idx] for idx in pair[1][1]]
            separation = evaluate_separation(cluster_a_articles, cluster_b_articles)
            separation_scores.append(separation)

    # 결과 집계
    result = {
        "config": config,
        "category": category,
        "cluster_count": len(clusters),
        "valid_cluster_count": len(valid_clusters),
        "evaluated_clusters": len(sample_clusters),
        "scores": {
            "coherence": {
                "mean": round(np.mean(coherence_scores), 2) if coherence_scores else 0,
                "std": round(np.std(coherence_scores), 2) if coherence_scores else 0,
                "values": coherence_scores
            },
            "separation": {
                "mean": round(np.mean(separation_scores), 2) if separation_scores else 0,
                "std": round(np.std(separation_scores), 2) if separation_scores else 0,
                "values": separation_scores
            },
            "representative": {
                "mean": round(np.mean(representative_scores), 2) if representative_scores else 0,
                "std": round(np.std(representative_scores), 2) if representative_scores else 0,
                "values": representative_scores
            }
        }
    }

    # 요약 점수 집계
    if summary_scores:
        for metric in ["relevance", "consistency", "fluency", "coverage"]:
            values = [s[metric] for s in summary_scores]
            result["scores"][f"summary_{metric}"] = {
                "mean": round(np.mean(values), 2),
                "std": round(np.std(values), 2),
                "values": values
            }

    return result


# ============================================================
# 메인 실행
# ============================================================

def main():
    total_start = time.time()

    print("=" * 60, flush=True)
    print("G-Eval Evaluation", flush=True)
    print("=" * 60, flush=True)
    print(f"Model: {EVAL_MODEL}", flush=True)
    print(f"Categories: {CATEGORIES_TO_EVAL}", flush=True)
    print(f"Configs to evaluate: {len(EVAL_CONFIGS)}", flush=True)
    print("=" * 60, flush=True)

    # 1. 데이터 로드
    print("\n[1/4] Loading data...", flush=True)

    # 임베딩
    data = np.load(EMBEDDINGS_FILE, allow_pickle=True)
    embeddings = data["embeddings"]
    article_ids = data["article_ids"]
    categories = data["categories"]

    print(f"   Embeddings: {len(embeddings)}", flush=True)

    # 원본 기사
    articles_dict = {}
    with open(RAW_DATA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                article = json.loads(line)
                articles_dict[article["id"]] = article

    print(f"   Articles: {len(articles_dict)}", flush=True)

    # 2. 카테고리별 데이터 구성
    print("\n[2/4] Organizing by category...", flush=True)

    category_data = defaultdict(lambda: {
        "embeddings": [],
        "article_ids": [],
        "articles": []
    })

    for i, (aid, cat) in enumerate(zip(article_ids, categories)):
        if cat in CATEGORIES_TO_EVAL and aid in articles_dict:
            category_data[cat]["embeddings"].append(embeddings[i])
            category_data[cat]["article_ids"].append(aid)
            category_data[cat]["articles"].append(articles_dict[aid])

    for cat in category_data:
        category_data[cat]["embeddings"] = np.array(category_data[cat]["embeddings"])
        print(f"   {cat}: {len(category_data[cat]['articles'])} articles", flush=True)

    # 3. 평가 실행
    print("\n[3/4] Running G-Eval...", flush=True)

    all_results = []

    for cat in CATEGORIES_TO_EVAL:
        if cat not in category_data:
            continue

        cat_data = category_data[cat]

        for config in EVAL_CONFIGS:
            print(f"\n   [{cat}] {config}", flush=True)

            result = run_evaluation(
                embeddings=cat_data["embeddings"],
                articles=cat_data["articles"],
                article_id_to_idx={aid: i for i, aid in enumerate(cat_data["article_ids"])},
                category=cat,
                config=config
            )

            all_results.append(result)

    # 4. 결과 저장
    print("\n[4/4] Saving results...", flush=True)

    output = {
        "evaluation_date": "2025-11-30",
        "model": EVAL_MODEL,
        "categories": CATEGORIES_TO_EVAL,
        "configs": EVAL_CONFIGS,
        "results": all_results
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    total_time = time.time() - total_start

    print("\n" + "=" * 60, flush=True)
    print("G-Eval Complete!", flush=True)
    print("=" * 60, flush=True)
    print(f"Total evaluations: {len(all_results)}", flush=True)
    print(f"Total time: {total_time:.1f}s ({total_time/60:.1f} min)", flush=True)
    print(f"Output: {OUTPUT_FILE}", flush=True)
    print("=" * 60, flush=True)

    # 요약 통계
    print("\nAverage Scores by Algorithm:", flush=True)
    print("-" * 60, flush=True)

    algo_scores = defaultdict(lambda: defaultdict(list))
    for result in all_results:
        if "error" in result:
            continue
        algo = result["config"]["algorithm"]
        for metric, data in result["scores"].items():
            if "mean" in data:
                algo_scores[algo][metric].append(data["mean"])

    for algo in ["union_find", "greedy", "hac", "dbscan"]:
        if algo in algo_scores:
            print(f"\n  {algo}:", flush=True)
            for metric, values in sorted(algo_scores[algo].items()):
                mean = np.mean(values)
                print(f"    {metric:20s}: {mean:.2f}", flush=True)


if __name__ == "__main__":
    main()
