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

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256") 
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", 60))

# OAuth2PasswordBearer는 token을 Header에서 추출하는 역할만 함
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")  # 실제 토큰 발급 엔드포인트는 Kakao 인증 기반이므로 사용 X, 형식용

def create_access_token(user_id: str) -> str:
    """
    주어진 user_id를 기반으로 JWT 액세스 토큰을 생성하여 반환
    """
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    }
    try:
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"JWT 토큰 생성 실패: {str(e)}")

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    HTTP Authorization 헤더에서 JWT 토큰을 읽어 현재 로그인된 사용자의 전체 정보를 반환
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="토큰에서 사용자 ID를 찾을 수 없습니다.")
        
        # DynamoDB에서 사용자 전체 정보 조회
        from app.utils.dynamo import get_user
        user = get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
            
        return user
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 인증 정보입니다 (JWT 디코딩 실패).",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"JWT 토큰 처리 중 오류: {str(e)}",
        )
