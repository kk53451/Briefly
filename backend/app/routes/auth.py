from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse, JSONResponse
import os, requests
from datetime import datetime
import time
import urllib.parse

from app.utils.jwt_service import create_access_token, get_current_user
from app.utils.dynamo import save_user, get_user

router = APIRouter(prefix="/api/auth", tags=["Auth"])

KAKAO_CLIENT_ID = os.getenv("KAKAO_CLIENT_ID")
KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI")

# 사용된 코드를 임시 저장 (실제 운영에서는 Redis 등 사용)
used_codes = set()

#  1. 카카오 로그인 URL 리다이렉트
@router.get("/kakao/login")
def kakao_login():
    # state 파라미터로 CSRF 공격 방지 및 세션 구분
    state = f"briefly_{int(time.time())}"
    
    kakao_auth_url = (
        f"https://kauth.kakao.com/oauth/authorize"
        f"?client_id={KAKAO_CLIENT_ID}"
        f"&redirect_uri={KAKAO_REDIRECT_URI}"
        f"&response_type=code"
        f"&state={state}"
    )
    return RedirectResponse(kakao_auth_url)

#  2. 콜백 처리
@router.get("/kakao/callback")
def kakao_callback(code: str):
    print(f" 카카오 콜백 시작")
    print(f" 원본 code: {code}")
    print(f" code 길이: {len(code)}")
    
    # URL 디코딩 시도
    try:
        decoded_code = urllib.parse.unquote(code)
        print(f" 디코딩된 code: {decoded_code}")
        if decoded_code != code:
            print(f" 코드가 URL 인코딩되어 있었음")
            code = decoded_code
    except Exception as e:
        print(f" URL 디코딩 실패: {e}")
    
    # 코드 재사용 체크
    if code in used_codes:
        print(f" 이미 사용된 코드: {code[:20]}...")
        raise HTTPException(
            status_code=400, 
            detail="이 인증 코드는 이미 사용되었습니다. 다시 로그인해주세요."
        )
    
    # 사용된 코드로 마킹
    used_codes.add(code)
    
    print(f" KAKAO_CLIENT_ID: {KAKAO_CLIENT_ID}")
    print(f" KAKAO_REDIRECT_URI: {KAKAO_REDIRECT_URI}")
    
    # 2-1. 토큰 요청
    token_data = {
        "grant_type": "authorization_code",
        "client_id": KAKAO_CLIENT_ID,
        "redirect_uri": KAKAO_REDIRECT_URI,
        "code": code,
    }
    
    print(f" 토큰 요청 데이터: {token_data}")
    
    try:
        token_res = requests.post(
            url="https://kauth.kakao.com/oauth/token",
            data=token_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        
        print(f" 카카오 토큰 응답 상태: {token_res.status_code}")
        print(f" 카카오 토큰 응답 헤더: {dict(token_res.headers)}")
        
        if token_res.status_code != 200:
            print(f" HTTP 오류: {token_res.text}")
            # 실패한 코드를 used_codes에서 제거 (재시도 가능하게)
            used_codes.discard(code)
            raise HTTPException(
                status_code=400, 
                detail=f"카카오 토큰 요청 실패 (HTTP {token_res.status_code}): {token_res.text}"
            )
            
        token_json = token_res.json()
        print(f" 카카오 토큰 응답: {token_json}")
        
    except requests.exceptions.RequestException as e:
        print(f" 네트워크 오류: {str(e)}")
        # 네트워크 오류시에도 코드 재사용 가능하게
        used_codes.discard(code)
        raise HTTPException(status_code=500, detail="카카오 서버 연결 실패")
    
    access_token = token_json.get("access_token")

    if not access_token:
        error_description = token_json.get("error_description", "알 수 없는 오류")
        error_code = token_json.get("error", "unknown_error")
        print(f" 토큰 발급 실패 - error: {error_code}, description: {error_description}")
        
        # 특정 오류에 대한 사용자 친화적 메시지
        if error_code == "invalid_grant":
            detail = "인증 코드가 만료되었거나 이미 사용되었습니다. 다시 로그인해주세요."
        elif error_code == "invalid_client":
            detail = "카카오 앱 설정에 문제가 있습니다."
        else:
            detail = f"카카오 로그인 실패: {error_description}"
            
        raise HTTPException(status_code=400, detail=detail)

    # 2-2. 사용자 정보 요청
    profile_res = requests.get(
        url="https://kapi.kakao.com/v2/user/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    profile_json = profile_res.json()

    kakao_id = profile_json.get("id")
    kakao_account = profile_json.get("kakao_account", {})
    nickname = kakao_account.get("profile", {}).get("nickname")
    profile_image = kakao_account.get("profile", {}).get("profile_image_url", "")

    if not kakao_id or not nickname:
        raise HTTPException(status_code=400, detail="카카오 사용자 정보 조회 실패")

    # 2-3. DB 저장
    user_id = f"kakao_{kakao_id}"
    user = get_user(user_id)  #  get_user가 None 반환하도록 구성 필요

    if user is None:
        print(f" 신규 사용자 생성: {user_id}")
        save_user({
            "user_id": user_id,
            "nickname": nickname,
            "profile_image": profile_image,
            "created_at": datetime.utcnow().isoformat(),
            "interests": [],
            "onboarding_completed": False,
        })
        user = get_user(user_id)
    else:
        # 기존 사용자의 경우에도 카카오에서 받은 최신 정보로 업데이트
        print(f" 기존 사용자 정보 업데이트: {user_id}")
        user["nickname"] = nickname
        user["profile_image"] = profile_image
        save_user(user)

    if not user or "nickname" not in user:
        raise HTTPException(status_code=500, detail="사용자 저장 실패")

    # 2-4. JWT 토큰 발급
    jwt_token = create_access_token(user_id)
    return JSONResponse({
        "access_token": jwt_token,
        "user_id": user_id,
        "nickname": user["nickname"]
    })

#  3. 사용자 정보 조회
@router.get("/me")
def auth_me(user: dict = Depends(get_current_user)):
    return user

#  4. 로그아웃
@router.post("/logout")
def logout():
    return {"message": "로그아웃 완료 (클라이언트 토큰 삭제 권장)"}
