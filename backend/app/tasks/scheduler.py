# app/tasks/scheduler.py

import logging
import traceback
from app.utils.date import get_today_kst

#  로깅 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# httpx, httpcore 로깅 비활성화 (과도한 HTTP Request 로그 방지)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

def lambda_handler(event, context):
    """
     AWS EventBridge → Lambda 트리거 함수 (매일 오전 6시 자동 실행)
    - 오늘의 뉴스 수집 (collect_today_news)
    - 카테고리별 종합 요약 + TTS 생성 (generate_all_frequencies)
    - 결과 로그 및 요약 반환
    """

    logger.info(" Lambda 트리거 시작")
    today = get_today_kst()
    logger.info(f" 기준 날짜: {today}")

    # 결과 요약용 딕셔너리 초기화
    result_summary = {
        "news": " 실패",
        "frequency": " 실패"
    }

    #  1단계: 오늘의 뉴스 수집
    try:
        logger.info("뉴스 수집 시작")
        from app.tasks.collect_news import collect_today_news
        collect_today_news()
        result_summary["news"] = " 완료"
        logger.info(" 뉴스 수집 완료")
    except ImportError as e:
        logger.error(f"[뉴스 수집 모듈 오류] {e}")
        logger.error(traceback.format_exc())
    except MemoryError as e:
        logger.error(f"[뉴스 수집 메모리 부족] {e}")
        logger.error(traceback.format_exc())
    except Exception as e:
        logger.error(f"[뉴스 수집 예상치 못한 오류] {e}")
        logger.error(traceback.format_exc())

    #  2단계: 주파수 요약(TTS 포함) 생성
    try:
        logger.info("🎧 주파수 요약 생성 시작")
        from app.tasks.generate_frequency import generate_all_frequencies
        generate_all_frequencies()
        result_summary["frequency"] = " 완료"
        logger.info(" 주파수 요약 생성 완료")
    except ImportError as e:
        logger.error(f"[주파수 생성 모듈 오류] {e}")
        logger.error(traceback.format_exc())
    except MemoryError as e:
        logger.error(f"[주파수 생성 메모리 부족] {e}")
        logger.error(traceback.format_exc())
    except Exception as e:
        logger.error(f"[주파수 생성 예상치 못한 오류] {e}")
        logger.error(traceback.format_exc())

    logger.info(f"📦 작업 결과 요약: {result_summary}")

    return {
        "statusCode": 200,
        "body": {
            "message": f"Lambda 작업 완료: {today}",
            "result": result_summary
        }
    }