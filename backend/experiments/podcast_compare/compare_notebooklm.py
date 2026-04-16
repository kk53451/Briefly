"""
notebooklm-py (비공식 Google NotebookLM 래퍼) 로 한국어 뉴스 팟캐스트 생성.

⚠️  Google 비공식 API. 프로덕션 사용 금지. 품질 비교 샘플 전용.

사전 준비:
    pip install notebooklm-py playwright
    python -m playwright install chromium
    notebooklm login       # 브라우저로 Google 로그인 (1회) → Enter 키

실행:
    cd backend/experiments/podcast_compare
    python compare_notebooklm.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from _common import StopWatch, load_sample, out_path

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


async def run() -> int:
    from notebooklm import DEFAULT_STORAGE_PATH, NotebookLMClient, AudioLength

    storage = Path(DEFAULT_STORAGE_PATH)
    if not storage.exists():
        print(
            f"❌ 인증 파일 없음: {storage}\n"
            "   먼저 `notebooklm login` 실행 후 Enter 키를 누르세요.",
            file=sys.stderr,
        )
        return 1

    sample = load_sample()
    language = os.getenv("NOTEBOOKLM_LANGUAGE", "ko")

    print(f"🎙️  NotebookLM (비공식) 팟캐스트 생성 시작")
    print(f"    카테고리: {sample.category_ko}")
    print(f"    입력 기사 수: {len(sample.articles)}")
    print(f"    언어: {language}")
    print(f"⚠️   프로덕션용 아님, 품질 비교 샘플 전용\n")

    instructions = (
        "이 소스들은 한국 경제 뉴스입니다. "
        "두 명의 진행자(앵커와 해설 전문가)가 자연스럽게 대화하는 형식으로, "
        "한국어로 쉽고 명확하게 전달해주세요. "
        "전문 용어는 풀어서 설명하고, 청취자가 지루하지 않게 진행해주세요."
    )

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = None

    async with await NotebookLMClient.from_storage() as client:
        nb = await client.notebooks.create(f"Briefly sample {sample.date} {ts}")
        print(f"📓 Notebook 생성: {nb.id}")

        source_ids: list[str] = []

        with StopWatch() as sw:
            try:
                # 소스 업로드
                print(f"📄 소스 업로드 중...")
                for idx, (title, content) in enumerate(sample.as_individual_sources(), start=1):
                    src = await client.sources.add_text(
                        nb.id, f"{idx}. {title}", content, wait=False
                    )
                    source_ids.append(src.id)
                    print(f"    [{idx}/{len(sample.articles)}] {title[:40]}")

                # 인덱싱 대기
                print(f"⏳ 소스 인덱싱 대기 중...")
                await client.sources.wait_for_sources(nb.id, source_ids, timeout=180.0)
                print(f"    인덱싱 완료")

                # 오디오 생성
                print(f"🎧 오디오 생성 요청 중 (language={language})...")
                status = await client.artifacts.generate_audio(
                    nb.id,
                    source_ids=source_ids,
                    language=language,
                    instructions=instructions,
                    audio_length=AudioLength.SHORT,  # SHORT=~5분, DEFAULT=~15분, LONG=~25분
                )
                print(f"    task_id: {status.task_id}")

                # 완료 대기 (수 분 소요)
                print(f"⏳ 생성 완료 대기 중 (최대 20분)...")
                await client.artifacts.wait_for_completion(
                    nb.id, status.task_id, timeout=1200.0
                )
                print(f"    생성 완료!")

                # 다운로드
                dst = out_path(f"notebooklm_{sample.category}_{ts}.mp3")
                print(f"⬇️  다운로드 중...")
                await client.artifacts.download_audio(nb.id, str(dst))

            finally:
                try:
                    await client.notebooks.delete(nb.id)
                    print(f"🗑️  Notebook 정리 완료")
                except Exception as e:
                    print(f"⚠️   Notebook 정리 실패 (무시): {e}")

    if dst and dst.exists():
        log = out_path(f"notebooklm_{sample.category}_{ts}.log.txt")
        log.write_text(
            f"engine: notebooklm-py (UNOFFICIAL)\n"
            f"version: 0.3.4\n"
            f"category: {sample.category}\n"
            f"articles: {len(sample.articles)}\n"
            f"language: {language}\n"
            f"elapsed_sec: {sw.elapsed:.2f}\n"
            f"output: {dst.name}\n",
            encoding="utf-8",
        )
        print(f"\n✅ 완료: {dst}  ({sw.elapsed:.1f}s)")
        print(f"   로그: {log}")
        return 0
    else:
        print(f"\n❌ 오디오 파일이 생성되지 않았습니다.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
