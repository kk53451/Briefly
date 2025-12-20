"""
클러스터링 실험 결과 시각화
"""
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 경로 설정
BASE_DIR = Path(__file__).parent.parent
RESULTS_DIR = BASE_DIR / "results"

# 데이터 로드
with open(RESULTS_DIR / "clustering_experiment_2025-11-30.json", 'r', encoding='utf-8') as f:
    clustering_data = json.load(f)

with open(RESULTS_DIR / "geval_results_2025-11-30.json", 'r', encoding='utf-8') as f:
    geval_data = json.load(f)

# Figure 설정 (2x2 레이아웃)
fig, axes = plt.subplots(2, 2, figsize=(14, 12))
fig.suptitle('Briefly 뉴스 클러스터링 실험 결과', fontsize=16, fontweight='bold')

# ============================================
# 1. G-Eval Coherence by Algorithm & Threshold
# ============================================
ax1 = axes[0, 0]

# Union-Find threshold별 coherence 추출
uf_coherence = {0.5: [], 0.6: [], 0.7: [], 0.8: []}
for r in geval_data['results']:
    if r['config']['algorithm'] == 'union_find' and 'scores' in r and r['scores']:
        t = r['config']['threshold']
        if 'coherence' in r['scores']:
            uf_coherence[t].append(r['scores']['coherence']['mean'])

# 평균 계산
thresholds = [0.5, 0.6, 0.7, 0.8]
uf_means = [np.mean(uf_coherence[t]) if uf_coherence[t] else 0 for t in thresholds]

# 다른 알고리즘 coherence
algo_coherence = {'greedy': [], 'hac': [], 'dbscan': []}
for r in geval_data['results']:
    algo = r['config']['algorithm']
    if algo in algo_coherence and 'scores' in r and r['scores']:
        if 'coherence' in r['scores']:
            algo_coherence[algo].append(r['scores']['coherence']['mean'])

other_means = {k: np.mean(v) if v else 0 for k, v in algo_coherence.items()}

# 바 차트
x = np.arange(len(thresholds))
width = 0.6
colors = ['#ff9999', '#ffcc99', '#99ff99', '#99ccff']
bars = ax1.bar(x, uf_means, width, color=colors, edgecolor='black')
ax1.axhline(y=other_means['greedy'], color='orange', linestyle='--', linewidth=2, label=f"Greedy (avg: {other_means['greedy']:.2f})")
ax1.axhline(y=other_means['hac'], color='purple', linestyle='--', linewidth=2, label=f"HAC (avg: {other_means['hac']:.2f})")
ax1.axhline(y=other_means['dbscan'], color='red', linestyle='--', linewidth=2, label=f"DBSCAN (avg: {other_means['dbscan']:.2f})")

ax1.set_xlabel('Union-Find Threshold', fontsize=11)
ax1.set_ylabel('G-Eval Coherence (1-5)', fontsize=11)
ax1.set_title('① G-Eval Coherence: Union-Find vs 다른 알고리즘', fontsize=12, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels([f't={t}' for t in thresholds])
ax1.set_ylim(0, 5.5)
ax1.legend(loc='lower right')

# 값 표시
for bar, val in zip(bars, uf_means):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, f'{val:.2f}',
             ha='center', va='bottom', fontweight='bold', fontsize=11)

# 최고값 강조
max_idx = np.argmax(uf_means)
bars[max_idx].set_edgecolor('green')
bars[max_idx].set_linewidth(3)

# ============================================
# 2. 가장 큰 클러스터 비율 비교
# ============================================
ax2 = axes[0, 1]

categories = ['politics', 'economy', 'society', 'tech']
uf_biggest = []
dbscan_03_biggest = []
dbscan_04_biggest = []

for cat in categories:
    for r in clustering_data['results']:
        if r['category'] != cat:
            continue
        algo = r['algorithm']
        params = r['parameters']

        if algo == 'union_find' and params.get('threshold') == 0.7:
            ratio = r['cluster_sizes'][0] / r['input_count'] * 100
            uf_biggest.append(ratio)
        if algo == 'dbscan' and params.get('eps') == 0.3 and params.get('min_samples') == 2:
            ratio = r['cluster_sizes'][0] / r['input_count'] * 100
            dbscan_03_biggest.append(ratio)
        if algo == 'dbscan' and params.get('eps') == 0.4 and params.get('min_samples') == 2:
            ratio = r['cluster_sizes'][0] / r['input_count'] * 100
            dbscan_04_biggest.append(ratio)

x = np.arange(len(categories))
width = 0.25

bars1 = ax2.bar(x - width, uf_biggest, width, label='Union-Find (t=0.7)', color='#4CAF50', edgecolor='black')
bars2 = ax2.bar(x, dbscan_03_biggest, width, label='DBSCAN (eps=0.3)', color='#2196F3', edgecolor='black')
bars3 = ax2.bar(x + width, dbscan_04_biggest, width, label='DBSCAN (eps=0.4)', color='#F44336', edgecolor='black')

ax2.set_xlabel('카테고리', fontsize=11)
ax2.set_ylabel('가장 큰 클러스터 비율 (%)', fontsize=11)
ax2.set_title('② 거대 클러스터 문제: 알고리즘별 비교', fontsize=12, fontweight='bold')
ax2.set_xticks(x)
ax2.set_xticklabels(categories)
ax2.legend(loc='upper right')
ax2.set_ylim(0, 100)
ax2.axhline(y=50, color='gray', linestyle=':', linewidth=1, alpha=0.7)

# ============================================
# 3. Silhouette Score 히트맵
# ============================================
ax3 = axes[1, 0]

# 알고리즘별, threshold별 평균 silhouette 계산
algos = ['union_find', 'greedy', 'hac']
algo_labels = ['Union-Find', 'Greedy', 'HAC']
thresholds = [0.5, 0.6, 0.7, 0.8]

silhouette_matrix = np.zeros((len(algos), len(thresholds)))

for i, algo in enumerate(algos):
    for j, t in enumerate(thresholds):
        values = []
        for r in clustering_data['results']:
            if r['algorithm'] == algo and r['parameters'].get('threshold') == t:
                if r['silhouette'] != -1.0:
                    values.append(r['silhouette'])
        if values:
            silhouette_matrix[i, j] = np.mean(values)

im = ax3.imshow(silhouette_matrix, cmap='RdYlGn', aspect='auto', vmin=-0.1, vmax=0.35)
ax3.set_xticks(np.arange(len(thresholds)))
ax3.set_yticks(np.arange(len(algos)))
ax3.set_xticklabels([f't={t}' for t in thresholds])
ax3.set_yticklabels(algo_labels)
ax3.set_xlabel('Threshold', fontsize=11)
ax3.set_title('③ Silhouette Score 히트맵 (높을수록 좋음)', fontsize=12, fontweight='bold')

# 값 표시
for i in range(len(algos)):
    for j in range(len(thresholds)):
        val = silhouette_matrix[i, j]
        color = 'white' if val > 0.15 or val < 0 else 'black'
        ax3.text(j, i, f'{val:.3f}', ha='center', va='center', color=color, fontweight='bold')

# 컬러바
cbar = plt.colorbar(im, ax=ax3)
cbar.set_label('Silhouette Score')

# ============================================
# 4. DBSCAN 노이즈 비율 vs eps
# ============================================
ax4 = axes[1, 1]

noise_data = {'0.3': [], '0.4': [], '0.5': []}
cluster_data = {'0.3': [], '0.4': [], '0.5': []}

for r in clustering_data['results']:
    if r['algorithm'] != 'dbscan':
        continue
    params = r['parameters']
    if params.get('min_samples') != 2:
        continue
    eps = params.get('eps')
    noise_ratio = r['noise_count'] / r['input_count'] * 100
    biggest_ratio = r['cluster_sizes'][0] / r['input_count'] * 100 if r['cluster_sizes'] else 0

    key = str(eps)
    if key in noise_data:
        noise_data[key].append(noise_ratio)
        cluster_data[key].append(biggest_ratio)

eps_labels = ['eps=0.3', 'eps=0.4', 'eps=0.5']
noise_means = [np.mean(noise_data[k]) for k in ['0.3', '0.4', '0.5']]
cluster_means = [np.mean(cluster_data[k]) for k in ['0.3', '0.4', '0.5']]

x = np.arange(len(eps_labels))
width = 0.35

bars1 = ax4.bar(x - width/2, noise_means, width, label='노이즈 비율', color='#FF5722', edgecolor='black')
bars2 = ax4.bar(x + width/2, cluster_means, width, label='최대 클러스터 비율', color='#3F51B5', edgecolor='black')

ax4.set_xlabel('DBSCAN eps 값', fontsize=11)
ax4.set_ylabel('비율 (%)', fontsize=11)
ax4.set_title('④ DBSCAN의 딜레마: 노이즈 vs 거대 클러스터', fontsize=12, fontweight='bold')
ax4.set_xticks(x)
ax4.set_xticklabels(eps_labels)
ax4.legend(loc='upper left')
ax4.set_ylim(0, 100)

# 값 표시
for bar, val in zip(bars1, noise_means):
    ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, f'{val:.0f}%',
             ha='center', va='bottom', fontsize=9)
for bar, val in zip(bars2, cluster_means):
    ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, f'{val:.0f}%',
             ha='center', va='bottom', fontsize=9)

# 문제 영역 표시
ax4.axhline(y=50, color='red', linestyle='--', linewidth=1, alpha=0.5)
ax4.text(2.3, 52, '← 50% 이상은 문제', fontsize=9, color='red')

plt.tight_layout()
plt.savefig(RESULTS_DIR / 'clustering_visualization.png', dpi=150, bbox_inches='tight')
print(f'저장 완료: {RESULTS_DIR / "clustering_visualization.png"}')
plt.show()
