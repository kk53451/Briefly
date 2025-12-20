# backend/test/scripts/generate_embeddings.py

"""
임베딩 생성 및 캐싱 스크립트

목적: 전체 뉴스 데이터에 대한 임베딩을 생성하고 NPZ 파일로 저장
      클러스터링 실험 시 재사용하여 비용 절감

사용법:
    cd backend
    python -m test.scripts.generate_embeddings

    또는
    python test/scripts/generate_embeddings.py
"""

import os
import sys
import json
import time
import numpy as np
from pathlib import Path
from typing import List, Dict

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI

# ============================================================
# 설정
# ============================================================

# 입력/출력 경로
DATA_DIR = Path(__file__).parent.parent / "data"
INPUT_FILE = DATA_DIR / "news_raw_2025-11-30.jsonl"
OUTPUT_FILE = DATA_DIR / "embeddings_2025-11-30.npz"

# 임베딩 설정
EMBEDDING_MODEL = "text-embedding-3-small"
CONTENT_LIMIT = 1000  # 현재 운영 설정과 동일
BATCH_SIZE = 100  # OpenAI API 배치 크기

# OpenAI 클라이언트
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ============================================================
# 임베딩 생성 함수
# ============================================================

def get_embedding(text: str) -> List[float]:
    """단일 텍스트 임베딩 생성"""
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text[:CONTENT_LIMIT]
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding: {e}", flush=True)
        return []


def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """배치 임베딩 생성 (효율성 향상)"""
    try:
        # 텍스트 길이 제한
        limited_texts = [text[:CONTENT_LIMIT] for text in texts]

        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=limited_texts
        )

        return [item.embedding for item in response.data]
    except Exception as e:
        print(f"Error generating batch embeddings: {e}", flush=True)
        # 실패 시 개별 처리
        return [get_embedding(text) for text in texts]


# ============================================================
# 데이터 로드
# ============================================================

def load_articles(file_path: Path) -> List[Dict]:
    """JSONL 파일에서 기사 로드"""
    articles = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                articles.append(json.loads(line))
    return articles


def filter_articles(articles: List[Dict],
                   min_length: int = 300,
                   min_korean_ratio: float = 0.7) -> List[Dict]:
    """운영 필터 적용 (300자 이상 + 한글 70% 이상)"""
    filtered = []
    for article in articles:
        content_length = article.get("content_length", 0)
        korean_ratio = article.get("korean_ratio", 0)

        if content_length >= min_length and korean_ratio >= min_korean_ratio:
            filtered.append(article)

    return filtered


# ============================================================
# 메인 실행
# ============================================================

def main():
    start_time = time.time()

    print("=" * 60, flush=True)
    print("Embedding Generation", flush=True)
    print("=" * 60, flush=True)
    print(f"Input: {INPUT_FILE}", flush=True)
    print(f"Output: {OUTPUT_FILE}", flush=True)
    print(f"Model: {EMBEDDING_MODEL}", flush=True)
    print(f"Content limit: {CONTENT_LIMIT} chars", flush=True)
    print(f"Batch size: {BATCH_SIZE}", flush=True)
    print("=" * 60, flush=True)

    # 1. 데이터 로드
    print("\n[1/4] Loading articles...", flush=True)
    articles = load_articles(INPUT_FILE)
    print(f"   Loaded: {len(articles)} articles", flush=True)

    # 2. 필터 적용
    print("\n[2/4] Applying production filter (300 chars + 70% Korean)...", flush=True)
    filtered_articles = filter_articles(articles)
    print(f"   After filter: {len(filtered_articles)} articles", flush=True)

    # 3. 임베딩 생성
    print("\n[3/4] Generating embeddings...", flush=True)

    embeddings = []
    article_ids = []
    categories = []

    total = len(filtered_articles)

    for i in range(0, total, BATCH_SIZE):
        batch = filtered_articles[i:i + BATCH_SIZE]
        batch_texts = [article["content"] for article in batch]

        # 배치 임베딩 생성
        batch_embeddings = get_embeddings_batch(batch_texts)

        for j, article in enumerate(batch):
            if batch_embeddings[j]:  # 빈 임베딩이 아닌 경우만
                embeddings.append(batch_embeddings[j])
                article_ids.append(article["id"])
                categories.append(article["category"])

        # 진행률 표시
        progress = min(i + BATCH_SIZE, total)
        elapsed = time.time() - start_time
        rate = progress / elapsed if elapsed > 0 else 0
        eta = (total - progress) / rate if rate > 0 else 0

        print(f"   Progress: {progress}/{total} ({progress/total*100:.1f}%) "
              f"- {rate:.1f} articles/sec - ETA: {eta:.0f}s", flush=True)

    # 4. NPZ 저장
    print("\n[4/4] Saving to NPZ file...", flush=True)

    embeddings_array = np.array(embeddings, dtype=np.float32)
    article_ids_array = np.array(article_ids, dtype=object)
    categories_array = np.array(categories, dtype=object)

    np.savez_compressed(
        OUTPUT_FILE,
        embeddings=embeddings_array,
        article_ids=article_ids_array,
        categories=categories_array
    )

    # 결과 출력
    total_time = time.time() - start_time
    file_size_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)

    print("\n" + "=" * 60, flush=True)
    print("Embedding Generation Complete!", flush=True)
    print("=" * 60, flush=True)
    print(f"Total articles: {len(embeddings)}", flush=True)
    print(f"Embedding dimension: {len(embeddings[0]) if embeddings else 0}", flush=True)
    print(f"Total time: {total_time:.1f}s ({total_time/60:.1f} min)", flush=True)
    print(f"File size: {file_size_mb:.1f} MB", flush=True)
    print(f"Output: {OUTPUT_FILE}", flush=True)
    print("=" * 60, flush=True)

    # 카테고리별 통계
    print("\nCategory breakdown:", flush=True)
    print("-" * 40, flush=True)

    from collections import Counter
    category_counts = Counter(categories)
    for cat, count in sorted(category_counts.items()):
        print(f"  {cat:15s}: {count:,} articles", flush=True)

    # 예상 비용 계산
    total_tokens = sum(len(a["content"][:CONTENT_LIMIT]) for a in filtered_articles) * 1.5  # 한글 ~1.5 tokens/char
    estimated_cost = (total_tokens / 1_000_000) * 0.02  # $0.02 per 1M tokens
    print(f"\nEstimated cost: ${estimated_cost:.2f}", flush=True)


if __name__ == "__main__":
    main()
