"""
임베딩 서비스 (KURE-v1 로컬 추론)

한국어 뉴스 기사 텍스트를 1024차원 벡터로 변환합니다.
모델은 최초 1회 로드 후 메모리에 유지.
임베딩 결과는 로컬 캐시(.npy)에 저장하여 재실행 시 재사용.
"""

import hashlib
import time
import logging
from pathlib import Path
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "embedding_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# 모델 싱글턴 (프로세스 수명 동안 1회 로드)
_model = None


def _get_model():
    """KURE-v1 모델을 로드합니다. 최초 호출 시 다운로드/캐시 로드."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        logger.info("🔄 KURE-v1 모델 로딩 중...")
        t0 = time.time()
        _model = SentenceTransformer("nlpai-lab/KURE-v1")
        logger.info(f"✅ KURE-v1 모델 로드 완료 ({time.time() - t0:.1f}초)")
    return _model


def unload_model():
    """KURE-v1 모델을 GPU 메모리에서 해제합니다.

    임베딩 완료 후 Gemma4 등 다른 GPU 모델이 사용할 수 있도록
    메모리를 확보합니다.
    """
    global _model
    if _model is not None:
        del _model
        _model = None
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass
        logger.info("🗑️ KURE-v1 모델 언로드 완료 (GPU 메모리 해제)")


def _cache_key(texts: List[str], max_chars: int) -> str:
    """텍스트 리스트로부터 캐시 키 생성"""
    content = f"{len(texts)}_{max_chars}_" + texts[0][:100] + texts[-1][:100]
    return hashlib.md5(content.encode()).hexdigest()


def embed_texts(
    texts: List[str],
    max_chars: int = 500,
    batch_size: int = 64,
    cache_label: Optional[str] = None,
) -> np.ndarray:
    """
    텍스트 리스트를 KURE-v1 임베딩 벡터로 변환합니다.
    캐시가 있으면 재사용합니다.

    Args:
        texts: 입력 텍스트 리스트
        max_chars: 텍스트 최대 길이 (토큰 절약)
        batch_size: 배치 크기
        cache_label: 캐시 파일명 라벨 (예: "economy_2026-04-11")

    Returns:
        (n_texts, 1024) 형태의 임베딩 배열
    """
    if not texts:
        return np.array([])

    # 캐시 확인
    key = _cache_key(texts, max_chars)
    label = f"{cache_label}_" if cache_label else ""
    cache_file = CACHE_DIR / f"{label}{len(texts)}_{key}.npy"

    if cache_file.exists():
        logger.info(f"📂 임베딩 캐시 로드: {cache_file.name}")
        return np.load(str(cache_file))

    model = _get_model()

    truncated = [t[:max_chars] for t in texts]

    logger.info(f"🔄 임베딩 생성 중 ({len(truncated)}건, max_chars={max_chars})...")
    t0 = time.time()
    embeddings = model.encode(
        truncated,
        batch_size=batch_size,
        show_progress_bar=len(truncated) > 100,
    )
    elapsed = time.time() - t0
    logger.info(
        f"✅ 임베딩 완료: {embeddings.shape} ({elapsed:.1f}초, "
        f"{len(truncated)/elapsed:.1f}건/초)"
    )

    result = np.array(embeddings)

    # 캐시 저장
    np.save(str(cache_file), result)
    logger.info(f"💾 임베딩 캐시 저장: {cache_file.name} ({cache_file.stat().st_size/1024:.0f}KB)")

    return result


def embed_articles(
    articles: List[dict],
    max_chars: int = 500,
    cache_label: Optional[str] = None,
) -> np.ndarray:
    """
    기사 리스트에서 제목+본문을 결합하여 임베딩합니다.

    Args:
        articles: 기사 딕셔너리 리스트 (title, content 필드 필요)
        max_chars: 결합된 텍스트 최대 길이
        cache_label: 캐시 라벨 (예: "economy_2026-04-11")

    Returns:
        (n_articles, 1024) 형태의 임베딩 배열
    """
    texts = []
    for a in articles:
        text = a.get("title", "") + " " + a.get("content", "")
        texts.append(text)

    return embed_texts(texts, max_chars=max_chars, cache_label=cache_label)
