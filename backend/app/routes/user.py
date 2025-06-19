from fastapi import APIRouter, Depends, HTTPException
from app.utils.jwt_service import get_current_user
from app.utils.dynamo import (
    get_user,
    save_user,
    get_user_bookmarks,
    get_frequency_by_category_and_date  #  공유 스크립트 기반
)
from app.utils.date import get_today_kst

#  /api/user 하위 엔드포인트 그룹
router = APIRouter(prefix="/api/user", tags=["User"])

#  [GET] /api/user/profile
@router.get("/profile")
def get_profile(user: dict = Depends(get_current_user)):
    """
    로그인된 사용자 프로필 정보 조회

    - 응답 항목: user_id, nickname, profile_image, interests, onboarding_completed 등
    - 사용 예시: 마이페이지 진입 시 프로필 렌더링
    """
    return user

#  [PUT] /api/user/profile
@router.put("/profile")
def update_profile(
    nickname: str = None,
    default_length: int = None,
    profile_image: str = None,
    user: dict = Depends(get_current_user)
):
    """
    사용자 프로필 정보 수정

    - 파라미터는 선택적(nickname, default_length, profile_image)
    - 수정된 값만 업데이트
    - 사용 예시: 프로필 편집 UI 저장 시
    """
    if nickname:
        user["nickname"] = nickname
    if default_length:
        user["default_length"] = default_length
    if profile_image:
        user["profile_image"] = profile_image

    save_user(user)
    return {"message": "프로필이 업데이트되었습니다."}

#  [GET] /api/user/bookmarks
@router.get("/bookmarks")
def get_bookmarks(user: dict = Depends(get_current_user)):
    """
    사용자가 북마크한 뉴스 목록 조회

    - 응답: 북마크한 뉴스 카드 배열
    - 사용 예시: 북마크 탭 또는 프로필의 '내 뉴스' 섹션
    """
    return get_user_bookmarks(user["user_id"])

#  [GET] /api/user/frequencies
@router.get("/frequencies")
def get_my_frequencies(user: dict = Depends(get_current_user)):
    """
    사용자의 관심 카테고리별 공유 주파수 요약(TTS 스크립트 및 오디오) 조회

    - 오늘 날짜 기준
    - 사용 예시: '내 주파수' 탭 진입 시 자동 조회
    """
    today = get_today_kst()
    results = []

    for category in user.get("interests", []):
        item = get_frequency_by_category_and_date(category, today)
        if item:
            results.append(item)

    return results

#  [GET] /api/user/categories
@router.get("/categories")
def get_my_categories(user: dict = Depends(get_current_user)):
    """
    사용자의 관심 카테고리 목록 조회

    - 사용 예시: 온보딩 화면 또는 마이페이지 → 카테고리 설정
    """
    return {"interests": user.get("interests", [])}

#  [PUT] /api/user/categories
@router.put("/categories")
def update_my_categories(interests: list[str], user: dict = Depends(get_current_user)):
    """
    사용자의 관심 카테고리 목록 수정

    - 파라미터: interests (한글 카테고리명 리스트)
    - 사용 예시: 온보딩 완료 시, 마이페이지 카테고리 수정 시
    """
    user["interests"] = interests
    save_user(user)
    return {"message": "관심 카테고리가 업데이트되었습니다."}

#  [POST] /api/user/onboarding
@router.post("/onboarding")
def complete_onboarding(user: dict = Depends(get_current_user)):
    """
    온보딩 완료 처리 (첫 설정 이후 호출)

    - user["onboarding_completed"] = True 플래그 설정
    """
    user["onboarding_completed"] = True
    save_user(user)
    return {"message": "온보딩 완료"}

#  [GET] /api/user/onboarding/status
@router.get("/onboarding/status")
def onboarding_status(user: dict = Depends(get_current_user)):
    """
    온보딩 완료 여부 확인

    - 응답: { onboarded: True/False }
    - 사용 예시: 최초 진입 시 온보딩 화면 띄울지 판단
    """
    return {"onboarded": user.get("onboarding_completed", False)}

#  [GET] /onboarding - 프론트엔드 요청 대응
@router.get("/onboarding")
def get_onboarding_page(user: dict = Depends(get_current_user)):
    """
    온보딩 페이지 정보 제공

    - 온보딩 완료 여부와 사용자 기본 정보 반환
    - 사용 예시: 프론트엔드에서 /onboarding 페이지 진입 시
    """
    return {
        "user_id": user["user_id"],
        "nickname": user.get("nickname", ""),
        "onboarding_completed": user.get("onboarding_completed", False),
        "interests": user.get("interests", [])
    }


