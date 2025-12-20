import json
import logging
from pathlib import Path
from typing import Literal

from pydub import AudioSegment

from neuralnoise.models import StudioConfig
from neuralnoise.studio import PodcastStudio

logger = logging.getLogger(__name__)


def generate_podcast_episode(
    name: str,
    content: str,
    config: StudioConfig | None = None,
    config_path: str | Path | None = None,
    format: Literal["wav", "mp3", "ogg"] = "wav",
    only_script: bool = False,
) -> AudioSegment | None:
    """Generate a podcast episode from a given content.

    Args:
        name: Name of the podcast episode.
        content: Content to generate the podcast episode from.
        config: Studio configuration (optional).
        config_path: Path to the studio configuration file (optional).
        format: Format of the podcast episode.
        only_script: Whether to only generate the script and not the podcast.
    """
    # Create output directory
    output_dir = Path("output") / name
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load configuration
    if config_path:
        logger.info("🔧  Loading configuration from %s", config_path)
        with open(config_path, "r") as f:
            config = StudioConfig.model_validate_json(f.read())

    if not config:
        raise ValueError("No studio configuration provided")

    studio = PodcastStudio(work_dir=output_dir, config=config)

    # Generate the script
    script_path = output_dir / "script.json"

    if script_path.exists():
        logger.info("💬  Loading cached script")
        script = json.loads(script_path.read_text())
    else:
        logger.info("💬  Generating podcast script")
        script = studio.generate_script(content)

        script_path.write_text(json.dumps(script, ensure_ascii=False))

    if only_script:
        return None

    # Generate audio segments and create the podcast
    logger.info("🎙️  Recording podcast episode")
    podcast = studio.generate_podcast_from_script(script)

    # Export podcast
    podcast_filepath = output_dir / f"output.{format}"
    logger.info("️💾  Exporting podcast to %s", podcast_filepath)
    podcast.export(podcast_filepath, format=format)

    logger.info("✅  Podcast generation complete")

    return podcast
