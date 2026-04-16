"""
ONNX 양자화 임베딩 속도 & 품질 비교 실험

동일한 뉴스 텍스트에 대해:
  1. PyTorch 원본 (현재 방식)
  2. ONNX 기본
  3. ONNX Int8 양자화

세 가지를 비교하여 속도 향상과 품질 손실을 측정합니다.

사용법:
    cd backend
    pip install sentence-transformers[onnx]
    python test/compare_onnx_quantization.py

출력:
    - 속도 비교 테이블
    - 임베딩 품질 비교 (코사인 유사도)
    - 클러스터링 결과 비교
"""

import sys
import time
import json
import numpy as np
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from app.utils.dynamo import get_news_by_category_and_date

RESULTS_DIR = Path(__file__).parent / "results"


def load_texts(category="economy", date="2025-12-02", limit=None):
    """DynamoDB에서 텍스트 로드"""
    articles = get_news_by_category_and_date(category, date)
    if limit:
        articles = articles[:limit]
    texts = []
    for a in articles:
        text = a.get("title", "") + " " + (a.get("content") or a.get("hilight", ""))
        texts.append(text[:1000])
    return texts, articles


def benchmark_pytorch(texts, model_name="nlpai-lab/KURE-v1"):
    """PyTorch 원본 추론"""
    from sentence_transformers import SentenceTransformer

    print(f"\n  [1/3] PyTorch 원본")
    print(f"  모델 로딩 중...", end=" ", flush=True)
    t0 = time.time()
    model = SentenceTransformer(model_name)
    load_time = time.time() - t0
    print(f"{load_time:.1f}초")

    print(f"  임베딩 생성 중...", end=" ", flush=True)
    t0 = time.time()
    embeddings = model.encode(texts, batch_size=32, show_progress_bar=False)
    encode_time = time.time() - t0
    print(f"{encode_time:.1f}초")

    del model  # 메모리 해제

    return {
        "method": "pytorch",
        "load_time": load_time,
        "encode_time": encode_time,
        "total_time": load_time + encode_time,
        "shape": embeddings.shape,
        "embeddings": embeddings,
    }


def benchmark_onnx(texts, model_name="nlpai-lab/KURE-v1"):
    """ONNX 기본 추론"""
    from sentence_transformers import SentenceTransformer

    print(f"\n  [2/3] ONNX 기본")
    print(f"  모델 로딩 중 (ONNX 변환 포함, 첫 실행 시 느림)...", end=" ", flush=True)
    t0 = time.time()
    model = SentenceTransformer(model_name, backend="onnx")
    load_time = time.time() - t0
    print(f"{load_time:.1f}초")

    print(f"  임베딩 생성 중...", end=" ", flush=True)
    t0 = time.time()
    embeddings = model.encode(texts, batch_size=32, show_progress_bar=False)
    encode_time = time.time() - t0
    print(f"{encode_time:.1f}초")

    del model

    return {
        "method": "onnx",
        "load_time": load_time,
        "encode_time": encode_time,
        "total_time": load_time + encode_time,
        "shape": embeddings.shape,
        "embeddings": embeddings,
    }


def benchmark_onnx_quantized(texts, model_name="nlpai-lab/KURE-v1"):
    """ONNX Int8 양자화 추론"""
    from sentence_transformers import SentenceTransformer, export_dynamic_quantized_onnx_model

    quantized_path = Path(__file__).parent / "models" / "kure_v1_int8"

    # 양자화 모델이 없으면 생성
    if not (quantized_path / "onnx" / "model_qint8_avx512_vnni.onnx").exists():
        print(f"\n  [3/3] ONNX Int8 양자화")
        print(f"  양자화 모델 생성 중 (1회만)...", end=" ", flush=True)
        quantized_path.mkdir(parents=True, exist_ok=True)
        t0 = time.time()

        base_model = SentenceTransformer(model_name, backend="onnx")
        try:
            export_dynamic_quantized_onnx_model(
                base_model, "avx512_vnni", str(quantized_path)
            )
        except Exception:
            # avx512 미지원 시 arm64 또는 avx2로 폴백
            try:
                export_dynamic_quantized_onnx_model(
                    base_model, "avx2", str(quantized_path)
                )
            except Exception as e:
                print(f"\n  양자화 실패: {e}")
                print(f"  ONNX 기본 결과를 복사합니다...")
                del base_model
                return None

        del base_model
        convert_time = time.time() - t0
        print(f"{convert_time:.1f}초")
    else:
        print(f"\n  [3/3] ONNX Int8 양자화 (캐시 사용)")

    # 양자화 모델 로드 및 추론
    print(f"  모델 로딩 중...", end=" ", flush=True)
    t0 = time.time()

    # 양자화 모델 파일 찾기
    onnx_dir = quantized_path / "onnx"
    quantized_files = list(onnx_dir.glob("*qint8*.onnx"))
    if quantized_files:
        file_name = f"onnx/{quantized_files[0].name}"
    else:
        print(f"\n  양자화 모델 파일을 찾을 수 없습니다.")
        return None

    model = SentenceTransformer(
        str(quantized_path),
        backend="onnx",
        model_kwargs={"file_name": file_name},
    )
    load_time = time.time() - t0
    print(f"{load_time:.1f}초")

    print(f"  임베딩 생성 중...", end=" ", flush=True)
    t0 = time.time()
    embeddings = model.encode(texts, batch_size=32, show_progress_bar=False)
    encode_time = time.time() - t0
    print(f"{encode_time:.1f}초")

    del model

    return {
        "method": "onnx_int8",
        "load_time": load_time,
        "encode_time": encode_time,
        "total_time": load_time + encode_time,
        "shape": embeddings.shape,
        "embeddings": embeddings,
    }


def compare_quality(results):
    """임베딩 품질 비교 — PyTorch를 기준으로 다른 방법의 유사도 측정"""
    baseline = results[0]["embeddings"]  # PyTorch

    print(f"\n{'='*60}")
    print(f"  품질 비교 (PyTorch 대비 코사인 유사도)")
    print(f"{'='*60}")

    for r in results[1:]:
        if r is None:
            continue
        emb = r["embeddings"]

        # 각 벡터 쌍의 코사인 유사도
        sims = []
        for i in range(len(baseline)):
            a = baseline[i] / np.linalg.norm(baseline[i])
            b = emb[i] / np.linalg.norm(emb[i])
            sims.append(np.dot(a, b))

        sims = np.array(sims)
        print(f"\n  {r['method']}:")
        print(f"    평균 유사도: {sims.mean():.6f}")
        print(f"    최소 유사도: {sims.min():.6f}")
        print(f"    최대 유사도: {sims.max():.6f}")
        print(f"    표준편차:    {sims.std():.6f}")

        if sims.mean() > 0.999:
            print(f"    → 거의 동일 (품질 손실 무시 가능)")
        elif sims.mean() > 0.99:
            print(f"    → 매우 유사 (미미한 품질 차이)")
        elif sims.mean() > 0.95:
            print(f"    → 유사 (약간의 품질 차이, 클러스터링에는 영향 적음)")
        else:
            print(f"    → 차이 있음 (클러스터링 결과에 영향 가능)")


def compare_clustering(results):
    """각 임베딩으로 HDBSCAN 클러스터링 → 결과 비교"""
    import umap
    from test.algorithms.hdbscan_clustering import cluster_with_hdbscan

    print(f"\n{'='*60}")
    print(f"  클러스터링 결과 비교 (UMAP→15d + HDBSCAN mcs=5)")
    print(f"{'='*60}")

    for r in results:
        if r is None:
            continue

        # UMAP 축소
        reducer = umap.UMAP(n_components=15, n_neighbors=15, min_dist=0.0,
                           metric="cosine", random_state=42)
        reduced = reducer.fit_transform(r["embeddings"])

        # HDBSCAN
        labels, clusters, info = cluster_with_hdbscan(reduced, min_cluster_size=5,
                                                       metric="euclidean")
        n_clusters = len(clusters)
        noise = int(np.sum(labels == -1))
        sizes = sorted([len(m) for m in clusters.values()], reverse=True)

        print(f"\n  {r['method']}:")
        print(f"    클러스터: {n_clusters}, 노이즈: {noise} ({noise/len(labels):.1%})")
        print(f"    크기: {sizes[:8]}{'...' if len(sizes) > 8 else ''}")


def main():
    print(f"{'='*60}")
    print(f"  ONNX 양자화 임베딩 속도 & 품질 비교")
    print(f"{'='*60}")

    # 텍스트 로드
    print(f"\n데이터 로드 중...")
    texts, articles = load_texts("economy", "2025-12-02")
    print(f"  {len(texts)}개 텍스트 로드됨")

    # 벤치마크 실행
    print(f"\n{'='*60}")
    print(f"  속도 벤치마크")
    print(f"{'='*60}")

    r_pytorch = benchmark_pytorch(texts)
    r_onnx = benchmark_onnx(texts)
    r_int8 = benchmark_onnx_quantized(texts)

    results = [r_pytorch, r_onnx]
    if r_int8:
        results.append(r_int8)

    # 속도 비교 테이블
    print(f"\n{'='*70}")
    print(f"{'METHOD':<15} {'LOAD':>8} {'ENCODE':>8} {'TOTAL':>8} {'SPEEDUP':>8} {'DIM':>5}")
    print(f"{'='*70}")

    baseline_total = r_pytorch["total_time"]
    baseline_encode = r_pytorch["encode_time"]

    for r in results:
        speedup_total = baseline_total / r["total_time"]
        speedup_encode = baseline_encode / r["encode_time"]
        print(f"{r['method']:<15} {r['load_time']:>7.1f}s {r['encode_time']:>7.1f}s "
              f"{r['total_time']:>7.1f}s {speedup_encode:>7.2f}x {r['shape'][1]:>5}")

    print(f"{'='*70}")
    print(f"SPEEDUP = 순수 인코딩 시간 기준 (모델 로드 제외)")

    # 품질 비교
    compare_quality(results)

    # 클러스터링 비교
    compare_clustering(results)

    # 6000건 예상 시간
    print(f"\n{'='*60}")
    print(f"  6000건 예상 소요시간")
    print(f"{'='*60}")
    for r in results:
        est = r["encode_time"] / len(texts) * 6000
        print(f"  {r['method']:<15} → {est:.0f}초 ({est/60:.1f}분)")

    # 결과 저장
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = {
        "experiment_date": ts,
        "article_count": len(texts),
        "results": [{k: v for k, v in r.items() if k != "embeddings"}
                     for r in results if r],
    }

    def convert(obj):
        if isinstance(obj, (np.integer,)): return int(obj)
        if isinstance(obj, (np.floating,)): return float(obj)
        if isinstance(obj, np.ndarray): return obj.tolist()
        if isinstance(obj, tuple): return list(obj)
        return obj

    output_file = RESULTS_DIR / f"onnx_quantization_comparison_{ts}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2, default=convert)
    print(f"\n결과 저장: {output_file}")


if __name__ == "__main__":
    main()
