"""
OpenAI gpt-5.4 + reasoning=high 엔진
"""

import os
import logging
from typing import Tuple, Dict

from openai import OpenAI

from .base import ScriptEngine

logger = logging.getLogger(__name__)


class OpenAIScriptEngine(ScriptEngine):
    name = "openai"

    def __init__(self, model: str = None, reasoning_effort: str = "high"):
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5.4")
        self.reasoning_effort = reasoning_effort
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    @staticmethod
    def _is_reasoning(model: str) -> bool:
        return model.startswith(("gpt-5", "o1", "o3"))

    @staticmethod
    def _strip_code_fence(text: str) -> str:
        """모델이 전체 응답을 markdown ``` 블록으로 감싸서 반환했을 때 fence만 제거.
        NotebookLM 이 ``` 으로 시작하는 텍스트 소스를 FAILED_PRECONDITION 으로 거절하므로 필수.
        """
        s = text.strip()
        if not s.startswith("```"):
            return s
        lines = s.split("\n")
        if len(lines) < 2 or lines[-1].strip() != "```":
            return s
        return "\n".join(lines[1:-1]).strip()

    def _build_kwargs(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> dict:
        kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if self._is_reasoning(self.model):
            kwargs["reasoning_effort"] = self.reasoning_effort
            kwargs["max_completion_tokens"] = max_tokens
        else:
            kwargs["temperature"] = temperature
            # 비-reasoning 모델(gpt-4o 등)은 completion 한도가 낮음.
            # gpt-4o = 16384, gpt-4o-mini = 16384. 호출부는 reasoning 기준
            # max_tokens=30000 을 그대로 던지므로 여기서 안전하게 cap.
            kwargs["max_tokens"] = min(max_tokens, 16384)
        return kwargs

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 30000,
    ) -> Tuple[str, Dict]:
        kwargs = self._build_kwargs(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            temperature=0.2,
        )
        response = self.client.chat.completions.create(**kwargs)
        text = self._strip_code_fence(
            (response.choices[0].message.content or "").strip()
        )

        # 캐시 히트 정보 추출 (OpenAI 자동 prompt caching)
        cached = 0
        if response.usage.prompt_tokens_details:
            cached = getattr(
                response.usage.prompt_tokens_details, "cached_tokens", 0
            ) or 0

        if cached > 0:
            logger.info(
                f"  💰 Prompt cache hit: {cached:,} tokens "
                f"({cached / response.usage.prompt_tokens * 100:.0f}% of input)"
            )

        usage = {
            "model": self.model,
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
            "cached_tokens": cached,
        }
        return text, usage
