# app/tasks/generate_frequency.py

import logging
from datetime import datetime
import concurrent.futures
import time

from app.utils.date import get_today_kst
from app.utils.dynamo import (
    save_frequency_summary,
    get_frequency_by_category_and_date,
    get_news_by_category_and_date,
    update_news_card_content,
)
from app.services.openai_service import summarize_articles, cluster_similar_texts, summarize_group
from app.services.tts_service import text_to_speech
from app.utils.s3 import upload_audio_to_s3_presigned
from app.constants.category_map import CATEGORY_MAP
from app.services.deepsearch_service import extract_content_flexibly

# 로그 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def process_single_category(category_ko: str, date: str) -> dict:
    """
    단일 카테고리 처리 함수 (병렬 처리용)
    """
    category_en = CATEGORY_MAP[category_ko]["api_name"]
    freq_id = f"{category_en}#{date}"
    start_time = time.time()
    
    try:
        # 중복 방지: 이미 생성된 경우 스킵
        if get_frequency_by_category_and_date(category_en, date):
            logger.info(f"🚫 이미 생성됨 → 스킵: {freq_id}")
            return {"category": category_en, "status": "skipped", "reason": "already_exists"}

        logger.info(f"🔄 [{category_en}] 대본/음성 생성 시작")

        # 해당 카테고리의 오늘 기사 불러오기
        articles = get_news_by_category_and_date(category_en, date)
        logger.info(f"📥 [{category_en}] 수집된 기사 수: {len(articles)}")

        full_contents = []
        processed_count = 0
        target_count = 30  # 정확히 30개로 제한

        # 기사 본문 정확히 30개까지 수집
        for i, article in enumerate(articles):
            if len(full_contents) >= target_count:
                logger.info(f"🎯 [{category_en}] 목표 달성: {target_count}개 수집 완료")
                break
                
            processed_count += 1
            news_id = article.get("news_id")
            url = article.get("content_url")
            content = article.get("content", "").strip()

            if not news_id or not url:
                logger.warning(f"⚠️ [{category_en}] #{processed_count} URL 또는 ID 없음 → 스킵")
                continue

            # 본문이 짧거나 없으면 재추출 시도
            if not content or len(content) < 300:
                try:
                    content = extract_content_flexibly(url)
                    if content and len(content) >= 300:
                        update_news_card_content(news_id, content)
                        logger.info(f"♻️ [{category_en}] #{processed_count} 본문 보완 저장 완료 ({len(content)}자)")
                    else:
                        logger.warning(f"⚠️ [{category_en}] #{processed_count} 본문 추출 실패 또는 너무 짧음 → 스킵")
                        continue
                except Exception as e:
                    logger.warning(f"❌ [{category_en}] #{processed_count} 본문 재추출 중 오류: {e}")
                    continue

            # 🔧 토큰 최적화: 3000자 → 1500자로 단축
            trimmed = content[:1500]
            full_contents.append(trimmed)
            logger.info(f"✅ [{category_en}] #{len(full_contents)} 본문 사용 완료 ({len(trimmed)}자)")

        logger.info(f"📊 [{category_en}] 최종 수집된 기사 수: {len(full_contents)}개 (목표: {target_count}개)")

        # 본문 수가 너무 적으면 스킵
        if len(full_contents) < 5:
            logger.warning(f"⚠️ [{category_en}] 유효 본문 부족 ({len(full_contents)}개) → 스킵")
            return {"category": category_en, "status": "failed", "reason": "insufficient_content"}

        # ⭐️ [1차 클러스터링] 원본 기사 본문 기반 물리적 중복 제거
        logger.info(f"🔄 [{category_en}] 1차 클러스터링 시작: {len(full_contents)}개 기사")
        try:
            groups = cluster_similar_texts(full_contents, threshold=0.80)
            group_summaries = []
            
            for group_idx, group in enumerate(groups):
                if len(group) == 1:
                    # 단일 기사는 그대로 사용
                    group_summaries.append(group[0])
                    logger.info(f"📄 [{category_en}] 그룹 #{group_idx+1}: 단일 기사 ({len(group[0])}자)")
                else:
                    # 여러 유사 기사 → 대표 요약문 생성
                    try:
                        summary = summarize_group(group, category_en)
                        group_summaries.append(summary)
                        logger.info(f"📊 [{category_en}] 그룹 #{group_idx+1}: {len(group)}개 기사 → 통합 요약 ({len(summary)}자)")
                    except Exception as e:
                        logger.warning(f"⚠️ [{category_en}] 그룹 #{group_idx+1} 요약 실패, 첫 번째 기사 사용: {e}")
                        group_summaries.append(group[0])
            
            logger.info(f"✅ [{category_en}] 1차 클러스터링 완료: {len(full_contents)}개 → {len(group_summaries)}개 그룹")
            final_contents = group_summaries
            
        except Exception as e:
            logger.warning(f"⚠️ [{category_en}] 1차 클러스터링 실패, 원본 기사 사용: {e}")
            final_contents = full_contents

        # GPT로 종합 스크립트 생성 (2차 클러스터링 포함)
        logger.info(f"📝 [{category_en}] 대본 생성 시작: {len(final_contents)}개 기사")
        script = summarize_articles(final_contents, category_en)
        if not script or len(script) < 500:
            logger.warning(f"⚠️ [{category_en}] 요약 길이 부족 → 스킵")
            return {"category": category_en, "status": "failed", "reason": "summary_too_short"}

        logger.info(f"📝 [{category_en}] 요약 완료: {len(script)}자")

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
            logger.info(f"🔊 [{category_en}] TTS Presigned URL 생성 완료")
        except Exception as e:
            logger.warning(f"❌ [{category_en}] TTS 업로드 실패: {str(e)}")
            return {"category": category_en, "status": "failed", "reason": f"tts_failed: {str(e)}"}

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
        
        elapsed_time = time.time() - start_time
        logger.info(f"✅ [{category_en}] DynamoDB 저장 완료 (소요시간: {elapsed_time:.1f}초)")
        
        return {
            "category": category_en, 
            "status": "success", 
            "script_length": len(script),
            "elapsed_time": elapsed_time
        }

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.exception(f"❌ [{category_en}] 처리 실패 (소요시간: {elapsed_time:.1f}초): {str(e)}")
        return {
            "category": category_en, 
            "status": "failed", 
            "reason": f"exception: {str(e)}",
            "elapsed_time": elapsed_time
        }

def generate_all_frequencies():
    """
    ✅ 매일 오전 6시 자동 실행: 카테고리별 뉴스 본문 기반 공유 대본/음성 생성 (병렬 처리)
    - 뉴스카드 DB에서 카테고리별 기사 정확히 30개 사용 (토큰 최적화)
    - 부족한 본문은 재추출
    - GPT 요약하여 스크립트 생성 (클러스터링 포함)
    - ElevenLabs TTS로 변환 후 S3 업로드
    - Frequencies 테이블에 저장 (스크립트 + Presigned MP3 링크)
    """
    date = get_today_kst()
    all_categories = list(CATEGORY_MAP.keys())
    total_start_time = time.time()
    
    logger.info(f"🚀 병렬 처리 시작: {len(all_categories)}개 카테고리 동시 처리")
    logger.info(f"📋 카테고리 목록: {all_categories}")

    # 🚀 병렬 처리: ThreadPoolExecutor 사용
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:  # 5개 동시 처리
        # 각 카테고리를 병렬로 처리하는 Future 객체 생성
        future_to_category = {
            executor.submit(process_single_category, category_ko, date): category_ko 
            for category_ko in all_categories
        }
        
        # 완료된 순서대로 결과 수집
        for future in concurrent.futures.as_completed(future_to_category):
            category_ko = future_to_category[future]
            try:
                result = future.result()
                results.append(result)
                
                if result["status"] == "success":
                    logger.info(f"🎉 [{result['category']}] 성공 완료 - 대본: {result['script_length']}자, 소요시간: {result['elapsed_time']:.1f}초")
                elif result["status"] == "skipped":
                    logger.info(f"⏭️ [{result['category']}] 스킵됨 - 사유: {result['reason']}")
                else:
                    logger.warning(f"⚠️ [{result['category']}] 실패 - 사유: {result['reason']}")
                    
            except Exception as exc:
                logger.exception(f"❌ [{category_ko}] 예상치 못한 오류: {exc}")
                results.append({
                    "category": CATEGORY_MAP[category_ko]["api_name"], 
                    "status": "failed", 
                    "reason": f"executor_exception: {str(exc)}"
                })

    # 📊 전체 결과 요약
    total_elapsed_time = time.time() - total_start_time
    success_count = sum(1 for r in results if r["status"] == "success")
    failed_count = sum(1 for r in results if r["status"] == "failed")
    skipped_count = sum(1 for r in results if r["status"] == "skipped")
    
    logger.info(f"🏁 병렬 처리 완료!")
    logger.info(f"⏱️ 총 소요시간: {total_elapsed_time:.1f}초")
    logger.info(f"📊 결과 요약: 성공 {success_count}개, 실패 {failed_count}개, 스킵 {skipped_count}개")
    
    # 각 카테고리별 상세 결과 로그
    for result in results:
        status_emoji = {"success": "✅", "failed": "❌", "skipped": "⏭️"}.get(result["status"], "❓") 
        logger.info(f"{status_emoji} {result['category']}: {result['status']}")
        if "reason" in result:
            logger.info(f"   └─ 사유: {result['reason']}")

    return results