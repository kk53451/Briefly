"""
Podcastfy 기반 대화형 팟캐스트 서비스

두 사람이 대화하는 형식의 뉴스 팟캐스트를 생성합니다.
- Person1 (앵커): 뉴스 진행
- Person2 (해설): 전문가 코멘트
"""

import os
import logging
from podcastfy.client import generate_podcast

logger = logging.getLogger(__name__)


class PodcastService:
    def __init__(self):
        self.config = self._load_korean_config()

    def _load_korean_config(self) -> dict:
        """한국어 대화형 팟캐스트 설정 로드"""
        return {
            "output_language": "Korean",
            "podcast_name": "브리플리 뉴스",
            "podcast_tagline": "AI가 전하는 오늘의 뉴스",
            "conversation_style": ["professional", "informative", "engaging"],
            "roles_person1": "뉴스 앵커",
            "roles_person2": "해설 전문가",
            "creativity": 0.6,
            "word_count": 2500,  # 7분 분량
            "dialogue_structure": [
                "오프닝 인사",
                "오늘의 주요 뉴스 소개",
                "뉴스별 심층 토론",
                "마무리 및 클로징"
            ],
            "engagement_techniques": [
                "rhetorical questions",
                "expert analysis",
                "contextual commentary"
            ],
            "text_to_speech": {
                "default_tts_model": "elevenlabs",
                "elevenlabs": {
                    "default_voices": {
                        "question": os.getenv("ELEVENLABS_VOICE_ID_PERSON1", "TX3LPaxmHKxFdv7VOQHJ"),
                        "answer": os.getenv("ELEVENLABS_VOICE_ID_PERSON2", "xi3rF0t7dg7uN2M0WUhr"),
                    },
                    "model": "eleven_multilingual_v2"
                },
                "audio_format": "mp3",
                "ending_message": "브리플리 뉴스였습니다. 내일 또 만나요."
            }
        }

    def generate_news_podcast(self, news_content: str, category: str) -> str:
        """
        뉴스 콘텐츠로부터 대화형 팟캐스트 생성

        Args:
            news_content: 팟캐스트로 변환할 뉴스 텍스트
            category: 뉴스 카테고리 (politics, economy 등)

        Returns:
            생성된 오디오 파일 경로
        """
        logger.info(f"🎙️ 대화형 팟캐스트 생성 시작: {category}")

        # 카테고리별 맞춤 지시사항 추가
        user_instructions = self._get_category_instructions(category)

        config = self.config.copy()
        config["user_instructions"] = user_instructions

        try:
            audio_file = generate_podcast(
                text=news_content,
                llm_model_name="gpt-4o-mini",
                api_key_label="OPENAI_API_KEY",
                tts_model="elevenlabs",
                conversation_config=config
            )
            logger.info(f"✅ 팟캐스트 생성 완료: {audio_file}")
            return audio_file

        except Exception as e:
            logger.error(f"❌ 팟캐스트 생성 실패: {e}")
            raise

    def _get_category_instructions(self, category: str) -> str:
        """카테고리별 맞춤 지시사항 반환"""
        instructions = {
            "politics": "정치 뉴스이므로 균형잡힌 시각으로 다양한 의견을 제시하세요. 특정 정당이나 정치인을 편향되게 다루지 마세요.",
            "economy": "경제 뉴스이므로 일반인도 이해하기 쉽게 설명하세요. 전문 용어는 쉬운 말로 풀어서 설명해주세요.",
            "society": "사회 뉴스이므로 공감과 따뜻한 시선으로 전달하세요. 피해자나 약자의 입장을 존중해주세요.",
            "culture": "문화 뉴스이므로 흥미롭고 생동감 있게 전달하세요. 문화적 맥락과 의미를 함께 설명해주세요.",
            "international": "국제 뉴스이므로 글로벌 맥락을 설명하세요. 한국과의 관련성도 함께 언급해주세요.",
            "local": "지역 뉴스이므로 지역 주민의 관점에서 전달하세요. 지역 사회에 미치는 영향을 설명해주세요.",
            "sports": "스포츠 뉴스이므로 열정적이고 생동감 있게 전달하세요. 경기 결과뿐 아니라 선수들의 노력도 조명해주세요.",
            "tech": "IT/과학 뉴스이므로 기술의 의미와 일상생활에 미치는 영향을 설명하세요. 기술 용어는 쉽게 풀어서 설명해주세요.",
        }
        return instructions.get(category, "뉴스를 명확하고 이해하기 쉽게 전달하세요. 청취자가 쉽게 이해할 수 있도록 설명해주세요.")
