from fastapi import APIRouter, Depends, HTTPException
from app.utils.jwt_service import get_current_user
from app.utils.dynamo import get_user, save_user
from app.constants.category_map import CATEGORY_KO_LIST

#  카테고리 관련 라우터 설정 (prefix: /api)
router = APIRouter(prefix="/api", tags=["Categories"])

#  [GET] /api/categories
@router.get("/categories")
def get_all_categories():
    """
    전체 카테고리 목록을 반환합니다.
    - 프론트 온보딩/프로필 설정 페이지에서 사용
    """
    return {"categories": CATEGORY_KO_LIST}

#  [GET] /api/user/categories
@router.get("/user/categories")
def get_user_categories(user: dict = Depends(get_current_user)):
    """
    로그인된 사용자의 관심 카테고리를 반환합니다.
    - JWT 인증을 통해 사용자 정보 조회
    - 사용자는 복수의 카테고리를 선택할 수 있음
    """
    interests = user.get("interests", [])
    return {"user_id": user["user_id"], "interests": interests}

#  [PUT] /api/user/categories
@router.put("/user/categories")
def update_user_categories(data: dict, user: dict = Depends(get_current_user)):
    """
    로그인된 사용자의 관심 카테고리를 수정합니다.
    - Body 예시: {"interests": ["정치", "경제", "IT/과학"]}
    - 관심사 저장 시 DynamoDB의 Users 테이블에 반영됨
    """
    selected = data.get("interests", [])
    if not isinstance(selected, list):
        raise HTTPException(status_code=400, detail="interests는 리스트여야 합니다")
    
    # 유효한 카테고리인지 검증
    invalid_categories = [cat for cat in selected if cat not in CATEGORY_KO_LIST]
    if invalid_categories:
        raise HTTPException(
            status_code=400, 
            detail=f"지원하지 않는 카테고리입니다: {invalid_categories}"
        )

    user["interests"] = selected
    save_user(user)
    return {"message": "관심 카테고리 업데이트 완료", "interests": selected}
