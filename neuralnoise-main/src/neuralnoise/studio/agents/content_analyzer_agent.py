from typing import Any

from autogen import AssistantAgent, SwarmResult

from neuralnoise.models import ContentAnalysis, SharedContext


def create_content_analyzer_agent(
    system_msg: str,
    llm_config: dict,
    language: str,
) -> AssistantAgent:
    """Create and return a ContentAnalyzerAgent for analyzing content."""

    def save_content_analysis(
        content_analysis: dict[str, Any] | ContentAnalysis,
        context_variables: dict,
    ) -> SwarmResult:
        """This function saves result of the agent getting the content analysis
        to the shared state."""
        if not content_analysis:
            return SwarmResult(
                values="Error: Missing content_analysis",
                agent=None,
                context_variables=context_variables,
            )

        shared_state = SharedContext.model_validate(context_variables)
        validated_analysis = ContentAnalysis.model_validate(
            content_analysis
        ).model_dump()

        shared_state.content_analysis = validated_analysis

        return SwarmResult(
            values="Content analysis successfully validated and saved. Moving to next agent.",
            agent="PlannerAgent",
            context_variables=shared_state.model_dump(),
        )

    agent = AssistantAgent(
        name="ContentAnalyzerAgent",
        system_message=system_msg.replace("${language}", language),
        llm_config=llm_config,
        functions=[save_content_analysis],
    )
    return agent
