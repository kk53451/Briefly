# backend/test/scripts/visualize_clustering.py
"""
클러스터링 실험 결과 시각화 스크립트

생성되는 그래프:
1. 알고리즘별 Silhouette Score 비교 (threshold별)
2. 알고리즘별 G-Eval Coherence 비교
3. Threshold별 Compression Rate
4. Silhouette vs G-Eval 비교 (핵심 그래프)
5. 카테고리별 성능 히트맵

사용법:
    cd backend
    pip install matplotlib seaborn pandas
    python -m test.scripts.visualize_clustering
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pathlib import Path
from collections import defaultdict

# 한글 폰트 설정 (Windows)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 경로 설정
RESULTS_DIR = Path(__file__).parent.parent / "results"
CLUSTERING_FILE = RESULTS_DIR / "clustering_experiment_2025-11-30.json"
GEVAL_FILE = RESULTS_DIR / "geval_results_2025-11-30.json"
OUTPUT_DIR = RESULTS_DIR / "figures"


def load_data():
    """데이터 로드"""
    with open(CLUSTERING_FILE, "r", encoding="utf-8") as f:
        clustering_data = json.load(f)

    with open(GEVAL_FILE, "r", encoding="utf-8") as f:
        geval_data = json.load(f)

    return clustering_data, geval_data


def plot_silhouette_comparison(clustering_data):
    """1. 알고리즘별 Silhouette Score 비교"""
    fig, ax = plt.subplots(figsize=(10, 6))

    # 데이터 추출 (Union-Find, Greedy, HAC만)
    algorithms = ["union_find", "greedy", "hac"]
    thresholds = [0.5, 0.6, 0.7, 0.8]
    colors = {'union_find': '#2196F3', 'greedy': '#4CAF50', 'hac': '#FF9800'}
    labels = {'union_find': 'Union-Find', 'greedy': 'Greedy', 'hac': 'HAC'}

    # 알고리즘별 평균 Silhouette 계산
    algo_scores = defaultdict(lambda: defaultdict(list))

    for result in clustering_data["results"]:
        algo = result["algorithm"]
        if algo in algorithms and "threshold" in result.get("parameters", {}):
            threshold = result["parameters"]["threshold"]
            silhouette = result["silhouette"]
            if silhouette > -1:  # 유효한 값만
                algo_scores[algo][threshold].append(silhouette)

    # 평균 계산 및 플롯
    x = np.arange(len(thresholds))
    width = 0.25

    for i, algo in enumerate(algorithms):
        means = [np.mean(algo_scores[algo][t]) if algo_scores[algo][t] else 0
                 for t in thresholds]
        bars = ax.bar(x + i * width, means, width, label=labels[algo], color=colors[algo])

        # 값 표시
        for bar, val in zip(bars, means):
            ax.annotate(f'{val:.2f}',
                       xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                       ha='center', va='bottom', fontsize=9)

    ax.set_xlabel('Threshold', fontsize=12)
    ax.set_ylabel('Silhouette Score', fontsize=12)
    ax.set_title('알고리즘별 Silhouette Score 비교', fontsize=14, fontweight='bold')
    ax.set_xticks(x + width)
    ax.set_xticklabels(thresholds)
    ax.legend(loc='upper left')
    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax.set_ylim(-0.15, 0.35)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "1_silhouette_comparison.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("[OK] 1_silhouette_comparison.png saved")


def plot_geval_comparison(geval_data):
    """2. 알고리즘별 G-Eval Coherence 비교"""
    fig, ax = plt.subplots(figsize=(10, 6))

    # Union-Find threshold별 Coherence 추출
    uf_coherence = defaultdict(list)
    other_coherence = defaultdict(list)

    for result in geval_data["results"]:
        if "error" in result or not result.get("scores"):
            continue

        algo = result["config"]["algorithm"]
        coherence = result["scores"].get("coherence", {}).get("mean", 0)

        if algo == "union_find":
            threshold = result["config"]["threshold"]
            uf_coherence[threshold].append(coherence)
        else:
            other_coherence[algo].append(coherence)

    # Union-Find 막대 그래프
    thresholds = [0.5, 0.6, 0.7, 0.8]
    uf_means = [np.mean(uf_coherence[t]) if uf_coherence[t] else 0 for t in thresholds]

    x = np.arange(len(thresholds))
    bars = ax.bar(x, uf_means, 0.6, color='#2196F3', label='Union-Find')

    # 값 표시
    for bar, val in zip(bars, uf_means):
        ax.annotate(f'{val:.2f}',
                   xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                   ha='center', va='bottom', fontsize=11, fontweight='bold')

    # 최적값 강조
    max_idx = np.argmax(uf_means)
    bars[max_idx].set_color('#1565C0')
    bars[max_idx].set_edgecolor('gold')
    bars[max_idx].set_linewidth(3)

    ax.set_xlabel('Threshold', fontsize=12)
    ax.set_ylabel('G-Eval Coherence (1-5)', fontsize=12)
    ax.set_title('Union-Find Threshold별 G-Eval Coherence', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(thresholds)
    ax.set_ylim(0, 5.5)
    ax.axhline(y=4.65, color='red', linestyle='--', alpha=0.7, label='최적값 (t=0.7)')
    ax.legend()

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "2_geval_coherence.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("[OK] 2_geval_coherence.png saved")


def plot_compression_rate(clustering_data):
    """3. Threshold별 Compression Rate"""
    fig, ax = plt.subplots(figsize=(10, 6))

    algorithms = ["union_find", "greedy", "hac"]
    thresholds = [0.5, 0.6, 0.7, 0.8]
    colors = {'union_find': '#2196F3', 'greedy': '#4CAF50', 'hac': '#FF9800'}
    markers = {'union_find': 'o', 'greedy': 's', 'hac': '^'}
    labels = {'union_find': 'Union-Find', 'greedy': 'Greedy', 'hac': 'HAC'}

    algo_compression = defaultdict(lambda: defaultdict(list))

    for result in clustering_data["results"]:
        algo = result["algorithm"]
        if algo in algorithms and "threshold" in result.get("parameters", {}):
            threshold = result["parameters"]["threshold"]
            compression = result["compression_rate"]
            algo_compression[algo][threshold].append(compression)

    for algo in algorithms:
        means = [np.mean(algo_compression[algo][t]) * 100 if algo_compression[algo][t] else 0
                 for t in thresholds]
        ax.plot(thresholds, means, marker=markers[algo], markersize=10,
                linewidth=2, label=labels[algo], color=colors[algo])

    # 최적점 강조 (t=0.7)
    ax.axvline(x=0.7, color='red', linestyle='--', alpha=0.5, label='선택된 Threshold')

    ax.set_xlabel('Threshold', fontsize=12)
    ax.set_ylabel('Compression Rate (%)', fontsize=12)
    ax.set_title('Threshold별 압축률 비교', fontsize=14, fontweight='bold')
    ax.legend()
    ax.set_ylim(0, 100)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "3_compression_rate.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("[OK] 3_compression_rate.png saved")


def plot_silhouette_vs_geval(clustering_data, geval_data):
    """4. Silhouette vs G-Eval 비교 (핵심 그래프)"""
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Union-Find 데이터만 추출
    thresholds = [0.5, 0.6, 0.7, 0.8]

    # Silhouette 평균
    silhouette_scores = defaultdict(list)
    for result in clustering_data["results"]:
        if result["algorithm"] == "union_find" and "threshold" in result.get("parameters", {}):
            t = result["parameters"]["threshold"]
            if result["silhouette"] > -1:
                silhouette_scores[t].append(result["silhouette"])

    silhouette_means = [np.mean(silhouette_scores[t]) if silhouette_scores[t] else 0
                        for t in thresholds]

    # G-Eval Coherence 평균
    coherence_scores = defaultdict(list)
    for result in geval_data["results"]:
        if result.get("config", {}).get("algorithm") == "union_find":
            if "scores" in result and "coherence" in result["scores"]:
                t = result["config"]["threshold"]
                coherence_scores[t].append(result["scores"]["coherence"]["mean"])

    coherence_means = [np.mean(coherence_scores[t]) if coherence_scores[t] else 0
                       for t in thresholds]

    # 이중 축 그래프
    x = np.arange(len(thresholds))
    width = 0.35

    # Silhouette (왼쪽 축)
    bars1 = ax1.bar(x - width/2, silhouette_means, width, label='Silhouette Score',
                    color='#90CAF9', edgecolor='#1565C0', linewidth=2)
    ax1.set_xlabel('Threshold', fontsize=12)
    ax1.set_ylabel('Silhouette Score', fontsize=12, color='#1565C0')
    ax1.tick_params(axis='y', labelcolor='#1565C0')
    ax1.set_ylim(-0.1, 0.3)

    # G-Eval (오른쪽 축)
    ax2 = ax1.twinx()
    bars2 = ax2.bar(x + width/2, coherence_means, width, label='G-Eval Coherence',
                    color='#A5D6A7', edgecolor='#2E7D32', linewidth=2)
    ax2.set_ylabel('G-Eval Coherence (1-5)', fontsize=12, color='#2E7D32')
    ax2.tick_params(axis='y', labelcolor='#2E7D32')
    ax2.set_ylim(0, 5.5)

    # 값 표시
    for bar, val in zip(bars1, silhouette_means):
        ax1.annotate(f'{val:.2f}', xy=(bar.get_x() + bar.get_width() / 2, max(0, val)),
                    ha='center', va='bottom', fontsize=9, color='#1565C0')

    for bar, val in zip(bars2, coherence_means):
        ax2.annotate(f'{val:.2f}', xy=(bar.get_x() + bar.get_width() / 2, val),
                    ha='center', va='bottom', fontsize=9, color='#2E7D32', fontweight='bold')

    # 최적점 강조
    ax1.axvline(x=2, color='red', linestyle='--', alpha=0.7, linewidth=2)
    ax1.annotate('최적 (t=0.7)', xy=(2, 0.25), fontsize=11, color='red', fontweight='bold')

    ax1.set_xticks(x)
    ax1.set_xticklabels(thresholds)
    ax1.set_title('Silhouette vs G-Eval Coherence 비교 (Union-Find)',
                  fontsize=14, fontweight='bold')

    # 범례 통합
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "4_silhouette_vs_geval.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("[OK] 4_silhouette_vs_geval.png saved")


def plot_category_heatmap(clustering_data):
    """5. 카테고리별 Silhouette 히트맵"""
    fig, ax = plt.subplots(figsize=(12, 8))

    categories = ["politics", "economy", "society", "culture",
                  "international", "local", "sports", "tech"]
    thresholds = [0.5, 0.6, 0.7, 0.8]

    # Union-Find 결과만 추출
    data = np.zeros((len(categories), len(thresholds)))

    for result in clustering_data["results"]:
        if result["algorithm"] == "union_find" and "threshold" in result.get("parameters", {}):
            cat = result["category"]
            t = result["parameters"]["threshold"]
            if cat in categories and t in thresholds:
                cat_idx = categories.index(cat)
                t_idx = thresholds.index(t)
                data[cat_idx, t_idx] = result["silhouette"]

    # 히트맵
    im = ax.imshow(data, cmap='RdYlGn', aspect='auto', vmin=-0.15, vmax=0.35)

    # 축 설정
    ax.set_xticks(np.arange(len(thresholds)))
    ax.set_yticks(np.arange(len(categories)))
    ax.set_xticklabels(thresholds)
    ax.set_yticklabels(categories)
    ax.set_xlabel('Threshold', fontsize=12)
    ax.set_ylabel('Category', fontsize=12)
    ax.set_title('카테고리별 Silhouette Score (Union-Find)', fontsize=14, fontweight='bold')

    # 값 표시
    for i in range(len(categories)):
        for j in range(len(thresholds)):
            val = data[i, j]
            color = 'white' if abs(val) > 0.15 else 'black'
            ax.text(j, i, f'{val:.2f}', ha='center', va='center', color=color, fontsize=10)

    # 컬러바
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Silhouette Score', fontsize=11)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "5_category_heatmap.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("[OK] 5_category_heatmap.png saved")


def plot_algorithm_comparison_summary(clustering_data, geval_data):
    """6. 알고리즘 종합 비교 (발표용 핵심 그래프)"""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    algorithms = ["union_find", "greedy", "hac"]
    labels = {'union_find': 'Union-Find', 'greedy': 'Greedy', 'hac': 'HAC'}
    colors = {'union_find': '#2196F3', 'greedy': '#4CAF50', 'hac': '#FF9800'}

    # t=0.7 기준 데이터 추출
    silhouette_07 = {}
    compression_07 = {}

    for result in clustering_data["results"]:
        algo = result["algorithm"]
        if algo in algorithms:
            params = result.get("parameters", {})
            if params.get("threshold") == 0.7:
                if algo not in silhouette_07:
                    silhouette_07[algo] = []
                    compression_07[algo] = []
                if result["silhouette"] > -1:
                    silhouette_07[algo].append(result["silhouette"])
                compression_07[algo].append(result["compression_rate"])

    # G-Eval (t=0.6 또는 0.7)
    geval_scores = {}
    for result in geval_data["results"]:
        if "error" in result:
            continue
        algo = result["config"]["algorithm"]
        if algo in algorithms:
            coherence = result["scores"].get("coherence", {}).get("mean", 0)
            if algo not in geval_scores:
                geval_scores[algo] = []
            geval_scores[algo].append(coherence)

    # 그래프 1: Silhouette
    ax1 = axes[0]
    means = [np.mean(silhouette_07.get(a, [0])) for a in algorithms]
    bars = ax1.bar([labels[a] for a in algorithms], means,
                   color=[colors[a] for a in algorithms])
    ax1.set_ylabel('Silhouette Score')
    ax1.set_title('Silhouette Score\n(t=0.7)', fontweight='bold')
    ax1.set_ylim(-0.05, 0.3)
    for bar, val in zip(bars, means):
        ax1.annotate(f'{val:.2f}', xy=(bar.get_x() + bar.get_width() / 2, max(0, val)),
                    ha='center', va='bottom', fontsize=11)

    # 그래프 2: G-Eval Coherence
    ax2 = axes[1]
    # Union-Find t=0.7, 나머지는 t=0.6
    uf_07 = [r["scores"]["coherence"]["mean"] for r in geval_data["results"]
             if r.get("config", {}).get("algorithm") == "union_find"
             and r.get("config", {}).get("threshold") == 0.7
             and "scores" in r and "coherence" in r["scores"]]

    geval_means = {
        "union_find": np.mean(uf_07) if uf_07 else 0,
        "greedy": np.mean(geval_scores.get("greedy", [0])),
        "hac": np.mean(geval_scores.get("hac", [0]))
    }

    means2 = [geval_means[a] for a in algorithms]
    bars2 = ax2.bar([labels[a] for a in algorithms], means2,
                    color=[colors[a] for a in algorithms])
    ax2.set_ylabel('G-Eval Coherence (1-5)')
    ax2.set_title('G-Eval Coherence\n(의미적 품질)', fontweight='bold')
    ax2.set_ylim(0, 5.5)
    bars2[0].set_edgecolor('gold')
    bars2[0].set_linewidth(3)
    for bar, val in zip(bars2, means2):
        ax2.annotate(f'{val:.2f}', xy=(bar.get_x() + bar.get_width() / 2, val),
                    ha='center', va='bottom', fontsize=11, fontweight='bold')

    # 그래프 3: Compression Rate
    ax3 = axes[2]
    means3 = [np.mean(compression_07.get(a, [0])) * 100 for a in algorithms]
    bars3 = ax3.bar([labels[a] for a in algorithms], means3,
                    color=[colors[a] for a in algorithms])
    ax3.set_ylabel('Compression Rate (%)')
    ax3.set_title('압축률\n(t=0.7)', fontweight='bold')
    ax3.set_ylim(0, 80)
    for bar, val in zip(bars3, means3):
        ax3.annotate(f'{val:.1f}%', xy=(bar.get_x() + bar.get_width() / 2, val),
                    ha='center', va='bottom', fontsize=11)

    plt.suptitle('알고리즘 종합 비교 (Threshold = 0.7 기준)', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "6_algorithm_summary.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("[OK] 6_algorithm_summary.png saved")


def plot_geval_by_category(geval_data):
    """7. 카테고리별 G-Eval Coherence (Union-Find t=0.7)"""
    fig, ax = plt.subplots(figsize=(10, 6))

    categories = ["politics", "economy", "society", "tech"]
    category_labels = {"politics": "정치", "economy": "경제", "society": "사회", "tech": "IT/과학"}

    coherence_by_cat = {}
    for result in geval_data["results"]:
        if result.get("config", {}).get("algorithm") == "union_find" \
           and result.get("config", {}).get("threshold") == 0.7:
            if "scores" in result and "coherence" in result["scores"]:
                cat = result["category"]
                coherence_by_cat[cat] = result["scores"]["coherence"]["mean"]

    cats = [c for c in categories if c in coherence_by_cat]
    values = [coherence_by_cat[c] for c in cats]
    labels_kr = [category_labels[c] for c in cats]

    colors = ['#1565C0' if v >= 4.6 else '#42A5F5' if v >= 4.0 else '#90CAF9' for v in values]

    bars = ax.bar(labels_kr, values, color=colors, edgecolor='#0D47A1', linewidth=2)

    # 값 표시
    for bar, val in zip(bars, values):
        ax.annotate(f'{val:.1f}', xy=(bar.get_x() + bar.get_width() / 2, val),
                   ha='center', va='bottom', fontsize=14, fontweight='bold')

    ax.set_ylabel('G-Eval Coherence (1-5)', fontsize=12)
    ax.set_title('카테고리별 G-Eval Coherence (Union-Find, t=0.7)', fontsize=14, fontweight='bold')
    ax.set_ylim(0, 5.5)
    ax.axhline(y=5.0, color='gold', linestyle='--', alpha=0.7, label='만점 (5.0)')
    ax.axhline(y=4.65, color='red', linestyle='--', alpha=0.7, label='평균 (4.65)')
    ax.legend()

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "7_geval_by_category.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("[OK] 7_geval_by_category.png saved")


def main():
    print("=" * 60)
    print("클러스터링 실험 결과 시각화")
    print("=" * 60)

    # 출력 디렉토리 생성
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 데이터 로드
    print("\n데이터 로드 중...")
    clustering_data, geval_data = load_data()
    print(f"  - 클러스터링 결과: {len(clustering_data['results'])}개")
    print(f"  - G-Eval 결과: {len(geval_data['results'])}개")

    # 그래프 생성
    print("\n그래프 생성 중...")
    plot_silhouette_comparison(clustering_data)
    plot_geval_comparison(geval_data)
    plot_compression_rate(clustering_data)
    plot_silhouette_vs_geval(clustering_data, geval_data)
    plot_category_heatmap(clustering_data)
    plot_algorithm_comparison_summary(clustering_data, geval_data)
    plot_geval_by_category(geval_data)

    print("\n" + "=" * 60)
    print(f"완료! 그래프 저장 위치: {OUTPUT_DIR}")
    print("=" * 60)
    print("\n생성된 파일:")
    print("  1. 1_silhouette_comparison.png - 알고리즘별 Silhouette 비교")
    print("  2. 2_geval_coherence.png - Union-Find Threshold별 G-Eval")
    print("  3. 3_compression_rate.png - Threshold별 압축률")
    print("  4. 4_silhouette_vs_geval.png - Silhouette vs G-Eval (핵심)")
    print("  5. 5_category_heatmap.png - 카테고리별 Silhouette 히트맵")
    print("  6. 6_algorithm_summary.png - 알고리즘 종합 비교 (발표용)")
    print("  7. 7_geval_by_category.png - 카테고리별 G-Eval")


if __name__ == "__main__":
    main()
