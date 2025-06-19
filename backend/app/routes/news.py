from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from app.utils.dynamo import (
    get_news_by_category_and_date,
    get_news_card_by_id,
    get_today_news_grouped,
    add_bookmark,
    remove_bookmark
)
from app.utils.jwt_service import get_current_user
from app.constants.category_map import CATEGORY_MAP, REVERSE_CATEGORY_MAP
from typing import List
from datetime import datetime
import pytz
import random

#  /api/news 하위 엔드포인트 그룹
router = APIRouter(prefix="/api/news", tags=["News"])

# 북마크 요청 모델
class BookmarkRequest(BaseModel):
    news_id: str

#  [GET] /api/news?category=xxx (trailing slash 유무 모두 지원)
@router.get("/")
@router.get("")  # trailing slash 없는 경로 추가
def get_news(category: str = Query(..., description="뉴스 카테고리")):
    """
    특정 카테고리의 오늘 뉴스 목록 조회 (최대 10개)

    - 파라미터: category (예: "정치", "경제", "전체")
    - 정렬 기준: 인기순 or 수집순 (현재는 상위 10개 슬라이싱)
    - 사용 예시: '내 뉴스' 탭 등에서 사용자 관심 카테고리별 뉴스 보기
    """
    print(f" 뉴스 조회 요청 - 한글 카테고리: '{category}'")
    
    kst = pytz.timezone("Asia/Seoul")
    today = datetime.now(kst).strftime("%Y-%m-%d")
    print(f" 조회 날짜: {today}")
    
    # '전체' 카테고리인 경우 모든 카테고리의 뉴스를 가져와서 다양하게 섞음
    if category == "전체":
        print(f" 전체 카테고리 뉴스 조회 시작")
        category_news = {}  # 카테고리별로 뉴스를 저장
        
        # 각 카테고리별로 뉴스 수집 (카테고리 순서를 고정)
        for ko_category, config in CATEGORY_MAP.items():
            en_category = config["api_name"]
            try:
                items = get_news_by_category_and_date(en_category, today)
                if items:
                    # 각 카테고리 내에서는 발행 시간 기준으로 정렬 (최신순)
                    sorted_items = sorted(items, key=lambda x: x.get("published_at", ""), reverse=True)
                    # 각 카테고리에서 최대 8개씩만 가져오기 (다양성 확보)
                    selected_items = sorted_items[:8]
                    category_news[ko_category] = selected_items
                else:
                    category_news[ko_category] = []
            except Exception as e:
                category_news[ko_category] = []
        
        # 카테고리별로 라운드로빈 방식으로 균등하게 분배
        mixed_news = []
        max_rounds = max(len(news_list) for news_list in category_news.values()) if category_news.values() else 0
        
        # 카테고리 순서를 고정 (매번 동일한 순서 보장)
        categories = list(CATEGORY_MAP.keys())
        
        for round_num in range(max_rounds):
            # 각 라운드에서 모든 카테고리를 순서대로 처리
            for category_name in categories:
                news_list = category_news[category_name]
                if round_num < len(news_list):
                    news_item = news_list[round_num]
                    # 중복 체크
                    if not any(existing.get("news_id") == news_item.get("news_id") for existing in mixed_news):
                        mixed_news.append(news_item)
        
        # 최대 30개로 제한
        result = mixed_news[:30]
        
        print(f" 전체 뉴스 {len(result)}개 반환 완료")
        
        return result
    
    # 특정 카테고리인 경우 기존 로직 사용
    # 한글 카테고리를 영문으로 변환
    if category in CATEGORY_MAP:
        en_category = CATEGORY_MAP[category]["api_name"]
        print(f" 변환된 영문 카테고리: '{en_category}'")
    else:
        print(f" 지원하지 않는 카테고리: '{category}'")
        print(f" 지원 카테고리 목록: {list(CATEGORY_MAP.keys())} + ['전체']")
        raise HTTPException(status_code=400, detail=f"지원하지 않는 카테고리입니다: {category}")
    
    items = get_news_by_category_and_date(en_category, today)
    
    print(f" 조회된 뉴스 개수: {len(items) if items else 0}")
    
    if not items:
        print(f" '{en_category}' 카테고리에 {today} 날짜 뉴스가 없음")
        return []
    
    result = items[:10]
    print(f" 반환하는 뉴스 개수: {len(result)}")
    
    return result

#  [GET] /api/news/today
@router.get("/today")
def get_today_news():
    """
    오늘의 뉴스 탭: 카테고리별 대표 뉴스 6개씩 그룹핑하여 반환

    - 내부적으로 DynamoDB에서 각 카테고리별 뉴스 6개씩 가져옴
    - 사용 예시: '오늘의 뉴스' 탭에서 전체 카테고리 뉴스 카드 슬라이드 출력
    - 리턴 예시: { "정치": [...6개], "경제": [...6개], ... }
    """
    return get_today_news_grouped()

#  [GET] /api/news/{news_id}
@router.get("/{news_id}")
def get_news_detail(news_id: str):
    """
    개별 뉴스 카드 상세 내용 조회

    - 뉴스 ID를 기준으로 뉴스 상세 데이터 반환
    - content, publisher, summary 등 포함
    - 예외 처리: 존재하지 않으면 404 반환
    """
    item =  get_news_card_by_id(news_id)
    if not item:
        raise HTTPException(status_code=404, detail="뉴스를 찾을 수 없습니다.")
    return item

#  [POST] /api/news/bookmark
@router.post("/bookmark")
def bookmark_news(request: BookmarkRequest, user=Depends(get_current_user)):
    """
    뉴스 북마크 추가

    - 인증 필요
    - 북마크된 뉴스는 사용자 북마크 목록에서 확인 가능
    - 사용 예시: 뉴스 카드의 북마크 버튼 클릭 시
    """
    print(f" 북마크 추가 요청 - 사용자: {user['user_id']}, 뉴스: {request.news_id}")
    add_bookmark(user_id=user["user_id"], news_id=request.news_id)
    return {"message": "북마크 완료"}

#  [DELETE] /api/news/bookmark/{news_id}
@router.delete("/bookmark/{news_id}")
def delete_bookmark(news_id: str, user=Depends(get_current_user)):
    """
    뉴스 북마크 삭제

    - 인증 필요
    - 사용 예시: 북마크 탭 또는 뉴스 카드에서 북마크 해제 버튼 클릭 시
    """
    print(f" 북마크 삭제 요청 - 사용자: {user['user_id']}, 뉴스: {news_id}")
    remove_bookmark(user_id=user["user_id"], news_id=news_id)
    return {"message": "북마크 삭제됨"}
