from enum import Enum, auto
from pathlib import Path
from string import Template


class PromptType(Enum):
    """Enumeration of all available prompt types."""

    CONTENT_ANALYZER = auto()
    PLANNER = auto()
    SCRIPT_GENERATOR = auto()
    EDITOR = auto()
    USER_PROXY = auto()
    USER_MESSAGE = auto()
    MANAGER = auto()


class PromptManager:
    """
    Manages loading and caching of system prompts for the neuralnoise application.

    This class provides a centralized way to load and access prompts from the prompts directory.
    It loads all prompts during initialization and provides methods to access and substitute
    variables in the prompts.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        """Implement singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super(PromptManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, prompts_dir: Path | None = None, language: str = "en"):
        """
        Initialize the PromptManager with the prompts directory and language.

        Args:
            prompts_dir: Directory containing prompt files. If None, uses the default package prompts.
            language: Language code for prompt templates.
        """
        # Skip initialization if already initialized
        if hasattr(self, "_initialized") and self._initialized:
            return

        self.language = language

        # Set prompts directory
        if prompts_dir is None:
            from neuralnoise.utils import package_root

            self.prompts_dir = package_root / "prompts"
        else:
            self.prompts_dir = Path(prompts_dir)

        # Map of PromptType to file paths
        self.prompt_files = {
            PromptType.CONTENT_ANALYZER: self.prompts_dir
            / "content_analyzer.system.xml",
            PromptType.PLANNER: self.prompts_dir / "planner.system.xml",
            PromptType.SCRIPT_GENERATOR: self.prompts_dir
            / "script_generation.system.xml",
            PromptType.EDITOR: self.prompts_dir / "editor.system.xml",
            PromptType.USER_PROXY: self.prompts_dir / "user_proxy.system.xml",
            PromptType.USER_MESSAGE: self.prompts_dir / "user_proxy.message.xml",
            PromptType.MANAGER: self.prompts_dir / "manager.system.xml",
        }

        # Load all prompts
        self.prompts: dict[PromptType, str] = {}
        self._load_all_prompts()

        self._initialized = True

    def _load_all_prompts(self) -> None:
        """Load all prompts from the prompts directory."""
        for prompt_type, file_path in self.prompt_files.items():
            self.prompts[prompt_type] = self._load_prompt_file(file_path)

    def _load_prompt_file(self, path: Path) -> str:
        """
        Load a prompt from a file.

        Args:
            path: Path to the prompt file.

        Returns:
            The content of the prompt file or an empty string if the file doesn't exist.
        """
        if not path.exists():
            return ""

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        return content

    def get_prompt(self, prompt_type: PromptType, **kwargs) -> str:
        """
        Get a prompt with variables substituted.

        Args:
            prompt_type: Type of prompt to get.
            **kwargs: Variables to substitute in the prompt.

        Returns:
            The prompt with variables substituted.
        """
        content = self.prompts.get(prompt_type, "")

        # Always include language in kwargs if not provided
        if "language" not in kwargs:
            kwargs["language"] = self.language

        if content and kwargs:
            template = Template(content)
            content = template.safe_substitute(kwargs)

        return content

    def update_prompt(self, prompt_type: PromptType, **common_kwargs) -> None:
        """
        Update a prompt with common variables substituted.

        Args:
            **common_kwargs: Common variables to substitute in all prompts.

        Returns:
            Dictionary mapping prompt names to prompt content.
        """
        self.prompts[prompt_type] = self.get_prompt(prompt_type, **common_kwargs)

    def update_prompts(self, **common_kwargs) -> None:
        """
        Update all prompts with common variables substituted.

        Args:
            **common_kwargs: Common variables to substitute in all prompts.

        Returns:
            Dictionary mapping prompt names to prompt content.
        """
        for prompt_type in PromptType:
            self.prompts[prompt_type] = self.get_prompt(prompt_type, **common_kwargs)
