import asyncio
import base64
import os
import time
from pathlib import Path
from typing import Iterator

import backoff
from elevenlabs import Voice, VoiceSettings, save
from elevenlabs.client import ElevenLabs
from hume import AsyncHumeClient
from hume.tts import (
    PostedContextWithGenerationId,
    PostedUtterance,
    PostedUtteranceVoiceWithId,
)
from openai import APIError, OpenAI, RateLimitError
from pydub import AudioSegment

from neuralnoise.models import Speaker


def generate_audio_segment_elevenlabs(
    content: str,
    speaker: Speaker,
) -> bytes | Iterator[bytes]:
    client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

    voice_id = speaker.settings.voice_id
    voice_settings = (
        speaker.settings.voice_settings.model_dump()
        if speaker.settings.voice_settings is not None
        else {}
    )

    audio = client.generate(
        text=content,
        model=speaker.settings.voice_model,
        voice=Voice(
            voice_id=voice_id,
            settings=VoiceSettings(
                **voice_settings,
            ),
        ),
    )

    return audio


hume_speaker_last_generation_id: dict[str, str] = {}


async def _generate_audio_segment_hume_async(
    content: str,
    speaker: Speaker,
) -> bytes:
    client = AsyncHumeClient(api_key=os.getenv("HUME_API_KEY"))

    context = None

    if speaker.name in hume_speaker_last_generation_id:
        generation_id = hume_speaker_last_generation_id[speaker.name]
        context = PostedContextWithGenerationId(
            generation_id=generation_id,
        )

    speech = await client.tts.synthesize_json(
        utterances=[
            PostedUtterance(
                voice=PostedUtteranceVoiceWithId(
                    id=speaker.settings.voice_id,
                ),
                text=content,
            )
        ],
        context=context,
    )

    hume_speaker_last_generation_id[speaker.name] = speech.generations[0].generation_id
    audio_data = base64.b64decode(speech.generations[0].audio)

    return audio_data


def generate_audio_segment_hume(
    content: str,
    speaker: Speaker,
) -> bytes:
    """Generate audio using Hume AI's TTS service."""
    # Run the async function in a synchronous context
    return asyncio.run(_generate_audio_segment_hume_async(content, speaker))


@backoff.on_exception(backoff.expo, (RateLimitError, APIError), max_tries=5)
def generate_audio_segment_openai(
    content: str,
    speaker: Speaker,
) -> bytes | Iterator[bytes]:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    try:
        audio = client.audio.speech.create(
            model=speaker.settings.voice_model,
            voice=speaker.settings.voice_id,  # type: ignore
            input=content,
        )
        return audio.content
    except RateLimitError as e:
        print(f"Rate limit reached: {e}. Retrying...")
        raise
    except APIError as e:
        print(f"API error occurred: {e}. Retrying...")
        raise
    finally:
        time.sleep(0.5)


TTS_PROVIDERS = {
    "elevenlabs": generate_audio_segment_elevenlabs,
    "openai": generate_audio_segment_openai,
    "hume": generate_audio_segment_hume,
}


def generate_audio_segment(
    content: str,
    speaker: Speaker,
    output_path: Path,
    overwrite: bool = False,
) -> AudioSegment:
    if not output_path.exists() or overwrite:
        tts_function = TTS_PROVIDERS[speaker.settings.provider]
        audio = tts_function(content, speaker)

        save(audio, str(output_path))

    audio_segment = AudioSegment.from_mp3(str(output_path))
    return audio_segment
