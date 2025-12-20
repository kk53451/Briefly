import hashlib
import json
import os
from pathlib import Path
from typing import Any

from autogen import ChatResult
from pydub import AudioSegment
from pydub.effects import normalize
from tqdm.auto import tqdm

from neuralnoise.models import StudioConfig
from neuralnoise.prompt_manager import PromptManager, PromptType
from neuralnoise.studio.agents.agents_manager import AgentsManager
from neuralnoise.tts import generate_audio_segment
from neuralnoise.utils import package_root


# Custom JSON encoder to handle ChatResult serialization
class ChatResultEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ChatResult):
            # Convert ChatResult to dictionary with relevant fields
            return {
                "chat_history": obj.chat_history,
                "summary": obj.summary,
                "cost": obj.cost,
            }
        return super().default(obj)


class PodcastStudio:
    """Manages the end-to-end process of podcast generation using agents and TTS."""

    def __init__(
        self, work_dir: str | Path, config: StudioConfig, max_round: int = 50
    ) -> None:
        """
        Initialize the podcast studio with configuration.

        Args:
            work_dir: Working directory for outputs and intermediate files
            config: Studio configuration with show details, speakers etc.
            max_round: Maximum conversation rounds for agent-based generation
        """
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.config = config
        self.language = config.show.language
        self.max_round = max_round

        # Initialize the prompt manager
        prompts_dir = (
            config.prompts_dir if config.prompts_dir else package_root / "prompts"
        )
        self.prompt_manager = PromptManager(
            prompts_dir=prompts_dir,
            language=self.language,
        )

        config_dict = self.config.model_dump()
        self.prompt_manager.update_prompts(
            min_segments=str(self.config.show.min_segments),
            max_segments=str(self.config.show.max_segments),
            show=json.dumps(config_dict["show"], indent=2),
            speakers=json.dumps(config_dict["speakers"], indent=2),
        )

        # Create agents manager with the required parameters
        self.agents_manager = AgentsManager(
            llm_config=self._load_llm_config(),
            language=self.language,
            work_dir=self.work_dir,
        )

    def _load_llm_config(self) -> dict:
        """Load LLM configuration."""
        return {
            "config_list": [
                {
                    "model": "gpt-4o",
                    "api_key": os.environ.get("OPENAI_API_KEY", ""),
                }
            ]
        }

    def generate_script(self, content: str) -> dict[str, Any]:
        """Generate a podcast script using AgentsManager and return the final script and chat log."""
        # For debugging
        print(f"DEBUG - Content length: {len(content) if content else 0}")
        print(f"DEBUG - Content preview: {content[:100] if content else 'None'}")

        #
        # WIP: adapt the DocumentAgent to handle the content directly.
        # For now, we're in charge of the content extraction
        #
        content_path = self.work_dir / "content.md"

        # Prepare initial message using the user message template with content properly embedded
        self.prompt_manager.update_prompt(
            PromptType.USER_MESSAGE,
            content_path=content_path,
        )
        initial_message = self.prompt_manager.get_prompt(PromptType.USER_MESSAGE)

        # For debugging
        print(f"DEBUG - Initial message length: {len(initial_message)}")
        print(f"DEBUG - Initial message preview: {initial_message[:100]}")

        chat_result, final_state, _ = self.agents_manager.run_swarm_chat(
            initial_message
        )

        with open(self.work_dir / "final_state.json", "w") as f:
            json.dump(final_state.model_dump(), f, indent=4)

        script_data = {
            "sections": final_state.section_scripts,
            "messages": chat_result,
        }

        # Use custom encoder for JSON serialization
        return json.loads(json.dumps(script_data, cls=ChatResultEncoder))

    def generate_podcast_from_script(self, script: dict[str, Any]) -> AudioSegment:
        """Generate the podcast audio from the script using TTS."""
        temp_dir = self.work_dir / "segments"
        temp_dir.mkdir(exist_ok=True)

        # Gather all segments from each section
        script_segments: list[tuple[str, dict]] = []
        for section_id in sorted(script["sections"].keys()):
            section = script["sections"][section_id]
            for segment in section.get("segments", []):
                script_segments.append((section_id, segment))

        audio_segments: list[AudioSegment] = []
        for section_id, segment in tqdm(
            script_segments, desc="Generating audio segments"
        ):
            speaker = self.config.speakers[segment["speaker"]]
            text = segment["content"].replace("¡", "").replace("¿", "")
            content_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
            segment_path = temp_dir / f"{section_id}_{segment['id']}_{content_hash}.mp3"
            audio_segment = generate_audio_segment(
                text, speaker, output_path=segment_path
            )
            audio_segments.append(audio_segment)
            if blank_duration := segment.get("blank_duration"):
                silence = AudioSegment.silent(duration=blank_duration * 1000)
                audio_segments.append(silence)

        podcast = AudioSegment.empty()
        for seg in audio_segments:
            podcast += seg
        podcast = normalize(podcast)
        return podcast
