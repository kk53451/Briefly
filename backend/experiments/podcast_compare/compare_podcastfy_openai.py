"""
Podcastfy + OpenAI TTS 버전.

compare_podcastfy.py 와 동일한 입력/LLM 설정을 쓰되, TTS 만 ElevenLabs → OpenAI
로 교체. OpenAI TTS 는 GPT API 크레딧으로 과금되므로 ElevenLabs 유료 플랜이
없어도 동작합니다.

환경변수:
    OPENAI_API_KEY     (필수)

출력:
    outputs/podcastfy_openai_<category>_<timestamp>.mp3
"""

from __future__ import annotations

import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from _common import StopWatch, load_sample, out_path

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


def build_config() -> dict:
    """Podcastfy 한국어 설정 + OpenAI TTS.

    OpenAI TTS 가 지원하는 음성은 현재 alloy, echo, fable, onyx, nova, shimmer 등.
    청취 느낌 기준으로 onyx(남성 앵커) + nova(여성 해설) 조합 시도.
    """
    return {
        "output_language": "Korean",
        "podcast_name": "브리플리 뉴스",
        "podcast_tagline": "AI가 전하는 오늘의 뉴스",
        "conversation_style": ["professional", "informative", "engaging"],
        "roles_person1": "뉴스 앵커",
        "roles_person2": "해설 전문가",
        "creativity": 0.6,
        "word_count": 2500,
        "dialogue_structure": [
            "오프닝 인사",
            "오늘의 주요 뉴스 소개",
            "뉴스별 심층 토론",
            "마무리 및 클로징",
        ],
        "engagement_techniques": [
            "rhetorical questions",
            "expert analysis",
            "contextual commentary",
        ],
        "text_to_speech": {
            "default_tts_model": "openai",
            "openai": {
                "default_voices": {
                    "question": "onyx",  # Person1 (앵커)
                    "answer": "nova",    # Person2 (해설)
                },
                "model": "tts-1",  # 또는 "tts-1-hd" (품질↑, 비용 2배)
            },
            "audio_format": "mp3",
            "ending_message": "브리플리 뉴스였습니다. 내일 또 만나요.",
        },
    }


def main() -> int:
    try:
        from podcastfy.client import generate_podcast  # type: ignore
    except ImportError:
        print(
            "❌ podcastfy 가 설치되어 있지 않습니다. `pip install podcastfy` 후 다시 실행하세요.",
            file=sys.stderr,
        )
        return 1

    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY 가 설정되어 있지 않습니다.", file=sys.stderr)
        return 1

    sample = load_sample()
    text = sample.as_joined_text()
    config = build_config()
    config["user_instructions"] = (
        "경제 뉴스이므로 일반인도 이해하기 쉽게 설명하세요. "
        "전문 용어는 쉬운 말로 풀어서 설명해주세요."
    )

    print(f"🎙️ Podcastfy + OpenAI TTS 팟캐스트 생성 시작 (카테고리: {sample.category_ko})")
    print(f"   입력 기사 수: {len(sample.articles)}, 총 길이: {len(text)}자")
    print(f"   TTS: openai tts-1 (onyx / nova)")

    with StopWatch() as sw:
        audio_path_str = generate_podcast(
            text=text,
            llm_model_name="gpt-4o-mini",
            api_key_label="OPENAI_API_KEY",
            tts_model="openai",
            conversation_config=config,
        )

    src = Path(audio_path_str)
    if not src.exists():
        print(f"❌ Podcastfy 가 리턴한 경로에 파일이 없습니다: {src}", file=sys.stderr)
        return 2

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = out_path(f"podcastfy_openai_{sample.category}_{ts}.mp3")
    shutil.copy2(src, dst)

    log = out_path(f"podcastfy_openai_{sample.category}_{ts}.log.txt")
    log.write_text(
        f"engine: podcastfy + openai tts\n"
        f"category: {sample.category}\n"
        f"articles: {len(sample.articles)}\n"
        f"input_chars: {len(text)}\n"
        f"elapsed_sec: {sw.elapsed:.2f}\n"
        f"output: {dst.name}\n"
        f"podcastfy_raw_path: {src}\n",
        encoding="utf-8",
    )

    print(f"✅ 완료: {dst}  ({sw.elapsed:.1f}s)")
    print(f"   로그: {log}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
