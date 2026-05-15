"""
통합 브리핑 팟캐스트 대본 테스트 유틸 (faster-whisper + G-Eval).

===============================================================================
왜 이 파일이 필요한가
===============================================================================
NotebookLM 이 우리 대본(PRIMARY)을 얼마나 충실히 살려서 오디오로 재현했는지,
톤·구조·팩트가 방송 품질에 부합하는지를 **수동으로 빠르게 측정** 하기 위한 도구.

기존 `test/transcribe_podcasts.py` 는 구 A/B/C 실험 전용(경제 카테고리,
`method*.mp3` glob) 이라 통합 브리핑 구조에선 못 씀. 그걸 대체.

운영 파이프라인에는 통합 안 됨 — 이건 **개발자 수동 점검용 CLI**.
주기적 감사 (W2, 주 1회 샘플) 는 별도로 스케줄러 job 으로 추가 예정.

===============================================================================
사용법
===============================================================================

최근 팟캐스트 자동 감지 + 같은 시각에 만들어진 대본·소스 자동 결합:

    cd backend_v2_supabase
    python -X utf8 -m test.transcribe_and_evaluate

명시적 지정:

    python -X utf8 -m test.transcribe_and_evaluate \
        --mp3 outputs/podcast_오후_podcast_20260419_205528.mp3 \
        --script outputs/scripts/briefing_PM_2026-04-19_205528.txt \
        --date 2026-04-19 --slot PM

옵션:
    --mp3 PATH         MP3 경로 (기본: outputs/podcast_*.mp3 중 최신)
    --script PATH      대본 텍스트 (기본: MP3 timestamp 에 매칭되는 briefing_*.txt)
    --date YYYY-MM-DD  source article 조회용 KST 날짜 (기본: MP3 filename 에서 추출)
    --slot AM|PM       source article 조회용 slot (기본: MP3 filename 에서 추출)
    --model SIZE       faster-whisper 모델 크기 (기본: large-v3)
                       ※ turbo 는 한국어 고유명사·소수점 오탐이 심해 금지.
                         2026-04-21 실측에서 turbo 가 진짜 TTS 오류 19건 + 자기 오탐 10건
                         혼합을 만들어 listenability 평가를 왜곡시킴. large-v3 전용.
    --no-eval          전사만, G-Eval 건너뜀 (빠른 사본 확인용)
    --save             결과 JSON 저장 (기본 True; test/results/podcast_eval_{ts}.json)
===============================================================================
"""

import argparse
import json
import logging
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)
for _noisy in ("httpx", "httpcore", "hpack", "urllib3", "faster_whisper"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)


OUTPUTS_DIR = Path(__file__).parent.parent / "outputs"
SCRIPTS_DIR = OUTPUTS_DIR / "scripts"
RESULTS_DIR = Path(__file__).parent / "results"

HARD_NEWS_EN = ["politics", "economy", "international"]


# ──────────────────────────────────────────────
# 파일 자동 감지
# ──────────────────────────────────────────────

def find_latest_mp3() -> Optional[Path]:
    """outputs/ 에서 가장 최근 팟캐스트 MP3 찾기."""
    candidates = sorted(
        OUTPUTS_DIR.glob("podcast_*.mp3"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def parse_mp3_filename(mp3_path: Path) -> Dict[str, Optional[str]]:
    """MP3 파일명에서 time_slot·timestamp 추정.

    scheduler 가 쓰는 포맷: `podcast_{time_slot_ko}_podcast_{YYYYMMDD_HHMMSS}.mp3`
    예: `podcast_오후_podcast_20260419_205528.mp3` → slot=PM, ts=20260419_205528
    """
    name = mp3_path.stem
    m = re.search(r"podcast_(오전|오후)_.*?(\d{8})_(\d{6})", name)
    if not m:
        return {"slot": None, "date": None, "ts": None}
    slot_ko, yyyymmdd, hhmmss = m.group(1), m.group(2), m.group(3)
    slot = "AM" if slot_ko == "오전" else "PM"
    date_iso = f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:8]}"
    return {"slot": slot, "date": date_iso, "ts": f"{yyyymmdd}_{hhmmss}"}


def find_matching_script(meta: Dict[str, Optional[str]]) -> Optional[Path]:
    """MP3 의 timestamp 와 가장 가까운 briefing_{slot}_{date}_{HHMMSS}.txt 찾기.

    scheduler 가 쓰는 포맷: `briefing_{AM|PM}_{YYYY-MM-DD}_{HHMMSS}.txt`
    """
    slot = meta.get("slot")
    date = meta.get("date")
    if not slot or not date:
        return None
    candidates = sorted(
        SCRIPTS_DIR.glob(f"briefing_{slot}_{date}_*.txt"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def load_source_articles_from_supabase(
    date_str: str, slot: str
) -> List[Dict]:
    """Supabase news_cards 에서 해당 (date, slot) 의 하드뉴스 대표 기사들 로드.

    정확히 NotebookLM 에 들어간 27 REF 와 동일하진 않지만(news_cards 는 top 20/
    카테고리), fidelity 평가에 충분한 근사. 시간 제약상 실측 프록시로 사용.
    """
    try:
        from app.utils.supabase_client import get_supabase
    except Exception as e:
        logger.warning(f"  ⚠️ Supabase 클라이언트 로드 실패: {e} — source 없이 진행")
        return []

    try:
        sb = get_supabase()
        res = (
            sb.table("news_cards")
            .select("title,content,provider,hilight,category,rank")
            .eq("date", date_str)
            .eq("slot", slot)
            .in_("category", HARD_NEWS_EN)
            .order("category")
            .order("rank")
            .execute()
        )
        articles = []
        for row in (res.data or []):
            articles.append({
                "title": row.get("title", ""),
                "content": row.get("content") or row.get("hilight") or "",
                "provider": row.get("provider", ""),
                "press": row.get("provider", ""),
                "lede": row.get("hilight", ""),
            })
        logger.info(
            f"  📚 Supabase news_cards 로드: {len(articles)}건 "
            f"(하드뉴스 {HARD_NEWS_EN}, date={date_str}, slot={slot})"
        )
        return articles
    except Exception as e:
        logger.warning(f"  ⚠️ news_cards 조회 실패: {e} — source 없이 진행")
        return []


# ──────────────────────────────────────────────
# 전사
# ──────────────────────────────────────────────

def transcribe(path: Path, model_size: str = "turbo") -> Dict:
    """faster-whisper 로 MP3 → 한국어 전사. GPU 우선, 실패 시 CPU fallback."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        logger.error(
            "❌ faster-whisper 미설치. `pip install faster-whisper` 실행하세요."
        )
        sys.exit(1)

    logger.info(f"🎙️ 전사 시작: {path.name} (model={model_size})")
    t0 = time.time()

    try:
        model = WhisperModel(model_size, device="cuda", compute_type="float16")
        device_used = "cuda/float16"
    except Exception as e_cuda:
        logger.warning(f"  CUDA 로딩 실패({e_cuda.__class__.__name__}) → CPU fallback")
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        device_used = "cpu/int8"
    load_time = time.time() - t0
    logger.info(f"  모델 로드: {load_time:.1f}초 ({device_used})")

    t0 = time.time()
    segments, info = model.transcribe(
        str(path),
        language="ko",
        beam_size=5,
        word_timestamps=False,
    )
    full = [seg.text.strip() for seg in segments]
    text = "\n".join(full)
    transcribe_time = time.time() - t0

    logger.info(
        f"  전사 완료: {len(text)}자, 오디오 {info.duration:.1f}초 "
        f"({info.duration/60:.1f}분), 전사 소요 {transcribe_time:.1f}초"
    )

    return {
        "file": str(path),
        "text": text,
        "duration_sec": round(info.duration, 1),
        "char_count": len(text),
        "transcribe_sec": round(transcribe_time, 1),
        "device": device_used,
    }


# ──────────────────────────────────────────────
# main
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="통합 브리핑 팟캐스트 대본 테스트 (Whisper 전사 + G-Eval)"
    )
    parser.add_argument("--mp3", help="MP3 경로 (기본: outputs/podcast_*.mp3 중 최신)")
    parser.add_argument("--script", help="대본 텍스트 경로 (기본: MP3 timestamp 로 자동 매칭)")
    parser.add_argument("--date", help="source article 조회용 KST 날짜 YYYY-MM-DD")
    parser.add_argument("--slot", choices=["AM", "PM"], help="source article 조회용 slot")
    parser.add_argument(
        "--model",
        default="large-v3",
        help="faster-whisper 모델 크기 (기본: large-v3 — turbo 금지)",
    )
    parser.add_argument(
        "--no-eval", action="store_true", help="전사만, G-Eval 건너뜀"
    )
    parser.add_argument(
        "--save", action="store_true", default=True,
        help="결과 JSON 저장 (기본 True)",
    )
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("  통합 브리핑 팟캐스트 대본 테스트")
    logger.info("=" * 70)

    # ── 1. MP3 선택 ──
    mp3 = Path(args.mp3) if args.mp3 else find_latest_mp3()
    if mp3 is None or not mp3.exists():
        logger.error(f"❌ MP3 를 찾을 수 없습니다: {args.mp3 or '(자동 감지 실패)'}")
        sys.exit(1)
    logger.info(f"🎧 MP3: {mp3.name} ({mp3.stat().st_size/1_000_000:.1f} MB)")

    meta = parse_mp3_filename(mp3)
    logger.info(f"  파일명 메타: slot={meta['slot']}, date={meta['date']}, ts={meta['ts']}")

    # ── 2. 대본 자동 매칭 ──
    if args.script:
        script_path = Path(args.script)
    else:
        script_path = find_matching_script(meta)
    reference_script = None
    if script_path and script_path.exists():
        reference_script = script_path.read_text(encoding="utf-8")
        logger.info(
            f"📝 대본: {script_path.name} ({len(reference_script)}자)"
        )
    else:
        logger.info("📝 대본: (없음) — Script Adherence 차원은 N/A")

    # ── 3. 소스 기사 로드 (Supabase) ──
    date_str = args.date or meta["date"]
    slot = args.slot or meta["slot"]
    source_articles: List[Dict] = []
    if date_str and slot and not args.no_eval:
        source_articles = load_source_articles_from_supabase(date_str, slot)

    # ── 4. 전사 ──
    trans = transcribe(mp3, model_size=args.model)
    logger.info("\n--- 전사본 프리뷰 (첫 600자) ---")
    logger.info(trans["text"][:600])

    # ── 5. 평가 ──
    eval_result = None
    if not args.no_eval:
        if not source_articles and not reference_script:
            logger.warning(
                "⚠️ source 도 script 도 없음 — G-Eval 의미 없음, 생략. "
                "--date/--slot 주거나 --script 명시하세요."
            )
        else:
            logger.info("\n" + "=" * 70)
            logger.info("  📊 G-Eval 평가 시작")
            logger.info("=" * 70)
            try:
                from app.services.podcast_eval_service import (
                    evaluate_podcast_transcript,
                    format_podcast_eval_report,
                )
                eval_result = evaluate_podcast_transcript(
                    transcript=trans["text"],
                    source_articles=source_articles,
                    reference_script=reference_script,
                )
                if eval_result:
                    report = format_podcast_eval_report(eval_result)
                    logger.info("\n" + report)
            except Exception as e:
                logger.exception(f"❌ 평가 실패: {e}")

    # ── 6. 결과 저장 ──
    if args.save:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = RESULTS_DIR / f"podcast_eval_{ts}.json"
        payload = {
            "mp3_file": str(mp3),
            "mp3_meta": meta,
            "script_file": str(script_path) if script_path else None,
            "date_queried": date_str,
            "slot_queried": slot,
            "source_articles_count": len(source_articles),
            "transcript": {k: v for k, v in trans.items() if k != "text"},
            "transcript_text": trans["text"],
            "evaluation": eval_result,
        }
        out_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info(f"\n💾 결과 저장: {out_path}")

        # 전사본도 별도 .txt 로 (바로 읽기 편하게)
        txt_path = RESULTS_DIR / f"{mp3.stem}_transcript.txt"
        txt_path.write_text(trans["text"], encoding="utf-8")
        logger.info(f"💾 전사본 저장: {txt_path}")


if __name__ == "__main__":
    main()
