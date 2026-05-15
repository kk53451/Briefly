"""
기존 대본을 그대로 써서 NotebookLM 오디오만 재생성 — 빠른 instructions 튜닝 루프.

===============================================================================
왜 이 파일이 필요한가
===============================================================================
Instructions 나 AudioLength 변경의 효과를 측정할 때 전체 파이프라인(수집→임베딩→
클러스터링→대본 생성→오디오)을 매번 돌리면 2시간씩 걸립니다. 대본·REF 는 동일
하게 두고 **NotebookLM 쪽 변화만 격리 측정** 하려면 이 스크립트를 쓰세요.

경로:
  1. `outputs/scripts/briefing_{slot}_{date}_{HHMMSS}.txt` — 기존 대본 로드
  2. Supabase `news_cards` 에서 해당 (date, slot) 하드뉴스 top-N REF 로드
     (원래 REF 27건과 정확히 같지 않지만 유사한 소재 — 길이·톤 측정엔 충분)
  3. `generate_podcast()` 재호출
  4. ffprobe 로 duration 측정 출력

사용:
  cd backend_v2_supabase
  # 최신 대본 자동 감지 + 동일 date/slot 로 재생성
  python -X utf8 -m test.regenerate_audio

  # 명시적 지정
  python -X utf8 -m test.regenerate_audio \\
      --script outputs/scripts/briefing_PM_2026-04-19_205528.txt \\
      --date 2026-04-19 --slot PM

옵션:
  --script PATH           대본 텍스트 경로 (기본: outputs/scripts/ 내 최신)
  --date YYYY-MM-DD       REF 소스 조회용 KST 날짜 (기본: 파일명 추출)
  --slot AM|PM            REF 소스 조회용 slot (기본: 파일명 추출)
  --refs-per-category N   카테고리당 REF 수 (기본: 9, 총 27건)
===============================================================================
"""

import argparse
import logging
import re
import subprocess
import sys
import time
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
for _noisy in ("httpx", "httpcore", "hpack", "urllib3"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)


SCRIPTS_DIR = Path(__file__).parent.parent / "outputs" / "scripts"
HARD_NEWS_EN = ["politics", "economy", "international"]
CAT_KO = {"politics": "정치", "economy": "경제", "international": "국제"}


def find_latest_script() -> Optional[Path]:
    candidates = sorted(
        SCRIPTS_DIR.glob("briefing_*.txt"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def parse_script_filename(path: Path) -> Dict[str, Optional[str]]:
    m = re.search(r"briefing_(AM|PM)_(\d{4}-\d{2}-\d{2})_", path.name)
    if not m:
        return {"slot": None, "date": None}
    return {"slot": m.group(1), "date": m.group(2)}


def load_refs(date_str: str, slot: str, per_category: int = 9) -> List[Dict]:
    from app.utils.supabase_client import get_supabase
    sb = get_supabase()
    all_refs: List[Dict] = []
    for cat_en in HARD_NEWS_EN:
        res = (
            sb.table("news_cards")
            .select("title,content,provider,hilight,rank")
            .eq("date", date_str)
            .eq("slot", slot)
            .eq("category", cat_en)
            .order("rank")
            .limit(per_category)
            .execute()
        )
        for row in (res.data or []):
            all_refs.append({
                "title": row.get("title", ""),
                "content": row.get("content") or row.get("hilight") or "",
                "press": row.get("provider", ""),
                "provider": row.get("provider", ""),
                "category_ko": CAT_KO[cat_en],
            })
    logger.info(
        f"  📚 REF 로드: 하드뉴스 {len(HARD_NEWS_EN)}카테 × 상위 {per_category}건 "
        f"= 총 {len(all_refs)}건"
    )
    return all_refs


def probe_duration(path: str) -> Optional[float]:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error",
             "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except Exception as e:
        logger.warning(f"ffprobe 실패: {e}")
    return None


def main():
    parser = argparse.ArgumentParser(
        description="대본 고정 + NotebookLM 오디오 재생성 (instructions 튜닝 루프)"
    )
    parser.add_argument("--script", help="대본 텍스트 경로")
    parser.add_argument("--date", help="REF 조회용 KST 날짜 YYYY-MM-DD")
    parser.add_argument("--slot", choices=["AM", "PM"])
    parser.add_argument("--refs-per-category", type=int, default=9)
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("  대본 고정 NotebookLM 오디오 재생성")
    logger.info("=" * 70)

    # 1. 대본 로드
    script_path = Path(args.script) if args.script else find_latest_script()
    if not script_path or not script_path.exists():
        logger.error(f"❌ 대본 파일 없음: {args.script or '(자동 감지 실패)'}")
        sys.exit(1)
    script = script_path.read_text(encoding="utf-8")
    logger.info(f"📝 대본: {script_path.name} ({len(script)}자)")

    meta = parse_script_filename(script_path)
    date_str = args.date or meta["date"]
    slot = args.slot or meta["slot"]
    if not date_str or not slot:
        logger.error(f"❌ date/slot 추출 실패 — --date --slot 명시하세요.")
        sys.exit(1)
    logger.info(f"  meta: date={date_str}, slot={slot}")

    # 2. REF 소스 로드
    refs = load_refs(date_str, slot, per_category=args.refs_per_category)

    # 3. NotebookLM 호출
    from app.services.notebooklm_service import (
        generate_podcast,
        probe_audio_duration_seconds,
        ensure_auth,
    )

    if not ensure_auth():
        logger.error("❌ NotebookLM 인증 실패 — `notebooklm login` 실행 필요")
        sys.exit(1)

    time_slot_ko = "오전" if slot == "AM" else "오후"
    logger.info(
        f"🎙️ NotebookLM 오디오 생성 시작 "
        f"(time_slot={time_slot_ko}, PRIMARY 1 + REF {len(refs)} = 총 {1+len(refs)}개)"
    )
    t0 = time.time()
    audio_path = generate_podcast(
        script=script,
        time_slot=time_slot_ko,
        reference_articles=refs,
        briefing_date=date_str,
    )
    elapsed = time.time() - t0

    if not audio_path:
        logger.error(f"❌ 오디오 생성 실패 ({elapsed:.0f}초)")
        sys.exit(1)

    # 4. 길이 측정
    duration_sec_probe = probe_audio_duration_seconds(audio_path)
    duration_sec_ffprobe = probe_duration(audio_path)

    logger.info("")
    logger.info("=" * 70)
    logger.info(f"✅ 생성 완료")
    logger.info(f"  audio_path: {audio_path}")
    logger.info(f"  총 소요: {elapsed:.0f}초 ({elapsed/60:.1f}분)")
    if duration_sec_probe:
        mm, ss = divmod(duration_sec_probe, 60)
        logger.info(
            f"  🕒 오디오 길이 (probe): {duration_sec_probe}초 "
            f"= {int(mm)}분 {int(ss)}초"
        )
    if duration_sec_ffprobe:
        mm = int(duration_sec_ffprobe // 60)
        ss = int(duration_sec_ffprobe % 60)
        logger.info(
            f"  🕒 오디오 길이 (ffprobe 직접): "
            f"{duration_sec_ffprobe:.1f}초 = {mm}분 {ss}초"
        )
    logger.info("=" * 70)

    # 5. 이전 실측(20분 39초) 대비 비교
    if duration_sec_ffprobe:
        delta = duration_sec_ffprobe - 1238.7
        sign = "▼" if delta < 0 else "▲"
        logger.info(
            f"  📉 이전 실측(20분 39초=1238.7초) 대비: "
            f"{sign} {abs(delta):.1f}초 ({delta/60:+.1f}분)"
        )
        target_lo, target_hi = 8 * 60, 10 * 60  # 8~10분 목표
        in_target = target_lo <= duration_sec_ffprobe <= target_hi
        logger.info(
            f"  🎯 타깃(8~10분) 내: "
            f"{'✅ 예' if in_target else '❌ 아니오'}"
        )


if __name__ == "__main__":
    main()
