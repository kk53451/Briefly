import os
import requests
from app.utils.s3 import upload_audio_to_s3

# 환경 변수에서 ElevenLabs API 키와 음성 ID 불러오기
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

def text_to_speech(text: str) -> bytes:
    """
    텍스트를 ElevenLabs TTS API로 음성(MP3) 변환
    API 문서 검증을 통한 안전한 설정
    """
    if not text or len(text.strip()) < 100:
        raise ValueError("TTS 변환 실패: 입력 텍스트가 너무 짧습니다")

    # API 문서에 따른 올바른 URL과 파라미터 구조
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}?output_format=mp3_44100_128"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    # 검증된 안전한 설정 (API 문서 기준)
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.45,          # 자연스러운 변화 허용 (0.5 → 0.45)
            "similarity_boost": 0.85,   # 음성 특성 더 강화 (0.8 → 0.85)
            "style": 0.15,             # 약간의 스타일 변화 허용 (0.1 → 0.15)
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        raise Exception(f"ElevenLabs TTS 실패: {response.status_code} {response.text}")

    return response.content

def text_to_speech_with_prosody(text: str) -> bytes:
    """
    자연스러운 억양과 감정을 위한 향상된 TTS 변환
    """
    # 자연스러운 억양을 위한 텍스트 전처리
    enhanced_text = enhance_text_for_natural_speech(text)
    
    return text_to_speech(enhanced_text)

def enhance_text_for_natural_speech(text: str) -> str:
    """
    자연스러운 음성을 위한 고급 텍스트 향상
    한국어 TTS 최적화 및 자연스러운 억양 구현
    """
    import re
    
    # 1. 기본 문장 부호 정리 및 호흡 지점 개선
    text = re.sub(r'\.(?!\s*$)', '. ', text)
    text = re.sub(r'\!(?!\s*$)', '! ', text)
    text = re.sub(r'\?(?!\s*$)', '? ', text)
    text = re.sub(r'\,(?!\s)', ', ', text)
    
    # 2. 자연스러운 억양을 위한 감탄사와 추임새 강화
    text = re.sub(r'그런데(?!\s)', '그런데... ', text)
    text = re.sub(r'하지만(?!\s)', '하지만... ', text)
    text = re.sub(r'그리고(?!\s)', '그리고, ', text)
    text = re.sub(r'또한(?!\s)', '또한, ', text)
    text = re.sub(r'특히(?!\s)', '특히... ', text)
    text = re.sub(r'정말(?!\s)', '정말로 ', text)
    
    # 3. 숫자와 단위 표현 자연스럽게 개선
    text = re.sub(r'(\d+)%', r'\1 퍼센트', text)
    text = re.sub(r'(\d+)억', r'\1억', text)
    text = re.sub(r'(\d+)만', r'\1만', text)
    text = re.sub(r'(\d{1,3})(,\d{3})+', lambda m: m.group().replace(',', ''), text)
    
    # 4. 전문용어와 고유명사 앞뒤 여유 추가
    text = re.sub(r'([A-Z]{2,})', r' \1 ', text)  # 약어들
    text = re.sub(r'(\w+API|\w+AI)', r' \1 ', text)  # 기술 용어
    
    # 5. 강조 표현 개선
    text = re.sub(r'중요한(?!\s)', '정말 중요한 ', text)
    text = re.sub(r'놀라운(?!\s)', '정말 놀라운 ', text)
    text = re.sub(r'흥미로운(?!\s)', '매우 흥미로운 ', text)
    
    # 6. 자연스러운 호흡과 리듬을 위한 문장 분할
    sentences = text.split('. ')
    enhanced_sentences = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # 긴 문장 자연스럽게 분할 (100자 이상)
        if len(sentence) > 100:
            # 접속사나 쉼표 기준으로 분할
            connectors = ['그런데', '하지만', '또한', '그리고', '특히', '즉', '다시 말해']
            for connector in connectors:
                if connector in sentence:
                    parts = sentence.split(connector, 1)
                    if len(parts) == 2:
                        sentence = parts[0].strip() + '. ' + connector + ' ' + parts[1].strip()
                        break
            
            # 쉼표 기준 분할 (여전히 길면)
            if len(sentence) > 120:
                comma_parts = sentence.split(', ')
                if len(comma_parts) > 2:
                    mid_point = len(comma_parts) // 2
                    sentence = ', '.join(comma_parts[:mid_point]) + '. ' + ', '.join(comma_parts[mid_point:])
        
        enhanced_sentences.append(sentence)
    
    # 7. 최종 정리 및 불필요한 공백 제거
    result = '. '.join(enhanced_sentences)
    result = re.sub(r'\s+', ' ', result)  # 연속된 공백 제거
    result = re.sub(r'\s+([,.!?])', r'\1', result)  # 문장부호 앞 공백 제거
    
    return result.strip()

def text_to_speech_and_store(text: str, user_id: str, category: str, date: str) -> str:
    """
    향상된 TTS 변환 → S3 업로드 → Presigned URL 반환
    """
    audio_bytes = text_to_speech_with_prosody(text)
    return upload_audio_to_s3(audio_bytes, user_id, category, date)
