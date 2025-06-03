# app/tasks/generate_frequency.py

import logging
from datetime import datetime

from app.utils.date import get_today_kst
from app.utils.dynamo import (
    save_frequency_summary,
    get_frequency_by_category_and_date,
    get_news_by_category_and_date,
    update_news_card_content,
)
from app.services.openai_service import summarize_articles
from app.services.tts_service import text_to_speech
from app.utils.s3 import upload_audio_to_s3_presigned
from app.constants.category_map import CATEGORY_MAP
from app.services.deepsearch_service import extract_content_with_bs4

# 로그 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def generate_all_frequencies():
    """
    ✅ 매일 오전 6시 자동 실행: 카테고리별 뉴스 본문 기반 공유 대본/음성 생성
    - 뉴스카드 DB에서 카테고리별 기사 최대 30개 사용
    - 부족한 본문은 재추출
    - 기사 본문을 GPT 요약하여 스크립트 생성
    - ElevenLabs TTS로 변환 후 S3 업로드
    - Frequencies 테이블에 저장 (스크립트 + Presigned MP3 링크)
    """
    date = get_today_kst()
    all_categories = CATEGORY_MAP.keys()
    logger.info(f"🌀 전체 카테고리 순회: {list(all_categories)}")

    for category_ko in all_categories:
        category_en = CATEGORY_MAP[category_ko]["api_name"]
        freq_id = f"{category_en}#{date}"

        # 중복 방지: 이미 생성된 경우 스킵
        if get_frequency_by_category_and_date(category_en, date):
            logger.info(f"🚫 이미 생성됨 → 스킵: {freq_id}")
            continue

        logger.info(f"📚 대본/음성 생성 시작: {category_en} ({freq_id})")

        try:
            # 해당 카테고리의 오늘 기사 불러오기
            articles = get_news_by_category_and_date(category_en, date)
            logger.info(f"📥 수집된 기사 수: {len(articles)}")

            full_contents = []

            # 기사 본문 최대 30개까지 수집
            for i, article in enumerate(articles[:40]):
                news_id = article.get("news_id")
                url = article.get("content_url")
                content = article.get("content", "").strip()

                if not news_id or not url:
                    logger.warning(f"⚠️ #{i+1} URL 또는 ID 없음 → 스킵")
                    continue

                # 본문이 짧거나 없으면 재추출 시도
                if not content or len(content) < 300:
                    try:
                        content = extract_content_with_bs4(url)
                        if content and len(content) >= 300:
                            update_news_card_content(news_id, content)
                            logger.info(f"♻️ #{i+1} 본문 보완 저장 완료 ({len(content)}자)")
                        else:
                            logger.warning(f"⚠️ #{i+1} 본문 추출 실패 또는 너무 짧음 → 스킵")
                            continue
                    except Exception as e:
                        logger.warning(f"❌ #{i+1} 본문 재추출 중 오류: {e}")
                        continue

                # 요약 전 텍스트 길이 제한 (토큰 초과 방지)
                trimmed = content[:3000]
                full_contents.append(trimmed)
                logger.info(f"✅ #{i+1} 본문 사용 완료 ({len(trimmed)}자)")

                if len(full_contents) >= 30:
                    break

            # 본문 수가 너무 적으면 스킵
            if len(full_contents) < 5:
                logger.warning(f"⚠️ 유효 본문 부족 → 스킵: {category_en}")
                continue

            # GPT로 종합 스크립트 요약 생성
            script = summarize_articles(full_contents, category_en)
            if not script or len(script) < 500:
                logger.warning(f"⚠️ 요약 길이 부족 → 스킵: {category_en}")
                continue

            logger.info(f"📝 요약 완료: {len(script)}자")

            # ElevenLabs로 TTS 변환 → S3 Presigned URL 생성
            try:
                audio_bytes = text_to_speech(script)
                audio_url = upload_audio_to_s3_presigned(
                    file_bytes=audio_bytes,
                    user_id="shared",
                    category=category_en,
                    date=date,
                    expires_in_seconds=604800  # 🔧 Presigned URL 7일 유효 (24시간 → 7일)
                )
                logger.info(f"🔊 TTS Presigned URL 생성 완료")
            except Exception as e:
                logger.warning(f"[TTS 업로드 실패] {category_en}: {str(e)}")
                continue

            # 결과 DynamoDB에 저장
            item = {
                "frequency_id": freq_id,
                "category": category_en,
                "date": date,
                "script": script,
                "audio_url": audio_url,
                "created_at": datetime.utcnow().isoformat()
            }

            save_frequency_summary(item)
            logger.info(f"✅ DynamoDB 저장 완료: {category_en} ({freq_id})")

        except Exception as e:
            logger.exception(f"[❌ {category_en} 처리 실패] {str(e)}")