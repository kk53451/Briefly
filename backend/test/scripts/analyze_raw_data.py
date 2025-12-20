# backend/test/scripts/analyze_raw_data.py

"""
수집된 뉴스 데이터 분석 스크립트

목적: 필터 없이 수집된 데이터를 분석하여 최적의 필터링 전략 수립

사용법:
    python test/scripts/analyze_raw_data.py
"""

import json
import sys
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime
import statistics

# ============================================================
# 설정
# ============================================================

DATA_FILE = Path(__file__).parent.parent / "data" / "news_raw_2025-11-30.jsonl"
RESULTS_DIR = Path(__file__).parent.parent / "results"

# ============================================================
# 데이터 로드
# ============================================================

def load_data(file_path: Path) -> list:
    """JSONL 파일에서 데이터 로드"""
    articles = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                articles.append(json.loads(line))
    return articles


# ============================================================
# 분석 함수들
# ============================================================

def analyze_basic_stats(articles: list) -> dict:
    """기본 통계 분석"""
    total = len(articles)

    # 카테고리별 분포
    category_counts = Counter(a["category"] for a in articles)

    # 언론사별 분포
    provider_counts = Counter(a["provider"] for a in articles)

    return {
        "total": total,
        "categories": dict(category_counts),
        "providers": dict(provider_counts.most_common(30))
    }


def analyze_content_length(articles: list) -> dict:
    """본문 길이 분석"""
    lengths = [a["content_length"] for a in articles]

    # 기본 통계
    stats = {
        "min": min(lengths),
        "max": max(lengths),
        "mean": statistics.mean(lengths),
        "median": statistics.median(lengths),
        "stdev": statistics.stdev(lengths),
    }

    # 백분위수
    sorted_lengths = sorted(lengths)
    n = len(sorted_lengths)
    percentiles = {}
    for p in [1, 5, 10, 25, 50, 75, 90, 95, 99]:
        idx = int(n * p / 100)
        percentiles[f"p{p}"] = sorted_lengths[idx]

    # 구간별 분포
    bins = [0, 100, 200, 300, 500, 1000, 2000, 3000, 5000, 10000, float("inf")]
    bin_labels = ["0-100", "100-200", "200-300", "300-500", "500-1000",
                  "1000-2000", "2000-3000", "3000-5000", "5000-10000", "10000+"]
    distribution = {label: 0 for label in bin_labels}

    for length in lengths:
        for i, (low, high) in enumerate(zip(bins[:-1], bins[1:])):
            if low <= length < high:
                distribution[bin_labels[i]] += 1
                break

    # 비율로 변환
    distribution_pct = {k: round(v / len(lengths) * 100, 2) for k, v in distribution.items()}

    return {
        "stats": stats,
        "percentiles": percentiles,
        "distribution": distribution,
        "distribution_pct": distribution_pct
    }


def analyze_korean_ratio(articles: list) -> dict:
    """한글 비율 분석"""
    ratios = [a["korean_ratio"] for a in articles]

    # 기본 통계
    stats = {
        "min": min(ratios),
        "max": max(ratios),
        "mean": statistics.mean(ratios),
        "median": statistics.median(ratios),
        "stdev": statistics.stdev(ratios),
    }

    # 구간별 분포
    bins = [0, 0.3, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0]
    bin_labels = ["0-30%", "30-50%", "50-60%", "60-70%", "70-80%", "80-90%", "90-95%", "95-100%"]
    distribution = {label: 0 for label in bin_labels}

    for ratio in ratios:
        for i, (low, high) in enumerate(zip(bins[:-1], bins[1:])):
            if low <= ratio < high:
                distribution[bin_labels[i]] += 1
                break
        if ratio >= 0.95:
            distribution["95-100%"] += 1

    # 비율로 변환
    distribution_pct = {k: round(v / len(ratios) * 100, 2) for k, v in distribution.items()}

    # 필터 임계값별 통과율
    thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]
    pass_rates = {}
    for threshold in thresholds:
        passed = sum(1 for r in ratios if r >= threshold)
        pass_rates[f">={int(threshold*100)}%"] = round(passed / len(ratios) * 100, 2)

    return {
        "stats": stats,
        "distribution": distribution,
        "distribution_pct": distribution_pct,
        "pass_rates": pass_rates
    }


def analyze_time_distribution(articles: list) -> dict:
    """시간대별 분포 분석"""
    hour_counts = Counter()

    for article in articles:
        published = article.get("published_at", "")
        if published:
            try:
                # "2025-11-30 10:30:00" 형식 파싱
                dt = datetime.strptime(published[:19], "%Y-%m-%d %H:%M:%S")
                hour_counts[dt.hour] += 1
            except:
                pass

    # 24시간 전체 채우기
    distribution = {h: hour_counts.get(h, 0) for h in range(24)}

    return {
        "hourly": distribution,
        "peak_hour": max(distribution, key=distribution.get),
        "min_hour": min(distribution, key=distribution.get)
    }


def analyze_filter_impact(articles: list) -> dict:
    """필터 적용 시 영향 분석"""
    total = len(articles)

    results = {}

    # 본문 길이 필터
    for min_length in [100, 200, 300, 500, 1000]:
        passed = sum(1 for a in articles if a["content_length"] >= min_length)
        results[f"content_length>={min_length}"] = {
            "passed": passed,
            "filtered": total - passed,
            "pass_rate": round(passed / total * 100, 2)
        }

    # 한글 비율 필터
    for threshold in [0.5, 0.6, 0.7, 0.8]:
        passed = sum(1 for a in articles if a["korean_ratio"] >= threshold)
        results[f"korean_ratio>={int(threshold*100)}%"] = {
            "passed": passed,
            "filtered": total - passed,
            "pass_rate": round(passed / total * 100, 2)
        }

    # 복합 필터 (현재 프로덕션 설정: 300자 + 70% 한글)
    passed = sum(1 for a in articles
                 if a["content_length"] >= 300 and a["korean_ratio"] >= 0.7)
    results["production_filter(300자+70%한글)"] = {
        "passed": passed,
        "filtered": total - passed,
        "pass_rate": round(passed / total * 100, 2)
    }

    return results


def analyze_category_details(articles: list) -> dict:
    """카테고리별 상세 분석"""
    category_data = defaultdict(list)
    for article in articles:
        category_data[article["category"]].append(article)

    results = {}
    for category, cat_articles in sorted(category_data.items()):
        lengths = [a["content_length"] for a in cat_articles]
        ratios = [a["korean_ratio"] for a in cat_articles]

        results[category] = {
            "count": len(cat_articles),
            "content_length": {
                "mean": round(statistics.mean(lengths), 0),
                "median": round(statistics.median(lengths), 0),
                "min": min(lengths),
                "max": max(lengths)
            },
            "korean_ratio": {
                "mean": round(statistics.mean(ratios), 4),
                "min": round(min(ratios), 4),
            },
            "short_articles(<300)": sum(1 for l in lengths if l < 300),
            "low_korean(<70%)": sum(1 for r in ratios if r < 0.7)
        }

    return results


def analyze_providers(articles: list) -> dict:
    """언론사별 상세 분석"""
    provider_data = defaultdict(list)
    for article in articles:
        provider_data[article["provider"]].append(article)

    results = {}
    for provider, prov_articles in sorted(provider_data.items(),
                                          key=lambda x: -len(x[1]))[:20]:
        lengths = [a["content_length"] for a in prov_articles]
        ratios = [a["korean_ratio"] for a in prov_articles]

        results[provider] = {
            "count": len(prov_articles),
            "avg_length": round(statistics.mean(lengths), 0),
            "avg_korean": round(statistics.mean(ratios), 4),
            "short_articles(<300)": sum(1 for l in lengths if l < 300),
        }

    return results


# ============================================================
# 리포트 생성
# ============================================================

def generate_report(articles: list) -> str:
    """분석 리포트 생성"""

    basic = analyze_basic_stats(articles)
    content = analyze_content_length(articles)
    korean = analyze_korean_ratio(articles)
    time_dist = analyze_time_distribution(articles)
    filter_impact = analyze_filter_impact(articles)
    category_details = analyze_category_details(articles)
    provider_details = analyze_providers(articles)

    report = []
    report.append("# 뉴스 데이터 분석 보고서")
    report.append("")
    report.append(f"**분석 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"**데이터 파일**: {DATA_FILE.name}")
    report.append(f"**총 기사 수**: {basic['total']:,}건")
    report.append("")

    # 1. 카테고리별 분포
    report.append("---")
    report.append("")
    report.append("## 1. 카테고리별 분포")
    report.append("")
    report.append("| 카테고리 | 기사 수 | 비율 |")
    report.append("|----------|--------|------|")
    for cat, count in sorted(basic["categories"].items(), key=lambda x: -x[1]):
        pct = count / basic["total"] * 100
        report.append(f"| {cat} | {count:,} | {pct:.1f}% |")
    report.append("")

    # 2. 본문 길이 분석
    report.append("---")
    report.append("")
    report.append("## 2. 본문 길이 분석")
    report.append("")
    report.append("### 기본 통계")
    report.append("")
    report.append(f"- **최소**: {content['stats']['min']:,}자")
    report.append(f"- **최대**: {content['stats']['max']:,}자")
    report.append(f"- **평균**: {content['stats']['mean']:,.0f}자")
    report.append(f"- **중앙값**: {content['stats']['median']:,.0f}자")
    report.append(f"- **표준편차**: {content['stats']['stdev']:,.0f}자")
    report.append("")

    report.append("### 백분위수")
    report.append("")
    report.append("| 백분위 | 길이 |")
    report.append("|--------|------|")
    for p, val in content["percentiles"].items():
        report.append(f"| {p} | {val:,}자 |")
    report.append("")

    report.append("### 구간별 분포")
    report.append("")
    report.append("| 구간 | 기사 수 | 비율 |")
    report.append("|------|--------|------|")
    for bin_name, count in content["distribution"].items():
        pct = content["distribution_pct"][bin_name]
        report.append(f"| {bin_name} | {count:,} | {pct}% |")
    report.append("")

    # 3. 한글 비율 분석
    report.append("---")
    report.append("")
    report.append("## 3. 한글 비율 분석")
    report.append("")
    report.append("### 기본 통계")
    report.append("")
    report.append(f"- **최소**: {korean['stats']['min']:.2%}")
    report.append(f"- **최대**: {korean['stats']['max']:.2%}")
    report.append(f"- **평균**: {korean['stats']['mean']:.2%}")
    report.append(f"- **중앙값**: {korean['stats']['median']:.2%}")
    report.append("")

    report.append("### 임계값별 통과율")
    report.append("")
    report.append("| 임계값 | 통과율 |")
    report.append("|--------|--------|")
    for threshold, rate in korean["pass_rates"].items():
        report.append(f"| {threshold} | {rate}% |")
    report.append("")

    # 4. 시간대별 분포
    report.append("---")
    report.append("")
    report.append("## 4. 시간대별 분포")
    report.append("")
    report.append(f"- **피크 시간**: {time_dist['peak_hour']}시 ({time_dist['hourly'][time_dist['peak_hour']]:,}건)")
    report.append(f"- **최저 시간**: {time_dist['min_hour']}시 ({time_dist['hourly'][time_dist['min_hour']]:,}건)")
    report.append("")
    report.append("| 시간 | 기사 수 |")
    report.append("|------|--------|")
    for hour in range(24):
        count = time_dist["hourly"][hour]
        bar = "#" * (count // 50)
        report.append(f"| {hour:02d}:00 | {count:,} {bar} |")
    report.append("")

    # 5. 필터 영향 분석
    report.append("---")
    report.append("")
    report.append("## 5. 필터 영향 분석")
    report.append("")
    report.append("| 필터 조건 | 통과 | 제외 | 통과율 |")
    report.append("|-----------|------|------|--------|")
    for filter_name, result in filter_impact.items():
        report.append(f"| {filter_name} | {result['passed']:,} | {result['filtered']:,} | {result['pass_rate']}% |")
    report.append("")

    # 6. 카테고리별 상세
    report.append("---")
    report.append("")
    report.append("## 6. 카테고리별 상세 분석")
    report.append("")
    report.append("| 카테고리 | 기사 수 | 평균 길이 | 짧은기사(<300) | 저한글(<70%) |")
    report.append("|----------|--------|----------|---------------|-------------|")
    for cat, stats in category_details.items():
        report.append(f"| {cat} | {stats['count']:,} | {stats['content_length']['mean']:,.0f}자 | {stats['short_articles(<300)']} | {stats['low_korean(<70%)']} |")
    report.append("")

    # 7. 상위 언론사
    report.append("---")
    report.append("")
    report.append("## 7. 상위 20개 언론사")
    report.append("")
    report.append("| 언론사 | 기사 수 | 평균 길이 | 평균 한글비율 |")
    report.append("|--------|--------|----------|-------------|")
    for provider, stats in provider_details.items():
        report.append(f"| {provider} | {stats['count']:,} | {stats['avg_length']:,.0f}자 | {stats['avg_korean']:.1%} |")
    report.append("")

    # 8. 결론 및 권장사항
    report.append("---")
    report.append("")
    report.append("## 8. 결론 및 권장사항")
    report.append("")

    # 짧은 기사 비율 계산
    short_rate = content["distribution_pct"].get("0-100", 0) + content["distribution_pct"].get("100-200", 0) + content["distribution_pct"].get("200-300", 0)
    low_korean_rate = 100 - korean["pass_rates"][">=70%"]

    report.append("### 현재 필터 설정 평가")
    report.append("")
    report.append(f"- **본문 300자 필터**: 전체의 {short_rate:.1f}%가 제외됨")
    report.append(f"- **한글 70% 필터**: 전체의 {low_korean_rate:.1f}%가 제외됨")
    report.append(f"- **복합 필터 통과율**: {filter_impact['production_filter(300자+70%한글)']['pass_rate']}%")
    report.append("")

    report.append("### 권장사항")
    report.append("")
    if short_rate < 5:
        report.append("1. **본문 길이 필터**: 현재 300자 유지 권장 (짧은 기사가 적음)")
    else:
        report.append(f"1. **본문 길이 필터**: {short_rate:.1f}%가 짧은 기사 - 필터 유지 필요")

    if low_korean_rate < 5:
        report.append("2. **한글 비율 필터**: 현재 70% 유지 권장 (비한글 기사가 적음)")
    else:
        report.append(f"2. **한글 비율 필터**: {low_korean_rate:.1f}%가 저한글 - 필터 유지 필요")

    report.append("")

    return "\n".join(report)


# ============================================================
# 메인 실행
# ============================================================

def main():
    print("=" * 60)
    print("News Data Analysis")
    print("=" * 60)

    # 데이터 로드
    print(f"\nLoading data from: {DATA_FILE}")
    if not DATA_FILE.exists():
        print(f"ERROR: File not found: {DATA_FILE}")
        sys.exit(1)

    articles = load_data(DATA_FILE)
    print(f"Loaded {len(articles):,} articles")

    # 분석 실행
    print("\nAnalyzing...")

    # 기본 통계 출력
    basic = analyze_basic_stats(articles)
    print(f"\n[Basic Stats]")
    print(f"  Total: {basic['total']:,}")
    print(f"  Categories: {len(basic['categories'])}")
    print(f"  Providers: {len(basic['providers'])}")

    # 본문 길이 분석
    content = analyze_content_length(articles)
    print(f"\n[Content Length]")
    print(f"  Mean: {content['stats']['mean']:,.0f} chars")
    print(f"  Median: {content['stats']['median']:,.0f} chars")
    print(f"  Min: {content['stats']['min']:,} chars")
    print(f"  Max: {content['stats']['max']:,} chars")

    # 한글 비율 분석
    korean = analyze_korean_ratio(articles)
    print(f"\n[Korean Ratio]")
    print(f"  Mean: {korean['stats']['mean']:.2%}")
    print(f"  Pass rate (>=70%): {korean['pass_rates']['>=70%']}%")

    # 필터 영향
    filter_impact = analyze_filter_impact(articles)
    print(f"\n[Filter Impact]")
    prod_filter = filter_impact["production_filter(300자+70%한글)"]
    print(f"  Production filter pass rate: {prod_filter['pass_rate']}%")
    print(f"  Would filter out: {prod_filter['filtered']:,} articles")

    # 리포트 생성
    print("\nGenerating report...")
    report = generate_report(articles)

    # 결과 저장
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    report_file = RESULTS_DIR / f"analysis_report_{DATA_FILE.stem.split('_')[-1]}.md"

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nReport saved to: {report_file}")
    print("=" * 60)

    # 콘솔에도 출력
    print("\n" + report)


if __name__ == "__main__":
    main()
