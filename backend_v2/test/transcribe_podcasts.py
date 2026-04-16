"""
팟캐스트 MP3 → 텍스트 전사 (faster-whisper turbo)

A/B/C 방식으로 생성된 팟캐스트의 실제 대본을 추출합니다.

사용법:
    cd backend_v2
    python -m test.transcribe_podcasts
"""

import sys
import time
from pathlib import Path

OUTPUTS_DIR = Path(__file__).parent.parent / "outputs"
RESULTS_DIR = Path(__file__).parent / "results"


def transcribe_file(filepath: str, model_size: str = "turbo") -> dict:
    """MP3 파일을 텍스트로 전사합니다."""
    from faster_whisper import WhisperModel

    print(f"\n{'─'*50}")
    print(f"  전사 중: {Path(filepath).name}")
    print(f"  모델: {model_size}")
    print(f"{'─'*50}")

    t0 = time.time()
    model = WhisperModel(model_size, device="cuda", compute_type="float16")
    load_time = time.time() - t0
    print(f"  모델 로드: {load_time:.1f}초")

    t0 = time.time()
    segments, info = model.transcribe(
        filepath,
        language="ko",
        beam_size=5,
        word_timestamps=False,
    )

    # 세그먼트 수집
    full_text = []
    for segment in segments:
        full_text.append(segment.text.strip())

    transcribe_time = time.time() - t0
    text = "\n".join(full_text)

    print(f"  전사 완료: {len(text)}자 ({transcribe_time:.1f}초)")
    print(f"  오디오 길이: {info.duration:.1f}초 ({info.duration/60:.1f}분)")

    return {
        "file": str(filepath),
        "text": text,
        "duration_sec": round(info.duration, 1),
        "char_count": len(text),
        "transcribe_sec": round(transcribe_time, 1),
    }


def main():
    # A/B/C MP3 파일 찾기
    mp3_files = sorted(OUTPUTS_DIR.glob("podcast_경제_method*.mp3"))

    if not mp3_files:
        print("MP3 파일이 없습니다. A/B/C 실험을 먼저 실행하세요.")
        return

    print(f"{'='*50}")
    print(f"  팟캐스트 전사 (faster-whisper turbo, GPU)")
    print(f"  파일 {len(mp3_files)}개")
    print(f"{'='*50}")

    results = []
    for mp3 in mp3_files:
        result = transcribe_file(str(mp3))
        results.append(result)

        # 전사 결과 저장
        txt_name = mp3.stem + "_transcript.txt"
        txt_path = RESULTS_DIR / txt_name
        txt_path.write_text(result["text"], encoding="utf-8")
        print(f"  저장: {txt_path.name}")

    # 비교 출력
    print(f"\n\n{'='*70}")
    print(f"  A/B/C 전사 결과 비교")
    print(f"{'='*70}")

    for r in results:
        name = Path(r["file"]).stem
        method = "A" if "methodA" in name else "B" if "methodB" in name else "C"
        print(f"\n{'─'*60}")
        print(f"  방식 {method} | {r['duration_sec']}초 ({r['duration_sec']/60:.1f}분) | {r['char_count']}자")
        print(f"{'─'*60}")
        print(r["text"][:500])
        print("..." if len(r["text"]) > 500 else "")

    # G-Eval 팟캐스트 평가
    print(f"\n\n{'='*70}")
    print(f"  G-Eval 팟캐스트 품질 평가")
    print(f"{'='*70}")

    import json
    from dotenv import load_dotenv
    load_dotenv()

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from app.services.podcast_eval_service import evaluate_podcast_transcript, format_podcast_eval_report

    # 소스 기사 로드
    DATA_DIR = Path(__file__).parent.parent.parent / "backend" / "test" / "data"
    source_path = DATA_DIR / "news_2026-04-11.json"
    source_articles = []
    if source_path.exists():
        with open(source_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        source_articles = [a for a in data["articles"] if a.get("category") == "economy"]

    # 참조 대본 로드 (가장 최근)
    script_files = sorted(RESULTS_DIR.glob("script_economy_*.txt"), reverse=True)
    reference_script = None
    if script_files:
        reference_script = script_files[0].read_text(encoding="utf-8")

    eval_results = {}
    for r in results:
        name = Path(r["file"]).stem
        method = "A" if "methodA" in name else "B" if "methodB" in name else "C"

        # 방식 A는 참조 대본 없이 평가
        ref = reference_script if method in ("B", "C") else None

        eval_result = evaluate_podcast_transcript(
            transcript=r["text"],
            source_articles=source_articles,
            reference_script=ref,
        )

        if eval_result:
            eval_results[method] = eval_result
            report = format_podcast_eval_report(eval_result, method)
            print(f"\n{report}")

    # 비교 요약 테이블
    print(f"\n\n{'='*90}")
    print(f"{'METHOD':<8} {'OVERALL':>8} {'FIDELITY':>9} {'FLOW':>6} {'COMPLETE':>9} {'LISTEN':>7} {'NEUTRAL':>8} {'ENGAGE':>7} {'SCRIPT':>7} {'READY':>6}")
    print(f"{'='*90}")

    for method in ["A", "B", "C"]:
        e = eval_results.get(method, {})
        if not e:
            continue

        def s(dim):
            d = e.get(dim, {})
            score = d.get("score") if isinstance(d, dict) else None
            return str(score) if score is not None else "-"

        ready = "✅" if e.get("broadcast_ready") else "❌"
        overall = e.get('overall_score', '-')
        overall_str = f"{overall}" if overall is not None else "-"
        print(f"  {method:<6} {overall_str:>8} "
              f"{s('source_fidelity'):>9} {s('conversational_flow'):>6} "
              f"{s('completeness'):>9} {s('listenability'):>7} "
              f"{s('neutrality'):>8} {s('engagement'):>7} "
              f"{s('script_adherence'):>7} {ready:>6}")

    print(f"{'='*90}")

    # 결과 JSON 저장
    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    eval_output = RESULTS_DIR / f"podcast_eval_{ts}.json"
    with open(eval_output, "w", encoding="utf-8") as f:
        json.dump({
            "transcripts": {
                Path(r["file"]).stem: {k: v for k, v in r.items() if k != "text"}
                for r in results
            },
            "evaluations": eval_results,
        }, f, ensure_ascii=False, indent=2)
    print(f"\n평가 결과 저장: {eval_output}")


if __name__ == "__main__":
    main()
