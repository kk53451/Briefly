"""
AgentsManager module: Centralizes instantiation and handoff registration for swarm agents.
It also defines a final workflow to run the swarm chat and extract the final results.
"""

import uuid
from pathlib import Path
from typing import Sequence, Tuple

from autogen import (
    AfterWorkOption,
    ChatResult,
    ConversableAgent,
    OnCondition,
    UserProxyAgent,
    initiate_swarm_chat,
    register_hand_off,
)
from autogen.agents.experimental.document_agent import DocAgent as DocumentAgent

from neuralnoise.models import ContentAnalysis, PodcastScript, SharedContext
from neuralnoise.prompt_manager import PromptManager, PromptType
from neuralnoise.studio.agents.content_analyzer_agent import (
    create_content_analyzer_agent,
)
from neuralnoise.studio.agents.editor_agent import create_editor_agent
from neuralnoise.studio.agents.planner_agent import create_planner_agent
from neuralnoise.studio.agents.script_generator_agent import (
    create_script_generator_agent,
)


class AgentsManager:
    def __init__(
        self,
        llm_config: dict,
        language: str,
        work_dir: Path | None = None,
    ) -> None:
        """
        Initialize the AgentsManager with required configuration parameters,
        instantiate all agents, and register handoffs.

        Args:
            llm_config (dict): LLM configuration parameters.
            language (str): Language identifier for prompts.
        """
        self.language: str = language
        self.llm_config: dict = llm_config
        self.work_dir = work_dir
        self.agents: dict[str, ConversableAgent] = {}

        self.prompt_manager = PromptManager(language=language)

        self.agents["PlannerAgent"] = create_planner_agent(
            system_msg=self.prompt_manager.get_prompt(PromptType.PLANNER),
            llm_config=llm_config,
        )

        random_id = str(uuid.uuid4())

        self.agents["ContentSummarizerAgent"] = DocumentAgent(
            name="ContentSummarizerAgent",
            llm_config=llm_config,
            collection_name=f"document_content_{random_id}",
            parsed_docs_path=self.work_dir / "parsed_docs" if self.work_dir else None,
        )

        content_analyzer_llm_config = llm_config.copy()
        content_analyzer_llm_config["response_format"] = ContentAnalysis
        self.agents["ContentAnalyzerAgent"] = create_content_analyzer_agent(
            system_msg=self.prompt_manager.get_prompt(PromptType.CONTENT_ANALYZER),
            llm_config=content_analyzer_llm_config,
            language=language,
        )

        register_hand_off(
            agent=self.agents["ContentSummarizerAgent"],
            hand_to=OnCondition(
                target=self.agents["ContentAnalyzerAgent"],
                condition="Summary is created and ready to analyze by the ContentAnalyzerAgent",
            ),
        )

        script_generator_llm_config = llm_config.copy()
        script_generator_llm_config["response_format"] = PodcastScript
        self.agents["ScriptGeneratorAgent"] = create_script_generator_agent(
            system_msg=self.prompt_manager.get_prompt(PromptType.SCRIPT_GENERATOR),
            llm_config=script_generator_llm_config,
        )

        self.agents["EditorAgent"] = create_editor_agent(
            system_msg=self.prompt_manager.get_prompt(PromptType.EDITOR),
            llm_config=llm_config,
        )

    def run_swarm_chat(
        self, initial_message: str
    ) -> Tuple[ChatResult, SharedContext, ConversableAgent]:
        """
        Set up the shared state and user proxy, and initiate the swarm chat flow.

        Args:
            initial_message (str): The initial message or prompt for the swarm chat.

        Returns:
            Tuple[ChatResult, SharedState, ConversableAgent]: A tuple containing the conversation log,
            the final shared state, and the last agent that handled the conversation.
        """
        # Instantiate shared state.
        shared_state = SharedContext()

        # Prepare list of agents.
        swarm_agents: Sequence[ConversableAgent] = list(self.agents.values())

        user_proxy = UserProxyAgent(
            name="UserProxyAgent",
            human_input_mode="NEVER",
            code_execution_config=False,
        )

        # Initiate swarm chat starting with the ContentAnalyzerAgent.
        chat_result, final_context, last_agent = initiate_swarm_chat(
            initial_agent=self.agents["ContentSummarizerAgent"],
            agents=swarm_agents,
            messages=initial_message,
            context_variables=shared_state.model_dump(),
            user_agent=user_proxy,
            swarm_manager_args={
                "human_input_mode": "NEVER",
                "system_message": self.prompt_manager.get_prompt(PromptType.MANAGER),
                "llm_config": self.llm_config,
            },
            after_work=AfterWorkOption.SWARM_MANAGER,
            max_rounds=200,
        )

        # Update shared state with final context.
        shared_state = shared_state.model_validate(final_context)

        return chat_result, shared_state, last_agent
