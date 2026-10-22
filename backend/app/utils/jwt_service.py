# app/utils/jwt_service.py

import os
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# PyJWT 라이브러리를 직접 import
try:
    import jwt
except ImportError:
    raise ImportError("PyJWT 라이브러리가 설치되어 있지 않습니다. 'pip install PyJWT'를 실행하세요.")

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-prod")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", 60))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

# 현재는 인증을 생략하고 모든 사용자를 게스트로 취급합니다.
# 추후 정식 인증(이메일, Google, Apple 등) 추가 시 이 모듈을 교체하세요.
DEFAULT_GUEST_USER = {
    "user_id": "guest",
    "nickname": "게스트",
    "interests": ["정치", "경제", "사회", "문화", "국제", "IT/과학"],
    "onboarding_completed": True,
}


def create_access_token(user_id: str) -> str:
    """주어진 user_id로 JWT 토큰 생성 (기존 인터페이스 호환용)"""
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    try:
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"JWT 토큰 생성 실패: {str(e)}")


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    현재 사용자 반환.

    현재 모든 요청을 게스트로 허용합니다. 토큰이 있으면 디코딩을 시도하고,
    실패하거나 없으면 기본 게스트 사용자를 반환합니다 (401 반환 안 함).
    """
    if not token:
        return DEFAULT_GUEST_USER

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub") or "guest"
    except Exception:
        return DEFAULT_GUEST_USER

    # DynamoDB 조회는 실패해도 게스트로 fallback
    try:
        from app.utils.dynamo import get_user
        user = get_user(user_id)
        if user:
            return user
    except Exception:
        pass

    return {**DEFAULT_GUEST_USER, "user_id": user_id}
