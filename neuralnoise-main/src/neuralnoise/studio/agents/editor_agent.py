from autogen import AssistantAgent
from typing import Any

from autogen import SwarmResult

from neuralnoise.models import SharedContext


def create_editor_agent(
    system_msg: str,
    llm_config: dict,
) -> AssistantAgent:
    """Create and return an EditorAgent that reviews a section script and determines the next agent.

    Args:
        system_msg (str): The system message for the EditorAgent.
        llm_config (dict): The LLM configuration.

    Returns:
        AssistantAgent: The EditorAgent instance.
    """

    def provide_script_feedback(
        section_feedback: str,
        context_variables: dict[str, Any],
    ) -> SwarmResult:
        """Provide feedback on the script. Don't iterate on the script more than 3 times."""
        shared_state = SharedContext.model_validate(context_variables)

        if shared_state.current_section_index not in shared_state.section_feedbacks:
            shared_state.section_feedbacks[shared_state.current_section_index] = []

        shared_state.section_feedbacks[shared_state.current_section_index].append(
            section_feedback
        )

        return SwarmResult(
            values="Feedback provided",
            agent="ScriptGeneratorAgent",
            context_variables=shared_state.model_dump(),
        )

    def mark_section_as_approved(
        context_variables: dict[str, Any],
    ) -> SwarmResult:
        """Validate the section script after the feedback was provided and transfer to the Planner Agent."""
        shared_state = SharedContext.model_validate(context_variables)

        return SwarmResult(
            values="Script validated and marked as approved",
            agent="PlannerAgent",
            context_variables=shared_state.model_dump(),
        )

    agent = AssistantAgent(
        name="EditorAgent",
        system_message=system_msg,
        llm_config=llm_config,
        functions=[provide_script_feedback, mark_section_as_approved],
    )

    return agent
