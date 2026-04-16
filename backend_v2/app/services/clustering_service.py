"""
클러스터링 서비스

UMAP 차원 축소 + HDBSCAN 밀도 기반 클러스터링.
동적 mcs + 거대 클러스터 fallback 포함.

파이프라인:
  1. Near-Duplicate 제거 (cosine > 0.95)
  2. UMAP 15d 축소
  3. HDBSCAN (동적 mcs)
  4. 거대 클러스터 감지 시 UMAP 25d 재시도
  5. 토픽 랭킹 & 대표 기사 선정 (가중 점수 기반)
"""

import re
import time
import logging
from collections import Counter
from typing import List, Dict, Tuple, Set, Optional

import numpy as np
import umap
import hdbscan
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# 거대 클러스터 판정 비율
GIANT_CLUSTER_RATIO = 0.30


# ──────────────────────────────────────────────
# 0. 키워드 추출 (Phase 2: 토픽 랭킹용)
# ──────────────────────────────────────────────

# 한국 뉴스에서 흔히 등장하지만 토픽 식별에 도움이 되지 않는 불용어.
# 너무 일반적인 단어를 거르는 용도. 토픽-키워드 유니크성이 핵심이기 때문에
# 카테고리 이름(경제, 정치 등)도 포함해서 카테고리 내에서 signal 이 되는
# 단어만 남기도록 한다.
STOP_WORDS: Set[str] = {
    # 시제 / 범위
    "오늘", "어제", "내일", "올해", "작년", "내년", "지난해", "최근",
    "지난", "이번", "요즘", "현재", "향후", "당분간", "이후", "이전",
    "지금", "그동안", "동안", "이날", "그날", "당일", "전날", "다음",
    # 지시/대명사
    "우리", "자신", "본인", "대상", "사람", "관련", "해당", "각자",
    "일부", "전체", "모두", "모든", "각각",
    # 언론/보도
    "기자", "뉴스", "속보", "단독", "종합", "특집", "기사", "보도",
    "인터뷰", "취재", "논평", "사설", "오피니언",
    # 카테고리명
    "경제", "정치", "사회", "문화", "국제", "스포츠", "연예",
    # 추상 명사
    "내용", "결과", "상황", "경우", "부분", "수준", "상태", "정도",
    "때문", "이유", "문제", "사항", "조치", "계획", "방안", "대책",
    "가능", "필요", "중요", "확인", "공개", "발표", "진행", "추진",
    "논의", "검토", "예정", "전망", "분석", "설명", "강조", "지적",
    # 형식 명사
    "대한", "위한", "통한", "대해", "위해", "통해", "보다", "이상",
    "이하", "정도", "약간", "전후", "내외",
    # 기타
    "하나", "가운데", "중에서", "중심", "기준", "방식", "방법",
    "자리", "만큼", "뿐만",
    # Okt 오태깅으로 Noun 으로 찍히는 흔한 동사/형용사 어간
    "있다", "없다", "되다", "하다", "이다", "있는", "없는", "되는",
    "하는", "이라", "라고", "라며", "라는", "이라고", "이라며",
    # 너무 일반적인 형용사/부사
    "많은", "적은", "새로운", "주요", "특히", "또한", "따라서",
    "그러나", "하지만", "한편", "이어", "여러", "일단", "먼저",
    # 카테고리 내부에서 너무 자주 등장해 토픽 시그널이 안 되는 단어
    "브랜드", "상품", "제품", "시장", "기업", "소비", "소비자",
    "가격", "지원", "정책", "업계",
}

# 숫자 + 한글 1~2자 단위(고유가, 기준금리 등)는 Okt 가 잘못 쪼개는 경우가 많아
# 원문에서 통째로 뽑도록 보조 정규식을 둔다.
COMPOUND_WORD_PATTERN = re.compile(
    r"[가-힣A-Za-z]{2,6}(?:가|세|값|율|률|권|비|료|원|주|금|업|국|안|론|파|안|책)?"
)

# 영어 대문자 약어(SKT, GPU, AI 등)
ENGLISH_ACRONYM_PATTERN = re.compile(r"\b[A-Z]{2,6}\b")

# Okt 인스턴스는 JVM 부팅이 무거워서 모듈 최초 호출 시 한 번만 만든다.
_OKT_INSTANCE = None


def _get_okt():
    """Okt 인스턴스를 lazy 하게 반환. konlpy 가 없으면 None."""
    global _OKT_INSTANCE
    if _OKT_INSTANCE is not None:
        return _OKT_INSTANCE
    try:
        from konlpy.tag import Okt  # type: ignore
        _OKT_INSTANCE = Okt()
        logger.info("  ✅ KoNLPy Okt 형태소 분석기 로드 완료")
    except Exception as e:
        logger.warning(
            f"  ⚠️ KoNLPy 로드 실패 ({e}). 키워드 추출이 fallback 으로 동작합니다."
        )
        _OKT_INSTANCE = False  # 재시도 방지
    return _OKT_INSTANCE or None


def _tokenize_text(text: str) -> List[str]:
    """
    하나의 텍스트에서 토픽 후보가 될 수 있는 토큰을 뽑는다.

    하이브리드 전략:
      1. Okt.pos() 에서 Noun + Alpha 태그만 필터링 (2~6자)
      2. 정규식으로 영어 약어(GPU, SKT 등)와 한글 복합어(고유가, 기준금리 등) 보강
      3. 불용어 제거
    """
    if not text:
        return []

    tokens: List[str] = []

    okt = _get_okt()
    if okt is not None:
        try:
            for word, tag in okt.pos(text, norm=False, stem=False):
                if tag in ("Noun", "Alpha") and 2 <= len(word) <= 6:
                    tokens.append(word)
        except Exception as e:
            logger.debug(f"Okt pos 실패: {e}")

    # 영어 약어는 항상 보강 (Okt 가 소문자로 떨어뜨릴 수 있음)
    tokens.extend(ENGLISH_ACRONYM_PATTERN.findall(text))

    # 한글 복합어 보강 — 숫자+단위 명사나 "고유가" 같은 표현을 잡기 위함
    for match in COMPOUND_WORD_PATTERN.findall(text):
        if 2 <= len(match) <= 6 and any("가" <= ch <= "힣" for ch in match):
            tokens.append(match)

    # 불용어/숫자-단독 제거 + lower casing (영어 약어는 그대로)
    cleaned: List[str] = []
    for tok in tokens:
        if tok in STOP_WORDS:
            continue
        if tok.isdigit():
            continue
        cleaned.append(tok)

    return cleaned


def extract_topic_keywords(
    cluster_members: List[int],
    articles: List[Dict],
    top_k: int = 5,
    title_weight: int = 3,
) -> List[Tuple[str, int]]:
    """
    클러스터의 기사들에서 대표 키워드 top_k 개를 추출한다.

    제목은 일반적으로 요지가 더 잘 드러나므로 title_weight 만큼 가중치를 준다.
    본문은 너무 길면 Okt 호출 비용이 폭발하므로 앞쪽 600자만 사용.

    Args:
        cluster_members: 기사 글로벌 인덱스 리스트
        articles: 전체 기사 리스트
        top_k: 반환할 키워드 수
        title_weight: 제목 토큰에 곱해줄 가중치

    Returns:
        [(키워드, 가중 빈도), ...] — 빈도 내림차순
    """
    counter: Counter = Counter()

    for idx in cluster_members:
        if idx >= len(articles):
            continue
        art = articles[idx]
        title = art.get("title", "") or ""
        content = (art.get("content", "") or "")[:600]

        title_tokens = _tokenize_text(title)
        content_tokens = _tokenize_text(content)

        for tok in title_tokens:
            counter[tok] += title_weight
        for tok in content_tokens:
            counter[tok] += 1

    return counter.most_common(top_k)


# ──────────────────────────────────────────────
# 0-b. 토픽 품질 지표 (corpus coverage, press diversity)
# ──────────────────────────────────────────────

def compute_corpus_coverage(
    keywords: List[Tuple[str, int]],
    category_articles: List[Dict],
    cluster_size: int,
    max_keywords: int = 3,
) -> float:
    """
    토픽의 키워드가 카테고리 전체 기사 안에서 차지하는 "무게" 를 계산한다.

    핵심 아이디어:
      - 클러스터 안에서만 많이 등장하는 키워드는 의미가 작다 (local 인기)
      - 카테고리 전체 기사 중 상당수가 같은 키워드를 언급한다면 그 토픽은
        실제로 "그날의 핵심 이슈" 이다

    점수는 [0, 1] 구간으로 정규화:
      - 상위 max_keywords 개 키워드의 외부(클러스터 밖) coverage 평균을 구하고
      - 15% 를 만점으로 간주해 min(coverage / 0.15, 1.0) 로 스케일

    Args:
        keywords: extract_topic_keywords 결과
        category_articles: 해당 카테고리의 전체 기사 리스트
        cluster_size: 이 클러스터 크기 (자기 자신의 기여를 뺄 때 사용)
        max_keywords: 점수 계산에 쓸 상위 키워드 수

    Returns:
        0.0 ~ 1.0 사이 점수
    """
    if not keywords or not category_articles:
        return 0.0

    n_total = len(category_articles)
    if n_total <= cluster_size:
        return 0.0

    top = keywords[:max_keywords]
    coverages: List[float] = []

    # 각 기사의 title + content(앞 400자) 를 한 번씩 읽어 매칭 여부 판정
    haystacks = [
        ((a.get("title") or "") + " " + (a.get("content") or "")[:400])
        for a in category_articles
    ]

    for kw, _ in top:
        hits = sum(1 for h in haystacks if kw in h)
        # 클러스터 내부 기사가 hits 에 포함되어 있으므로 최소 cluster_size 만큼은
        # 토픽 자기 자신 기여분이다. 엄밀하진 않지만 self-inflation 을 낮춰준다.
        external_hits = max(hits - cluster_size, 0)
        denom = max(n_total - cluster_size, 1)
        coverages.append(external_hits / denom)

    raw = float(np.mean(coverages)) if coverages else 0.0
    # 15% 커버리지를 1.0 으로 스케일
    return min(raw / 0.15, 1.0)


def _get_article_press(article: Dict) -> str:
    """기사 dict 에서 언론사 필드를 뽑는다.

    데이터 소스에 따라 `press` 또는 `provider` 키를 쓰기 때문에 둘 다 본다.
    """
    return (
        (article.get("press") or article.get("provider") or "").strip()
    )


def compute_press_diversity(
    cluster_members: List[int],
    articles: List[Dict],
    saturation: int = 10,
) -> float:
    """
    한 토픽이 여러 언론사에서 동시에 다뤄지고 있는지를 본다.

    동일한 프레스 하나가 같은 주제로 3~4건 연달아 쓴다면 "국지적 관심" 이고,
    여러 언론사가 함께 쓰면 "광역 이슈" 이다. 광역 이슈일수록 팟캐스트 커버
    가치가 높다.

    점수: unique_presses / saturation, 최대 1.0
    """
    if not cluster_members:
        return 0.0
    presses = {
        _get_article_press(articles[i])
        for i in cluster_members
        if i < len(articles)
    }
    presses.discard("")
    if not presses:
        return 0.0
    return min(len(presses) / saturation, 1.0)


# ──────────────────────────────────────────────
# 1. Near-Duplicate 제거
# ──────────────────────────────────────────────

def remove_near_duplicates(
    embeddings: np.ndarray,
    threshold: float = 0.95,
) -> np.ndarray:
    """
    cosine 유사도가 threshold 이상인 중복 기사를 제거합니다.

    Args:
        embeddings: (n, dim) 임베딩 배열
        threshold: 중복 판정 임계값

    Returns:
        유지할 인덱스 배열
    """
    n = len(embeddings)
    if n <= 1:
        return np.arange(n)

    # 정규화
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    normalized = embeddings / norms

    # 유사도 행렬
    sim_matrix = np.dot(normalized, normalized.T)

    # 중복 제거 (앞쪽 기사 우선 유지)
    removed = set()
    for i in range(n):
        if i in removed:
            continue
        for j in range(i + 1, n):
            if j in removed:
                continue
            if sim_matrix[i, j] >= threshold:
                removed.add(j)

    keep = np.array([i for i in range(n) if i not in removed])
    logger.info(
        f"  Near-dup 제거: {n}건 → {len(keep)}건 ({len(removed)}건 제거)"
    )
    return keep


# ──────────────────────────────────────────────
# 2. UMAP + HDBSCAN 클러스터링
# ──────────────────────────────────────────────

def _run_umap_hdbscan(
    embeddings: np.ndarray,
    umap_dim: int,
    mcs: int,
) -> Tuple[np.ndarray, Dict[int, List[int]], Dict]:
    """UMAP + HDBSCAN 실행 (내부 함수)"""

    # UMAP
    reducer = umap.UMAP(
        n_components=umap_dim,
        n_neighbors=15,
        min_dist=0.0,
        metric="cosine",
        random_state=42,
    )
    reduced = reducer.fit_transform(embeddings)

    # HDBSCAN (precomputed 코사인 거리)
    normalized = reduced.astype(np.float64)
    norms = np.linalg.norm(normalized, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    normalized = normalized / norms
    distance_matrix = 1.0 - np.clip(np.dot(normalized, normalized.T), -1, 1)

    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=mcs,
        metric="precomputed",
        cluster_selection_method="eom",
    )
    labels = clusterer.fit_predict(distance_matrix)

    # 클러스터 딕셔너리 (크기 내림차순)
    clusters_raw = {}
    for idx, label in enumerate(labels):
        if label == -1:
            continue
        if label not in clusters_raw:
            clusters_raw[label] = []
        clusters_raw[label].append(idx)

    sorted_clusters = sorted(
        clusters_raw.items(), key=lambda x: len(x[1]), reverse=True
    )
    clusters = {i: members for i, (_, members) in enumerate(sorted_clusters)}

    # 레이블 재매핑
    label_map = {
        old_id: new_id
        for new_id, (old_id, _) in enumerate(sorted_clusters)
    }
    final_labels = np.full(len(labels), -1, dtype=int)
    for idx, label in enumerate(labels):
        if label != -1:
            final_labels[idx] = label_map[label]

    sizes = [len(m) for m in clusters.values()]
    noise = int(np.sum(final_labels == -1))

    info = {
        "n_clusters": len(clusters),
        "noise_count": noise,
        "noise_ratio": noise / len(labels) if len(labels) > 0 else 0,
        "cluster_sizes": sizes,
        "max_cluster_size": max(sizes) if sizes else 0,
        "umap_dim": umap_dim,
        "mcs": mcs,
    }

    return final_labels, clusters, info


def cluster_articles(
    embeddings: np.ndarray,
    n_articles: int = None,
) -> Tuple[np.ndarray, Dict[int, List[int]], Dict]:
    """
    기사 임베딩을 클러스터링합니다.

    동적 mcs + 거대 클러스터 fallback 포함.

    Args:
        embeddings: (n, dim) 임베딩 배열
        n_articles: 기사 수 (동적 mcs 계산용. None이면 len(embeddings))

    Returns:
        labels: 클러스터 레이블 (노이즈=-1)
        clusters: {cluster_id: [article_indices]}
        info: 클러스터링 메타정보
    """
    n = n_articles or len(embeddings)
    mcs = max(3, n // 80)

    logger.info(f"  클러스터링 시작: {len(embeddings)}건, 동적 mcs={mcs}")
    t0 = time.time()

    # 1차 시도: UMAP 15d
    labels, clusters, info = _run_umap_hdbscan(embeddings, umap_dim=15, mcs=mcs)
    info["attempt"] = 1

    logger.info(
        f"  1차 결과: {info['n_clusters']}개 클러스터, "
        f"노이즈 {info['noise_ratio']:.1%}, "
        f"최대 크기 {info['max_cluster_size']}"
    )

    # 거대 클러스터 감지 → fallback
    if (
        info["max_cluster_size"] > 0
        and info["max_cluster_size"] / len(embeddings) > GIANT_CLUSTER_RATIO
    ):
        logger.warning(
            f"  ⚠️ 거대 클러스터 감지 "
            f"({info['max_cluster_size']}/{len(embeddings)} = "
            f"{info['max_cluster_size']/len(embeddings):.0%}). "
            f"UMAP 25d로 재시도."
        )

        labels, clusters, info = _run_umap_hdbscan(
            embeddings, umap_dim=25, mcs=mcs
        )
        info["attempt"] = 2
        info["fallback_reason"] = "giant_cluster"

        logger.info(
            f"  2차 결과: {info['n_clusters']}개 클러스터, "
            f"노이즈 {info['noise_ratio']:.1%}, "
            f"최대 크기 {info['max_cluster_size']}"
        )

    info["elapsed_sec"] = time.time() - t0
    return labels, clusters, info


# ──────────────────────────────────────────────
# 3. 토픽 랭킹 & 대표 기사 선정
# ──────────────────────────────────────────────

def rank_topics(
    clusters: Dict[int, List[int]],
    articles: List[Dict],
    embeddings: np.ndarray,
    top_n: int = 8,
    articles_per_topic: int = 3,
    category_articles: Optional[List[Dict]] = None,
    use_weighted_score: bool = True,
    score_weights: Tuple[float, float, float] = (0.25, 0.60, 0.15),
) -> List[Dict]:
    """
    클러스터를 랭킹하고, 토픽당 대표 기사 + 다양한 관점 기사를 선정합니다.

    **Phase 2: 가중 점수 기반 랭킹**

    단순히 클러스터 크기만 쓰면, 비슷한 프레스에서 우르르 쓰는 국지 이슈가
    진짜 그날의 핵심 이슈(중동전, 유가)를 밀어내버리는 문제가 있다.
    이를 막기 위해 3가지 신호를 가중합하여 랭킹한다.

      score = w_size * size_score
            + w_corpus * corpus_score
            + w_diversity * diversity_score

      기본 가중치는 (0.25, 0.60, 0.15). 카테고리 전체 기사에 대한 coverage 를
      가장 크게 본다. 이는 "사람들이 오늘 뭘 많이 쓰고 있느냐" 를 직접 반영.

    선정 전략 (토픽당 articles_per_topic개):
      1. centroid 최근접 1개 (대표)
      2. 다른 언론사에서 centroid 최원거리 순 (관점 다양성)

    Args:
        clusters: {cluster_id: [article_indices]}
        articles: 클러스터링에 사용된 기사 리스트 (dedupe 후)
        embeddings: 임베딩 배열
        top_n: 선정할 토픽 수
        articles_per_topic: 토픽당 선정할 기사 수
        category_articles: 카테고리 전체 원본 기사 (corpus coverage 계산용).
                           None 이면 articles 로 대체.
        use_weighted_score: False 면 과거와 같이 size 기준으로 정렬
        score_weights: (size, corpus, diversity) 가중치

    Returns:
        토픽 리스트 (정렬된 순서)
    """
    topics: List[Dict] = []

    if not clusters:
        return topics

    # corpus coverage 계산용 — 기본값은 articles 그대로
    corpus_for_coverage = category_articles or articles

    # 크기 정규화를 위해 최대 클러스터 크기 선계산
    max_size = max(len(m) for m in clusters.values())

    # 1) 모든 클러스터에 대해 3가지 점수 계산 → 가중합 → 정렬
    scored: List[Tuple[float, int, List[int], Dict]] = []
    for cid, members in clusters.items():
        size_score = len(members) / max_size if max_size else 0.0

        if use_weighted_score:
            keywords = extract_topic_keywords(members, articles, top_k=5)
            corpus_score = compute_corpus_coverage(
                keywords, corpus_for_coverage, cluster_size=len(members)
            )
            diversity_score = compute_press_diversity(members, articles)
        else:
            keywords = []
            corpus_score = 0.0
            diversity_score = 0.0

        w_size, w_corpus, w_div = score_weights
        if use_weighted_score:
            total_score = (
                w_size * size_score
                + w_corpus * corpus_score
                + w_div * diversity_score
            )
        else:
            total_score = size_score  # 과거와 동일 동작

        score_detail = {
            "size_score": round(size_score, 3),
            "corpus_score": round(corpus_score, 3),
            "diversity_score": round(diversity_score, 3),
            "total_score": round(total_score, 3),
            "keywords": keywords,
        }
        scored.append((total_score, cid, members, score_detail))

    # 정렬 (점수 내림차순, 동점이면 크기 큰 순)
    scored.sort(key=lambda x: (x[0], len(x[2])), reverse=True)

    selected = scored[:top_n]

    # ── 로깅: 상위 토픽의 점수 breakdown 출력 ──
    if use_weighted_score and selected:
        logger.info("  📊 토픽 가중 점수 랭킹 (Phase 2)")
        for rank, (total, cid, members, detail) in enumerate(selected, start=1):
            kw_preview = ", ".join(
                f"{k}({c})" for k, c in detail["keywords"][:3]
            ) or "-"
            logger.info(
                f"    #{rank} size={len(members):3d}  "
                f"total={detail['total_score']:.3f}  "
                f"[size={detail['size_score']:.2f} "
                f"corpus={detail['corpus_score']:.2f} "
                f"div={detail['diversity_score']:.2f}]  "
                f"kw: {kw_preview}"
            )

    for rank, (total_score, cid, members, score_detail) in enumerate(selected):
        member_embeddings = embeddings[members]
        centroid = np.mean(member_embeddings, axis=0)

        # 정규화
        centroid_norm = centroid / (np.linalg.norm(centroid) or 1)
        member_norms = member_embeddings / (
            np.linalg.norm(member_embeddings, axis=1, keepdims=True) + 1e-9
        )

        similarities = np.dot(member_norms, centroid_norm)

        # 1. 대표 기사 (centroid 최근접)
        rep_local_idx = int(np.argmax(similarities))
        rep_idx = members[rep_local_idx]
        rep_press = _get_article_press(articles[rep_idx])

        selected_indices = [rep_idx]
        selected_presses = {rep_press}

        # 2. 다른 관점 기사 (다른 언론사, centroid에서 먼 순)
        # 유사도 오름차순 (centroid에서 먼 것 = 다른 관점)
        distant_order = np.argsort(similarities)

        for local_idx in distant_order:
            if len(selected_indices) >= articles_per_topic:
                break

            global_idx = members[local_idx]
            press = _get_article_press(articles[global_idx])

            # 이미 선정된 언론사 제외
            if press in selected_presses:
                continue

            selected_indices.append(global_idx)
            selected_presses.add(press)

        # 언론사 다양성이 부족하면 그냥 먼 순으로 채움
        if len(selected_indices) < articles_per_topic:
            for local_idx in distant_order:
                if len(selected_indices) >= articles_per_topic:
                    break
                global_idx = members[local_idx]
                if global_idx not in selected_indices:
                    selected_indices.append(global_idx)

        selected_articles = [articles[i] for i in selected_indices]

        topics.append({
            "topic_id": rank,
            "size": len(members),
            "representative_idx": rep_idx,
            "representative_article": articles[rep_idx],
            "selected_articles": selected_articles,
            "selected_indices": selected_indices,
            "selected_presses": list(selected_presses),
            "member_indices": members,
            "member_titles": [
                articles[i].get("title", "") for i in members[:10]
            ],
            # Phase 2: 가중 점수 세부
            "score_total": score_detail["total_score"],
            "score_breakdown": {
                "size": score_detail["size_score"],
                "corpus": score_detail["corpus_score"],
                "diversity": score_detail["diversity_score"],
            },
            "keywords": score_detail["keywords"],
        })

    return topics


# ──────────────────────────────────────────────
# 4. 토픽 기반 비례 샘플링 (GPT 대본 생성용 소스 풀)
# ──────────────────────────────────────────────

def build_topic_weighted_pool(
    topics: List[Dict],
    articles: List[Dict],
    embeddings: np.ndarray,
    target: int = 50,
    min_per_topic: int = 6,
) -> Tuple[List[Dict], List[Dict]]:
    """
    토픽 크기에 비례하여 카테고리 소스 풀을 구성합니다.

    배분 방식: Pure Proportional + Largest Remainder + Safety Floor
      1. 각 토픽의 이상적 배분: topic_size / total_topic_size * target
      2. 반올림(내림) 후 남은 잔여분은 largest remainder method로 분배
      3. 토픽별 최소 min_per_topic 보장 (해당 토픽 크기 내에서)
      4. 각 토픽 내에서는 centroid 최근접 순으로 선정

    Args:
        topics: rank_topics() 결과 (top_n개 토픽)
        articles: 원본 기사 리스트
        embeddings: 임베딩 배열 (articles와 인덱스 매칭)
        target: 풀의 목표 크기 (기본 50)
        min_per_topic: 토픽당 최소 배분 (기본 6, 토픽 크기보다 큰 경우 해당 토픽 크기로 clamp)

    Returns:
        (pool_articles, allocation_info)
          pool_articles: 선정된 기사 리스트 (총 <= target 개)
          allocation_info: 디버깅/로깅용 배분 정보
                [{"topic_id", "topic_size", "allocated", "selected_global_indices"}, ...]
    """
    if not topics:
        return [], []

    n_topics = len(topics)
    total_size = sum(len(t["member_indices"]) for t in topics)

    # Step 1: Pure proportional allocation (소수점까지)
    raw_allocations = [
        len(t["member_indices"]) / total_size * target
        for t in topics
    ]

    # Step 2: 내림 + 반올림 나머지 (Largest Remainder Method)
    floor_alloc = [int(x) for x in raw_allocations]
    remainders = [
        (raw - int_val, idx)
        for idx, (raw, int_val) in enumerate(zip(raw_allocations, floor_alloc))
    ]
    remainders.sort(reverse=True)  # 나머지가 큰 순으로

    remaining = target - sum(floor_alloc)
    for i in range(remaining):
        _, topic_idx = remainders[i % n_topics]
        floor_alloc[topic_idx] += 1

    # Step 3: min_per_topic 보장 (토픽 크기 내에서 clamp)
    allocations = []
    for i, topic in enumerate(topics):
        topic_size = len(topic["member_indices"])
        desired = max(floor_alloc[i], min_per_topic)
        actual = min(desired, topic_size)  # 토픽 크기 넘지 않음
        allocations.append(actual)

    # Step 4: 총합이 target을 초과하면 큰 토픽부터 깎음
    while sum(allocations) > target:
        # 가장 많이 할당된 토픽 중에서, 축소 후에도 floor 유지 가능한 것부터
        candidates = [
            (allocations[i], i) for i in range(n_topics)
            if allocations[i] > max(min_per_topic, 1)
        ]
        if not candidates:
            break
        candidates.sort(reverse=True)
        _, idx = candidates[0]
        allocations[idx] -= 1

    # Step 5: 각 토픽에서 centroid 최근접 순으로 기사 선정
    pool_articles = []
    allocation_info = []

    for topic, n_pick in zip(topics, allocations):
        members = topic["member_indices"]
        member_embeddings = embeddings[members]

        # centroid 계산
        centroid = np.mean(member_embeddings, axis=0)
        centroid_norm = centroid / (np.linalg.norm(centroid) or 1)

        # 각 member의 centroid 유사도
        member_norms = member_embeddings / (
            np.linalg.norm(member_embeddings, axis=1, keepdims=True) + 1e-9
        )
        similarities = np.dot(member_norms, centroid_norm)

        # centroid 최근접 순 정렬 (유사도 내림차순)
        sorted_local_idx = np.argsort(-similarities)
        selected_global = [
            members[int(local_idx)]
            for local_idx in sorted_local_idx[:n_pick]
        ]

        for gi in selected_global:
            pool_articles.append(articles[gi])

        allocation_info.append({
            "topic_id": topic.get("topic_id"),
            "topic_size": len(members),
            "allocated": n_pick,
            "selected_global_indices": selected_global,
        })

    return pool_articles, allocation_info
