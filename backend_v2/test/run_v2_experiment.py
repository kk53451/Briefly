"""
v2 instructions 실측 실험 (1회성)

목표:
  Phase 2 대본 (8차, Overall 4.0/5.0) + NotebookLM instructions v2 조합이
  실제 오디오 품질에 어떤 영향을 주는지 측정한다.

비교 기준 (4/14 실측):
  | 차원               | v1 baseline (B) |
  |--------------------|------------------|
  | source_fidelity    | 2/5              |
  | conversational_flow| 4/5              |
  | completeness       | 3/5              |
  | listenability      | 4/5              |
  | neutrality         | 4/5              |
  | engagement         | 4/5              |
  | script_adherence   | 2/5              |
  | **Overall**        | **3.3/5**        |

흐름:
  1. 8차 대본 로드
  2. NotebookLM B 방식 + instructions v2 로 오디오 생성 (약 15분)
  3. faster-whisper 로 전사 (약 1분)
  4. podcast_eval_service 로 채점 (약 1분)
  5. v1 baseline 과 차원별 delta 출력

사용:
    cd backend_v2
    python -m test.run_v2_experiment
"""

import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# 4/14 v1 baseline (고정, 읽기 전용)
# ──────────────────────────────────────────────
BASELINE_V1 = {
    "source_fidelity": 2,
    "conversational_flow": 4,
    "completeness": 3,
    "listenability": 4,
    "neutrality": 4,
    "engagement": 4,
    "script_adherence": 2,
    "overall_score": 3.3,
    "label": "B-v1 (4/14, pre-Phase-1 script + instructions v1)",
}


DATA_PATH = Path("../backend/test/data/news_2026-04-11.json")
CATEGORY_KO = "경제"
CATEGORY_EN = "economy"
RESULTS_DIR = Path("test/results")


def find_latest_script() -> Path:
    """
    test/results/ 에서 가장 최근 script_economy_openai_*.txt 파일을 찾는다.

    이렇게 하면 새 대본을 생성할 때마다 실험 스크립트를 손댈 필요가 없다.
    """
    candidates = sorted(
        RESULTS_DIR.glob("script_economy_openai_*.txt"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError(
            f"{RESULTS_DIR}/script_economy_openai_*.txt 파일이 없습니다. "
            "먼저 `python -m test.generate_fresh_script` 를 실행하세요."
        )
    return candidates[0]


def load_script(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_source_articles() -> list:
    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return [a for a in data["articles"] if a.get("category") == CATEGORY_EN]


def transcribe_mp3(mp3_path: str) -> dict:
    """faster-whisper turbo 로 전사."""
    from faster_whisper import WhisperModel

    logger.info(f"🎤 Whisper 전사 시작: {Path(mp3_path).name}")
    t0 = time.time()
    model = WhisperModel("turbo", device="cuda", compute_type="float16")
    logger.info(f"  모델 로드: {time.time() - t0:.1f}초")

    t0 = time.time()
    segments, info = model.transcribe(
        mp3_path,
        language="ko",
        beam_size=5,
        word_timestamps=False,
    )
    text = "\n".join(seg.text.strip() for seg in segments)
    elapsed = time.time() - t0

    logger.info(
        f"✅ 전사 완료: {len(text)}자, {info.duration:.0f}초 "
        f"({info.duration/60:.1f}분 오디오), 전사 {elapsed:.1f}초"
    )
    return {
        "text": text,
        "duration_sec": round(info.duration, 1),
        "char_count": len(text),
    }


def print_comparison(new_result: dict):
    """v1 baseline 과 dimension 별 비교."""
    from app.services.podcast_eval_service import format_podcast_eval_report

    print()
    print("=" * 72)
    print("  v1 baseline vs v2 실측 비교")
    print("=" * 72)

    rows = [
        ("source_fidelity",     "Source Fidelity   "),
        ("conversational_flow", "Conversational    "),
        ("completeness",        "Completeness      "),
        ("listenability",       "Listenability     "),
        ("neutrality",          "Neutrality        "),
        ("engagement",          "Engagement        "),
        ("script_adherence",    "Script Adherence  "),
    ]

    header = f"  {'차원':<20} {'v1 (기준)':>10} {'v2 (신규)':>10} {'Δ':>6}"
    print(header)
    print("  " + "-" * 50)
    for key, label in rows:
        v1 = BASELINE_V1.get(key)
        v2_dim = new_result.get(key, {})
        v2 = v2_dim.get("score") if isinstance(v2_dim, dict) else None

        v1_str = str(v1) if v1 is not None else "-"
        v2_str = str(v2) if v2 is not None else "-"
        if v1 is not None and v2 is not None:
            delta = v2 - v1
            delta_str = f"{delta:+d}"
        else:
            delta_str = "-"
        print(f"  {label:<20} {v1_str:>10} {v2_str:>10} {delta_str:>6}")

    v1_overall = BASELINE_V1["overall_score"]
    v2_overall = new_result.get("overall_score", "-")
    print("  " + "-" * 50)
    if isinstance(v2_overall, (int, float)):
        delta = v2_overall - v1_overall
        verdict_icon = "✅" if delta >= 0.5 else ("🟡" if delta > -0.3 else "❌")
        print(
            f"  {'Overall':<20} {v1_overall:>10.1f} {v2_overall:>10.1f} "
            f"{delta:>+6.1f}  {verdict_icon}"
        )
    else:
        print(f"  {'Overall':<20} {v1_overall:>10.1f} {'-':>10} {'-':>6}")

    # 판정
    print()
    if isinstance(v2_overall, (int, float)):
        delta = v2_overall - v1_overall
        if delta >= 0.5:
            print("  ✅ 판정: v2 instructions 강화가 유의미하게 작동함. 정식 채택 검토.")
        elif delta > -0.3:
            print("  🟡 판정: 노이즈 범위. 추가 1-2회 실험 필요.")
        else:
            print("  ❌ 판정: 악화. v1 롤백 검토.")
    print()

    # 상세 리포트도 출력
    print(format_podcast_eval_report(new_result, method="B-v2"))


def main():
    print("=" * 72)
    print("  v2.1 instructions 실측 실험")
    print(f"  시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 72)

    # ── 1. 최신 대본 자동 선택 ──
    script_path = find_latest_script()
    script = load_script(script_path)
    logger.info(f"📄 최신 대본 로드: {script_path.name} ({len(script)}자)")

    # ── 2. 소스 기사 로드 ──
    articles = load_source_articles()
    logger.info(f"📰 소스 기사 로드: {len(articles)}건 ({CATEGORY_EN})")

    # ── 3. NotebookLM 인증 확인 ──
    from app.services.notebooklm_service import check_auth, generate_podcast

    logger.info("🔐 NotebookLM 인증 확인...")
    if not check_auth():
        logger.error(
            "❌ NotebookLM 인증 만료 또는 파일 없음. "
            "먼저 'notebooklm login' 실행하세요."
        )
        sys.exit(1)
    logger.info("  ✅ 인증 OK")

    # ── 4. 오디오 생성 (B 방식 + v2 instructions) ──
    logger.info("🎙️ NotebookLM 오디오 생성 (B 방식 + v2 instructions)...")
    t0 = time.time()
    mp3_path = generate_podcast(
        topics=[],           # B 방식은 topics 불필요
        category_ko=CATEGORY_KO,
        script=script,
        method="B",
        instructions_version="v2",
        # time_slot=None → 현재 KST 기준 자동 (오전/오후)
    )
    if not mp3_path:
        logger.error("❌ 오디오 생성 실패")
        sys.exit(1)

    gen_elapsed = time.time() - t0
    logger.info(f"✅ 오디오 생성 완료: {mp3_path} ({gen_elapsed/60:.1f}분 소요)")

    # ── 5. Whisper 전사 ──
    transcript_data = transcribe_mp3(mp3_path)
    transcript_path = Path("test/results") / (Path(mp3_path).stem + "_transcript.txt")
    transcript_path.write_text(transcript_data["text"], encoding="utf-8")
    logger.info(f"💾 전사 저장: {transcript_path.name}")

    # ── 6. 평가 ──
    logger.info("📊 podcast_eval 평가 시작...")
    from app.services.podcast_eval_service import evaluate_podcast_transcript

    eval_result = evaluate_podcast_transcript(
        transcript=transcript_data["text"],
        source_articles=articles,
        reference_script=script,
        max_sources=60,
    )

    if not eval_result:
        logger.error("❌ 평가 실패")
        sys.exit(1)

    # ── 7. 결과 저장 ──
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_path = Path("test/results") / f"v2_experiment_{ts}.json"
    result_path.write_text(
        json.dumps({
            "timestamp": ts,
            "script_file": str(script_path.name),
            "mp3_file": str(Path(mp3_path).name),
            "transcript": transcript_data,
            "baseline_v1": BASELINE_V1,
            "evaluation_v2": eval_result,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info(f"💾 결과 저장: {result_path.name}")

    # ── 8. 비교 출력 ──
    print_comparison(eval_result)


if __name__ == "__main__":
    main()
