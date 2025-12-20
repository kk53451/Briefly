from typing import Any

from autogen import AssistantAgent, SwarmResult

from neuralnoise.models import SharedContext


def create_planner_agent(system_msg: str, llm_config: dict) -> AssistantAgent:
    """Create and return a PlannerAgent that generates a sections plan based on
    content analysis."""

    def generate_execution_plan(
        execution_plans: str,
        context_variables: dict[str, Any],
    ) -> SwarmResult:
        """Generate an execution plan for the complete podcast after a complete
        analysis of the podcast was done."""
        shared_state = SharedContext.model_validate(context_variables)

        shared_state.execution_plans = execution_plans

        return SwarmResult(
            values=execution_plans,
            agent="ScriptGeneratorAgent",
            context_variables=shared_state.model_dump(),
        )

    def update_current_section_index(
        section_index: int,
        context_variables: dict[str, Any],
    ) -> SwarmResult:
        """Update the current section index in the shared context to go to next
        section."""
        shared_state = SharedContext.model_validate(context_variables)
        shared_state.current_section_index = section_index

        return SwarmResult(
            values="Execute the plan and generate the next section of the podcast script.",
            agent="ScriptGeneratorAgent",
            context_variables=shared_state.model_dump(),
        )

    def wrap_up_podcast(
        context_variables: dict[str, Any],
    ) -> SwarmResult:
        """Wrap up the podcast and save the final script if you're done or created a conclusion section."""
        shared_state = SharedContext.model_validate(context_variables)

        return SwarmResult(
            values="Terminate the process and wrap up the podcast.",
            context_variables=shared_state.model_dump(),
        )

    agent = AssistantAgent(
        name="PlannerAgent",
        system_message=system_msg,
        llm_config=llm_config,
        functions=[
            generate_execution_plan,
            update_current_section_index,
            wrap_up_podcast,
        ],
    )

    return agent
