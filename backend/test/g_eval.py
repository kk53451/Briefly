"""
G-Eval: LLM을 사용한 클러스터 품질 평가

GPT-4o-mini를 활용하여 클러스터의 의미적 품질을 평가합니다.
기하학적 지표(Silhouette Score)로는 측정하기 어려운
"사람이 느끼는 뉴스 주제의 일관성"을 평가합니다.

기술 감사 보고서 권장:
- LLM에게 각 클러스터에 대해 다음 질문을 던져 점수(1-5점) 매기기
- "이 클러스터에 묶인 기사들이 모두 동일한 사건을 다루고 있는가?" (Coherence)
- "이 클러스터에 불필요한 광고나 관계없는 기사가 포함되어 있는가?" (Noise)

사용법:
    evaluator = GEval(api_key="...")
    results = evaluator.evaluate_clusters(clusters, articles)
"""

import os
import sys
import json
import time
from typing import List, Dict, Any, Optional
import numpy as np

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv()

import openai

# OpenAI 설정
openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


class GEval:
    """
    G-Eval: LLM 기반 클러스터 품질 평가기

    사용법:
        evaluator = GEval()
        results = evaluator.evaluate_clusters(clusters, articles)
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        temperature: float = 0.1,
        max_articles_per_cluster: int = 5
    ):
        """
        Args:
            model: 사용할 OpenAI 모델
            temperature: LLM 응답 온도 (낮을수록 일관성 높음)
            max_articles_per_cluster: 클러스터당 평가에 사용할 최대 기사 수
        """
        self.model = model
        self.temperature = temperature
        self.max_articles_per_cluster = max_articles_per_cluster

    def evaluate_cluster(
        self,
        articles: List[Dict],
        cluster_id: int = 0
    ) -> Dict[str, Any]:
        """
        단일 클러스터의 품질을 평가합니다.

        Args:
            articles: 클러스터 내 기사 리스트
            cluster_id: 클러스터 ID (로깅용)

        Returns:
            평가 결과 딕셔너리
        """
        if not articles:
            return {"error": "빈 클러스터"}

        # 기사 수 제한 (토큰 비용 절감)
        sample_articles = articles[:self.max_articles_per_cluster]

        # 기사 텍스트 구성
        articles_text = self._format_articles(sample_articles)

        # 프롬프트 구성
        prompt = self._build_evaluation_prompt(articles_text)

        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=500
            )

            result_text = response.choices[0].message.content.strip()
            result = self._parse_response(result_text)

            result["cluster_id"] = cluster_id
            result["n_articles"] = len(articles)
            result["n_evaluated"] = len(sample_articles)

            return result

        except openai.RateLimitError as e:
            return {"error": f"Rate Limit: {e}", "cluster_id": cluster_id}
        except openai.APIError as e:
            return {"error": f"API Error: {e}", "cluster_id": cluster_id}
        except Exception as e:
            return {"error": f"Unknown Error: {e}", "cluster_id": cluster_id}

    def evaluate_clusters(
        self,
        clusters: Dict[int, List[int]],
        articles: List[Dict],
        sample_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        여러 클러스터의 품질을 평가합니다.

        Args:
            clusters: 클러스터 ID → 기사 인덱스 리스트
            articles: 전체 기사 리스트
            sample_size: 평가할 클러스터 샘플 수 (None이면 전체)

        Returns:
            종합 평가 결과
        """
        cluster_ids = list(clusters.keys())

        # 샘플링 (비용 절감)
        if sample_size and sample_size < len(cluster_ids):
            # 크기가 큰 클러스터 우선 선택 (더 중요)
            cluster_ids = sorted(
                cluster_ids,
                key=lambda cid: len(clusters[cid]),
                reverse=True
            )[:sample_size]

        results = []
        total_coherence = []
        total_noise = []

        for cluster_id in cluster_ids:
            member_indices = clusters[cluster_id]
            cluster_articles = [articles[idx] for idx in member_indices]

            result = self.evaluate_cluster(cluster_articles, cluster_id)
            results.append(result)

            if "coherence_score" in result:
                total_coherence.append(result["coherence_score"])
            if "noise_score" in result:
                total_noise.append(result["noise_score"])

            # Rate limit 방지
            time.sleep(0.5)

        # 종합 통계
        summary = {
            "n_clusters_evaluated": len(results),
            "n_clusters_total": len(clusters),
            "avg_coherence": float(np.mean(total_coherence)) if total_coherence else 0,
            "avg_noise": float(np.mean(total_noise)) if total_noise else 0,
            "std_coherence": float(np.std(total_coherence)) if total_coherence else 0,
            "std_noise": float(np.std(total_noise)) if total_noise else 0,
            "cluster_results": results
        }

        # 종합 점수 (높을수록 좋음)
        # coherence는 높을수록 좋고, noise는 낮을수록 좋음
        if total_coherence and total_noise:
            summary["overall_score"] = summary["avg_coherence"] - summary["avg_noise"]
        else:
            summary["overall_score"] = 0

        return summary

    def _format_articles(self, articles: List[Dict]) -> str:
        """기사 리스트를 텍스트로 포맷팅합니다."""
        formatted = []

        for i, article in enumerate(articles, 1):
            title = article.get("title", "제목 없음")
            content = article.get("hilight", "") or article.get("content", "")
            content = content[:300]  # 토큰 절약

            formatted.append(f"[기사 {i}]\n제목: {title}\n내용: {content}")

        return "\n\n".join(formatted)

    def _build_evaluation_prompt(self, articles_text: str) -> str:
        """평가 프롬프트를 구성합니다."""
        return f"""당신은 뉴스 클러스터링 품질 평가 전문가입니다.
아래 기사들이 하나의 클러스터(그룹)로 묶여 있습니다.
이 클러스터의 품질을 평가해주세요.

**평가 기준:**

1. **Coherence (일관성)**: 1-5점
   - 모든 기사가 동일한 사건/주제를 다루고 있는가?
   - 5점: 모든 기사가 완벽하게 같은 사건을 다룸
   - 4점: 대부분 같은 사건, 약간의 관련 기사 포함
   - 3점: 비슷한 주제이지만 다른 사건도 섞임
   - 2점: 주제가 다른 기사가 여러 개 포함
   - 1점: 전혀 관련 없는 기사들이 묶임

2. **Noise (노이즈)**: 1-5점
   - 광고, 스팸, 또는 전혀 관련 없는 기사가 포함되어 있는가?
   - 5점: 명백한 광고/스팸이 다수 포함
   - 4점: 광고성 기사가 일부 포함
   - 3점: 관련 없는 기사가 일부 섞임
   - 2점: 약간의 관련 없는 기사만 있음
   - 1점: 모든 기사가 관련 있음 (노이즈 없음)

**평가할 기사들:**

{articles_text}

**응답 형식 (JSON만 출력):**
{{"coherence_score": 점수, "noise_score": 점수, "coherence_reason": "이유", "noise_reason": "이유", "main_topic": "클러스터의 주요 주제"}}

JSON 형식으로만 응답해주세요:"""

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """LLM 응답을 파싱합니다."""
        try:
            # JSON 블록 추출
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            result = json.loads(response_text)

            # 점수 유효성 검사
            coherence = result.get("coherence_score", 3)
            noise = result.get("noise_score", 3)

            result["coherence_score"] = max(1, min(5, int(coherence)))
            result["noise_score"] = max(1, min(5, int(noise)))

            return result

        except json.JSONDecodeError as e:
            return {
                "coherence_score": 3,
                "noise_score": 3,
                "parse_error": str(e),
                "raw_response": response_text[:200]
            }


def run_g_eval(
    clusters: Dict[int, List[int]],
    articles: List[Dict],
    sample_size: int = 10
) -> Dict[str, Any]:
    """
    편의 함수: G-Eval 실행

    Args:
        clusters: 클러스터 딕셔너리
        articles: 기사 리스트
        sample_size: 평가할 클러스터 수

    Returns:
        평가 결과
    """
    evaluator = GEval()
    return evaluator.evaluate_clusters(clusters, articles, sample_size)


def format_geval_report(results: Dict[str, Any]) -> str:
    """G-Eval 결과를 읽기 쉬운 리포트로 포맷팅합니다."""
    lines = []
    lines.append("=" * 60)
    lines.append("G-Eval 클러스터 품질 평가 리포트")
    lines.append("=" * 60)
    lines.append("")

    # 요약
    lines.append("📊 종합 통계")
    lines.append("-" * 40)
    lines.append(f"  평가 클러스터 수: {results['n_clusters_evaluated']}/{results['n_clusters_total']}")
    lines.append(f"  평균 일관성 점수: {results['avg_coherence']:.2f}/5.00")
    lines.append(f"  평균 노이즈 점수: {results['avg_noise']:.2f}/5.00 (낮을수록 좋음)")
    lines.append(f"  종합 품질 점수: {results['overall_score']:.2f}")
    lines.append("")

    # 점수 해석
    lines.append("📈 점수 해석")
    lines.append("-" * 40)

    coherence = results['avg_coherence']
    if coherence >= 4.5:
        coherence_grade = "매우 우수 ⭐⭐⭐⭐⭐"
    elif coherence >= 4.0:
        coherence_grade = "우수 ⭐⭐⭐⭐"
    elif coherence >= 3.0:
        coherence_grade = "보통 ⭐⭐⭐"
    elif coherence >= 2.0:
        coherence_grade = "미흡 ⭐⭐"
    else:
        coherence_grade = "매우 미흡 ⭐"
    lines.append(f"  일관성: {coherence_grade}")

    noise = results['avg_noise']
    if noise <= 1.5:
        noise_grade = "매우 깨끗 ⭐⭐⭐⭐⭐"
    elif noise <= 2.0:
        noise_grade = "깨끗 ⭐⭐⭐⭐"
    elif noise <= 3.0:
        noise_grade = "보통 ⭐⭐⭐"
    elif noise <= 4.0:
        noise_grade = "노이즈 있음 ⭐⭐"
    else:
        noise_grade = "노이즈 많음 ⭐"
    lines.append(f"  노이즈: {noise_grade}")
    lines.append("")

    # 개별 클러스터 결과 (상위 5개)
    lines.append("📋 주요 클러스터 평가 결과")
    lines.append("-" * 40)

    cluster_results = results.get("cluster_results", [])
    for result in cluster_results[:5]:
        if "error" in result:
            lines.append(f"  클러스터 {result.get('cluster_id', '?')}: 평가 실패 - {result['error']}")
        else:
            cid = result.get("cluster_id", "?")
            n = result.get("n_articles", 0)
            coh = result.get("coherence_score", 0)
            noise = result.get("noise_score", 0)
            topic = result.get("main_topic", "주제 미정")

            lines.append(f"\n  클러스터 {cid} ({n}개 기사):")
            lines.append(f"    일관성: {coh}/5, 노이즈: {noise}/5")
            lines.append(f"    주요 주제: {topic[:50]}...")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)


# 테스트 코드
if __name__ == "__main__":
    print("G-Eval 테스트")
    print("=" * 50)

    # 테스트 데이터
    test_articles = [
        {"title": "삼성전자 3분기 영업이익 10조원 달성", "hilight": "삼성전자가 3분기 영업이익 10조원을 기록했다고 발표했다."},
        {"title": "삼성전자, 3분기 실적 발표... 영업익 10조", "hilight": "삼성전자의 3분기 영업이익이 10조원을 돌파했다."},
        {"title": "삼성 반도체 실적 회복세", "hilight": "반도체 업황 회복으로 삼성전자 실적이 개선됐다."},
    ]

    test_clusters = {
        0: [0, 1, 2]  # 모든 기사가 같은 클러스터
    }

    # 평가 실행
    print("\n단일 클러스터 평가 테스트...")

    evaluator = GEval()
    result = evaluator.evaluate_cluster(test_articles, cluster_id=0)

    print(f"\n결과:")
    print(f"  일관성 점수: {result.get('coherence_score', 'N/A')}/5")
    print(f"  노이즈 점수: {result.get('noise_score', 'N/A')}/5")
    print(f"  주요 주제: {result.get('main_topic', 'N/A')}")
