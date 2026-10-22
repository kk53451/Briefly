"""
대본 생성 엔진 공통 인터페이스

gpt-5.4 기반 대본 생성을 통일된 방식으로 호출하기 위한 추상 클래스.
generate_script()는 이 인터페이스만 보고, 구체 엔진 교체는 팩토리를 통해 수행한다.
"""

from abc import ABC, abstractmethod
from typing import Dict, Tuple


class ScriptEngine(ABC):
    """대본 생성 엔진 베이스 클래스"""

    name: str = "base"

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 30000,
    ) -> Tuple[str, Dict]:
        """
        주어진 프롬프트로 대본을 생성합니다.

        Args:
            system_prompt: 시스템 프롬프트 (역할 정의)
            user_prompt: 사용자 프롬프트 (태스크 + 소스)
            max_tokens: 최대 출력 토큰 (reasoning 포함)

        Returns:
            (generated_text, usage_info)
                generated_text: 생성된 대본 텍스트
                usage_info: {"input_tokens", "output_tokens", "model", ...}
        """
        ...
