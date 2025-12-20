import logging
import shutil
from pathlib import Path

import typer
from dotenv import load_dotenv
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
from tabulate import tabulate

from neuralnoise.extract import extract_content
from neuralnoise.studio import generate_podcast_episode
from neuralnoise.utils import package_root

app = typer.Typer()

load_dotenv()
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


@app.command()
def generate(
    name: str = typer.Option(..., help="Name of the podcast episode"),
    input: list[str] | None = typer.Argument(
        None,
        help="Paths to input files or URLs. Can specify multiple inputs.",
    ),
    config: Path = typer.Option(
        Path("config/config_openai.json"),
        help="Path to the podcast configuration file",
    ),
    only_script: bool = typer.Option(False, help="Only generate the script and exit"),
):
    """
    Generate a script from one or more input text files using the specified configuration.

    For example:

    nn generate <url|file> [<url|file>...] --name <name> --config config/config_openai.json
    """
    typer.secho(f"Generating podcast episode {name}", fg=typer.colors.GREEN)

    output_dir = Path("output") / name
    output_dir.mkdir(parents=True, exist_ok=True)

    content_path = output_dir / "content.md"

    if content_path.exists():
        with open(content_path, "r") as f:
            content = f.read()
    else:
        if input is None:
            typer.secho(
                "No input provided. Please specify input files or URLs.",
                fg=typer.colors.RED,
            )
            raise typer.Exit(1)

        typer.secho(f"Extracting content from inputs {input}", fg=typer.colors.YELLOW)
        content = extract_content(input)

        with open(content_path, "w") as f:
            f.write(content)

    typer.secho(f"Generating podcast episode {name}", fg=typer.colors.GREEN)
    generate_podcast_episode(
        name,
        content,
        config_path=config,
        only_script=only_script,
    )

    typer.secho(
        f"Podcast generation complete. Output saved to {output_dir}",
        fg=typer.colors.GREEN,
    )


def get_audio_length(file_path: Path) -> float:
    """Get the length of an audio file in seconds."""
    try:
        audio = AudioSegment.from_file(file_path)
        return len(audio) / 1000  # Convert milliseconds to seconds
    except CouldntDecodeError:
        typer.echo(f"Error: Couldn't decode audio file {file_path}")
        return -1.0


@app.command("list")
def list_episodes():
    """
    List all generated podcast episodes stored in the 'output' folder,
    including their audio file length in minutes. Episodes with invalid audio files are filtered out.
    """
    output_dir = Path("output")
    if not output_dir.exists():
        typer.echo("No episodes found. The 'output' folder does not exist.")
        return

    episodes = [d for d in output_dir.iterdir() if d.is_dir()]

    if not episodes:
        typer.echo("No episodes found in the 'output' folder.")
        return

    episode_data = []
    for episode in sorted(episodes):
        audio_files = list(episode.glob("*.wav")) + list(episode.glob("*.mp3"))
        if audio_files:
            audio_file = audio_files[0]  # Take the first audio file found
            length_seconds = get_audio_length(audio_file)
            if length_seconds != -1:  # Filter out invalid audio files
                length_minutes = length_seconds / 60  # Convert seconds to minutes
                episode_data.append(
                    [episode.name, audio_file.name, f"{length_minutes:.2f}"]
                )
        else:
            episode_data.append([episode.name, "No audio file", "N/A"])

    if not episode_data:
        typer.echo("No valid episodes found.")
        return

    headers = ["Episode", "Audio File", "Length (minutes)"]
    table = tabulate(episode_data, headers=headers, tablefmt="grid")
    typer.echo("Generated podcast episodes:")
    typer.echo(table)


@app.command()
def init(
    output_path: Path = typer.Option(
        Path("prompts"),
        "--output",
        "-o",
        help="Directory where prompts will be copied to",
        show_default=True,
    ),
):
    """
    Initialize a local copy of the default prompts.
    Creates a directory with the default prompt templates.

    Example:
        nn init
        nn init --output custom/path/prompts
    """
    source_dir = package_root / "prompts"

    if output_path.exists():
        typer.echo(f"Directory {output_path} already exists. Skipping initialization.")
        return

    try:
        shutil.copytree(source_dir, output_path)
        typer.echo(f"Successfully created prompts directory at {output_path}")
        typer.echo("You can now customize these prompts for your podcast generation.")
    except Exception as e:
        typer.echo(f"Error creating prompts directory: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
