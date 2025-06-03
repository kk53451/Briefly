from fastapi import APIRouter, Depends, HTTPException, Query
from app.utils.jwt_service import get_current_user
from app.utils.dynamo import get_frequency_by_category_and_date, get_frequency_history_by_categories
from app.utils.date import get_today_kst
from app.constants.category_map import CATEGORY_MAP

# ✅ /api/frequencies 엔드포인트 그룹
router = APIRouter(prefix="/api/frequencies", tags=["Frequency"])

# ✅ [GET] /api/frequencies
@router.get("")
def get_frequencies(user: dict = Depends(get_current_user)):
    """
    오늘 날짜 기준으로 사용자의 관심 카테고리별 공유 요약(TTS 스크립트 및 오디오)을 반환합니다.
    
    - 각 카테고리에 대해, 시스템이 사전에 생성해둔 공유 주파수를 DynamoDB에서 가져옵니다.
    - 프론트에서는 사용자 관심사 기반의 오디오 목록 뷰에 사용됩니다.
    - 리턴: [{category, script, audio_url, ...}, ...]
    """
    date = get_today_kst()
    results = []

    for korean_category in user.get("interests", []):
        # 한국어 카테고리를 영어 카테고리로 변환
        if korean_category in CATEGORY_MAP:
            english_category = CATEGORY_MAP[korean_category]["api_name"]
            item = get_frequency_by_category_and_date(english_category, date)
            if item:
                results.append(item)

    return results

# ✅ [GET] /api/frequencies/history
@router.get("/history")
def get_frequency_history(
    user: dict = Depends(get_current_user),
    limit: int = Query(default=30, ge=1, le=100, description="조회할 히스토리 개수 (최대 100)")
):
    """
    사용자의 관심 카테고리별 주파수 히스토리를 반환합니다.
    
    - 사용자의 관심 카테고리에 해당하는 과거 주파수 데이터를 날짜순으로 정렬하여 반환
    - 오늘 날짜는 제외하고 과거 데이터만 반환
    - 리턴: [{frequency_id, category, script, audio_url, date, created_at}, ...]
    """
    user_interests = user.get("interests", [])
    if not user_interests:
        return []
    
    # 한국어 카테고리를 영어로 변환
    english_categories = []
    for korean_category in user_interests:
        if korean_category in CATEGORY_MAP:
            english_categories.append(CATEGORY_MAP[korean_category]["api_name"])
    
    if not english_categories:
        return []
    
    # 전체 히스토리 조회
    all_history = get_frequency_history_by_categories(english_categories, limit + 10)  # 여유분 확보
    
    # 오늘 날짜 제외
    today = get_today_kst()
    past_history = [item for item in all_history if item.get("date") != today]
    
    # 제한 개수만 반환
    return past_history[:limit]

# ✅ [GET] /api/frequencies/{category}
@router.get("/{category}")
def get_frequency_detail(category: str, user: dict = Depends(get_current_user)):
    """
    특정 카테고리에 대한 공유 주파수 상세 정보를 조회합니다.
    
    - 사용자는 관심 카테고리에 상관없이 직접 카테고리 detail 접근 가능
    - 공유된 script (요약 텍스트) 및 audio_url (MP3) 정보를 반환
    - 예외 처리: 해당 카테고리에 오늘자 데이터가 없을 경우 404 반환
    """
    date = get_today_kst()
    
    # 카테고리가 한국어인 경우 영어로 변환
    if category in CATEGORY_MAP:
        english_category = CATEGORY_MAP[category]["api_name"]
    else:
        # 이미 영어 카테고리인 경우 그대로 사용
        english_category = category
    
    result = get_frequency_by_category_and_date(english_category, date)
    if not result:
        raise HTTPException(status_code=404, detail="해당 주파수가 없습니다.")
    return result
