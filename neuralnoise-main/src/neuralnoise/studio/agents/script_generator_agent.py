import logging
from typing import Any

from autogen import AssistantAgent, SwarmResult

from neuralnoise.models import PodcastScript, SharedContext


def create_script_generator_agent(
    system_msg: str,
    llm_config: dict,
) -> AssistantAgent:
    """Create and return a ScriptGeneratorAgent that writes a section script.

    Args:
        system_msg: Base system message for the agent
        llm_config: LLM configuration dictionary
        next_agent: The next agent to hand off to after script generation

    Returns:
        AssistantAgent: The configured script generator agent
    """
    logger = logging.getLogger(__name__)

    def ask_content_summarizer_agent(
        question: str,
        context_variables: dict[str, Any] = {},
    ) -> SwarmResult:
        """Ask the ContentSummarizerAgent for any relevant information to make the script more accurate."""
        logger.info("Asking ContentSummarizerAgent for any relevant information")

        return SwarmResult(
            values=f"ContentSummarizerAgent, I need to know more about this question: {question}",
            context_variables=context_variables,
            agent="ContentSummarizerAgent",
        )

    def write_podcast_section_script(
        podcast_script: PodcastScript | dict[str, Any],
        context_variables: dict[str, Any] = {},
    ) -> SwarmResult:
        """Writes and saves a generated PodcastScript to the shared context.

        Args:
            podcast_script: The generated podcast script
            context_variables: The shared context variables

        Returns:
            SwarmResult: Result containing success message and next agent
        """
        logger.info("Writing script to shared context")
        shared_state = SharedContext.model_validate(context_variables)

        # Validate and convert to model if not already
        if isinstance(podcast_script, PodcastScript):
            script_dict = podcast_script.model_dump()
        else:
            script_dict = PodcastScript.model_validate(podcast_script).model_dump()

        # Update the shared context with the generated script
        section_id = script_dict["section_id"]
        shared_state.section_scripts[section_id] = script_dict

        return SwarmResult(
            values="Successfully generated this section of the podcast script. I'll look forward to the EditorAgent's review.",
            context_variables=shared_state.model_dump(),
            agent="EditorAgent",
        )

    # Create and return the agent
    agent = AssistantAgent(
        name="ScriptGeneratorAgent",
        system_message=system_msg,
        llm_config=llm_config,
        functions=[ask_content_summarizer_agent, write_podcast_section_script],
    )
    return agent
