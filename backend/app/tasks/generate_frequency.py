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
from app.services.content_scraper import extract_content_flexibly

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

    # 로그 버퍼 (카테고리별로 모아서 한 번에 출력)
    log_buffer = []

    def add_log(message, level="INFO"):
        """로그를 버퍼에 추가"""
        log_buffer.append({"level": level, "message": message})

    def flush_logs():
        """버퍼에 모인 로그 일괄 출력"""
        for log in log_buffer:
            if log["level"] == "WARNING":
                logger.warning(log["message"])
            elif log["level"] == "ERROR":
                logger.error(log["message"])
            else:
                logger.info(log["message"])

    try:
        add_log(f"\n{'='*70}")
        add_log(f"📰 [{category_en.upper()}] 대본 생성 시작")
        add_log(f"{'='*70}")

        # 중복 방지: 이미 생성된 경우 스킵
        if get_frequency_by_category_and_date(category_en, date):
            add_log(f"🚫 이미 생성됨 → 스킵")
            flush_logs()
            return {"category": category_en, "status": "skipped", "reason": "already_exists"}

        # 해당 카테고리의 오늘 기사 불러오기
        add_log(f"\n[1단계] 기사 수집")
        articles = get_news_by_category_and_date(category_en, date)
        add_log(f"  - DB에서 불러온 기사: {len(articles)}개")

        full_contents = []
        articles_metadata = []  # 기사 메타데이터 (제목, 길이 등)
        processed_count = 0
        target_count = 30  # 정확히 30개로 제한

        # 기사 본문 정확히 30개까지 수집
        for i, article in enumerate(articles):
            if len(full_contents) >= target_count:
                add_log(f"  - 목표 달성: {target_count}개 수집 완료")
                break

            processed_count += 1
            news_id = article.get("news_id")
            url = article.get("provider_link_page")
            title = article.get("title", "제목 없음")[:40]  # DynamoDB 필드명: title
            content = article.get("content", "").strip()

            if not news_id or not url:
                add_log(f"  - #{processed_count} URL 또는 ID 없음 → 스킵", "WARNING")
                continue

            # 본문이 짧거나 없으면 재추출 시도
            if not content or len(content) < 300:
                try:
                    content = extract_content_flexibly(url)
                    if content and len(content) >= 300:
                        update_news_card_content(news_id, content)
                    else:
                        add_log(f"  - #{processed_count} 본문 추출 실패 또는 너무 짧음 → 스킵", "WARNING")
                        continue
                except Exception as e:
                    add_log(f"  - #{processed_count} 본문 재추출 중 오류: {e}", "WARNING")
                    continue

            # 토큰 최적화: 1500자로 제한
            trimmed = content[:1500]
            full_contents.append(trimmed)
            articles_metadata.append({
                "title": title,
                "length": len(trimmed),
                "index": len(full_contents) - 1
            })

        add_log(f"  - 최종 수집: {len(full_contents)}개 기사 (목표: {target_count}개)")

        # 본문 수가 너무 적으면 스킵
        if len(full_contents) < 5:
            add_log(f"❌ 유효 본문 부족 ({len(full_contents)}개) → 스킵", "WARNING")
            flush_logs()
            return {"category": category_en, "status": "failed", "reason": "insufficient_content"}

        # 클러스터링: 원본 기사 본문 기반 물리적 중복 제거
        add_log(f"\n[2단계] 클러스터링 (Greedy threshold=0.80)")
        add_log(f"  - 입력: {len(full_contents)}개 기사")

        clustering_start = time.time()
        try:
            groups = cluster_similar_texts(full_contents, threshold=0.80)
            clustering_time = time.time() - clustering_start

            group_summaries = []
            merged_groups = 0
            cluster_details = []

            for group_idx, group in enumerate(groups):
                if len(group) == 1:
                    # 단일 기사는 그대로 사용
                    group_summaries.append(group[0])
                    cluster_details.append({
                        "cluster_id": group_idx + 1,
                        "size": 1,
                        "merged": False
                    })
                else:
                    # 여러 유사 기사 → 대표 요약문 생성
                    try:
                        # 클러스터에 속한 기사 제목들 찾기
                        merged_titles = []
                        for content in group[:5]:  # 최대 5개까지만 제목 수집
                            # 원본 인덱스 찾기 (content가 full_contents에서 몇 번째인지)
                            try:
                                idx = full_contents.index(content)
                                if idx < len(articles_metadata):
                                    merged_titles.append(articles_metadata[idx]["title"])
                            except (ValueError, IndexError):
                                pass

                        summary = summarize_group(group, category_en)
                        group_summaries.append(summary)
                        merged_groups += 1

                        cluster_details.append({
                            "cluster_id": group_idx + 1,
                            "size": len(group),
                            "merged": True,
                            "titles": merged_titles[:3]  # 로그에는 최대 3개만
                        })
                    except Exception as e:
                        add_log(f"  - 클러스터 #{group_idx+1} 요약 실패, 첫 번째 기사 사용: {e}", "WARNING")
                        group_summaries.append(group[0])
                        cluster_details.append({
                            "cluster_id": group_idx + 1,
                            "size": len(group),
                            "merged": False
                        })

            # 압축률 계산
            compression_rate = ((len(full_contents) - len(group_summaries)) / len(full_contents)) * 100 if len(full_contents) > 0 else 0

            add_log(f"  - 출력: {len(group_summaries)}개 그룹")
            add_log(f"  - 통합된 클러스터: {merged_groups}개")
            add_log(f"  - 압축률: {compression_rate:.1f}%")
            add_log(f"  - 처리 시간: {clustering_time:.2f}초")

            # 통합된 클러스터 상세 정보 출력 (최대 3개)
            merged_clusters = [c for c in cluster_details if c["merged"]]
            if merged_clusters:
                add_log(f"  - 통합 클러스터 상세:")
                for cluster in merged_clusters[:3]:
                    titles = cluster.get("titles", [])
                    if titles:
                        add_log(f"    클러스터 {cluster['cluster_id']}: {cluster['size']}개 통합")
                        for idx, title in enumerate(titles, 1):
                            add_log(f"      {idx}. {title}")
                    else:
                        add_log(f"    클러스터 {cluster['cluster_id']}: {cluster['size']}개 통합")

            final_contents = group_summaries

        except Exception as e:
            add_log(f"  - 클러스터링 실패, 원본 기사 사용: {e}", "WARNING")
            final_contents = full_contents

        # GPT로 종합 스크립트 생성
        add_log(f"\n[3단계] GPT 대본 생성")
        add_log(f"  - 입력: {len(final_contents)}개 요약문")

        gpt_start = time.time()
        script = summarize_articles(final_contents, category_en)
        gpt_time = time.time() - gpt_start

        if not script or len(script) < 500:
            add_log(f"❌ 대본 길이 부족 ({len(script) if script else 0}자) → 스킵", "WARNING")
            flush_logs()
            return {"category": category_en, "status": "failed", "reason": "summary_too_short"}

        add_log(f"  - 출력: {len(script)}자")
        add_log(f"  - 처리 시간: {gpt_time:.2f}초")

        # 스크립트 DynamoDB에 저장 (TTS 없이 먼저 저장)
        add_log(f"\n[4단계] DynamoDB 저장")
        item = {
            "frequency_id": freq_id,
            "category": category_en,
            "date": date,
            "script": script,
            "created_at": datetime.utcnow().isoformat()
        }
        save_frequency_summary(item)
        add_log(f"  - 저장 완료: {freq_id}")

        elapsed_time = time.time() - start_time

        add_log(f"\n{'='*70}")
        add_log(f"✅ [{category_en.upper()}] 완료")
        add_log(f"{'='*70}")
        add_log(f"  - 총 소요시간: {elapsed_time:.1f}초")
        add_log(f"  - 대본 길이: {len(script)}자")
        add_log(f"  - 압축률: {compression_rate:.1f}% ({len(full_contents)}개 → {len(group_summaries)}개)")

        flush_logs()

        return {
            "category": category_en,
            "status": "success",
            "script_length": len(script),
            "elapsed_time": elapsed_time,
            "compression_rate": compression_rate
        }

        # # ElevenLabs로 TTS 변환 → S3 Presigned URL 생성 (임시 비활성화)
        # logger.info(f"[{category_en}] TTS 음성 생성 시작...")
        # try:
        #     audio_bytes = text_to_speech(script)
        #     audio_url = upload_audio_to_s3_presigned(
        #         file_bytes=audio_bytes,
        #         user_id="shared",
        #         category=category_en,
        #         date=date,
        #         expires_in_seconds=604800  # Presigned URL 7일 유효 (24시간에서 7일로 연장)
        #     )
        #     logger.info(f"  └─ TTS 음성 생성 완료 → S3 업로드")
        # except Exception as e:
        #     logger.warning(f"❌ [{category_en}] TTS 실패: {str(e)}")
        #     return {"category": category_en, "status": "failed", "reason": f"tts_failed: {str(e)}"}

        # # 결과 DynamoDB에 저장
        # item = {
        #     "frequency_id": freq_id,
        #     "category": category_en,
        #     "date": date,
        #     "script": script,
        #     "audio_url": audio_url,
        #     "created_at": datetime.utcnow().isoformat()
        # }

        # save_frequency_summary(item)

        # elapsed_time = time.time() - start_time
        # logger.info(f"✅ [{category_en}] 완료 → 대본: {len(script)}자, TTS 생성, DynamoDB 저장 (소요시간: {elapsed_time:.1f}초)")

        # return {
        #     "category": category_en,
        #     "status": "success",
        #     "script_length": len(script),
        #     "elapsed_time": elapsed_time
        # }

    except Exception as e:
        elapsed_time = time.time() - start_time
        add_log(f"\n{'='*70}", "ERROR")
        add_log(f"❌ [{category_en.upper()}] 처리 실패", "ERROR")
        add_log(f"{'='*70}", "ERROR")
        add_log(f"  - 오류: {str(e)}", "ERROR")
        add_log(f"  - 소요시간: {elapsed_time:.1f}초", "ERROR")
        flush_logs()
        logger.exception(f"[{category_en}] 상세 오류:")
        return {
            "category": category_en,
            "status": "failed",
            "reason": f"exception: {str(e)}",
            "elapsed_time": elapsed_time
        }

def generate_all_frequencies():
    """
    매일 오전 6시 자동 실행: 카테고리별 뉴스 본문 기반 공유 대본/음성 생성 (병렬 처리)
    - 뉴스카드 DB에서 카테고리별 기사 정확히 30개 사용 (토큰 최적화)
    - 부족한 본문은 재추출
    - 클러스터링으로 중복 제거 후 GPT 요약하여 스크립트 생성
    - ElevenLabs TTS로 변환 후 S3 업로드
    - Frequencies 테이블에 저장 (스크립트 + Presigned MP3 링크)
    """
    date = get_today_kst()
    all_categories = list(CATEGORY_MAP.keys())
    total_start_time = time.time()
    
    logger.info(f"병렬 처리 시작: {len(all_categories)}개 카테고리 동시 처리")
    logger.info(f"카테고리 목록: {all_categories}")

    # 병렬 처리: ThreadPoolExecutor 사용
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:  # ElevenLabs Concurrency limit(5)에 맞춰 설정
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
                    logger.info(f"[{result['category']}] 성공 완료 - 대본: {result['script_length']}자, 소요시간: {result['elapsed_time']:.1f}초")
                elif result["status"] == "skipped":
                    logger.info(f"[{result['category']}] 스킵됨 - 사유: {result['reason']}")
                else:
                    logger.warning(f"[{result['category']}] 실패 - 사유: {result['reason']}")
                    
            except Exception as exc:
                logger.exception(f"[{category_ko}] 예상치 못한 오류: {exc}")
                results.append({
                    "category": CATEGORY_MAP[category_ko]["api_name"], 
                    "status": "failed", 
                    "reason": f"executor_exception: {str(exc)}"
                })

    # 전체 결과 요약
    total_elapsed_time = time.time() - total_start_time
    success_count = sum(1 for r in results if r["status"] == "success")
    failed_count = sum(1 for r in results if r["status"] == "failed")
    skipped_count = sum(1 for r in results if r["status"] == "skipped")
    
    logger.info("병렬 처리 완료!")
    logger.info(f"총 소요시간: {total_elapsed_time:.1f}초")
    logger.info(f"결과 요약: 성공 {success_count}개, 실패 {failed_count}개, 스킵 {skipped_count}개")
    
    # 각 카테고리별 상세 결과 로그
    for result in results:
        status_text = {"success": "SUCCESS", "failed": "FAILED", "skipped": "SKIPPED"}.get(result["status"], "UNKNOWN")
        logger.info(f"{status_text} {result['category']}: {result['status']}")
        if "reason" in result:
            logger.info(f"   └─ 사유: {result['reason']}")

    return results