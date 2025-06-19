# app/main.py

import os
from fastapi import FastAPI
from mangum import Mangum
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv  #  dotenv 로드 추가

#  .env 환경변수 불러오기
load_dotenv()

#  라우터 임포트
from app.routes import (
    auth,
    category,
    frequency,
    news,
    user
)

#  카테고리 맵 임포트
from app.constants.category_map import CATEGORY_KO_LIST

#  FastAPI 인스턴스 생성
app = FastAPI(
    title="Briefly API",
    redirect_slashes=False  # trailing slash 자동 리다이렉트 방지
)

#  라우터 등록
app.include_router(auth.router)
app.include_router(category.router)
app.include_router(frequency.router)
app.include_router(news.router)
app.include_router(user.router)

#  CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 운영 환경에서는 구체적인 도메인으로 제한 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#  AWS Lambda용 Mangum 핸들러
handler = Mangum(app)

#  루트 헬스 체크
@app.get("/")
def read_root():
    return {"message": "Welcome to Briefly API"}

#  온보딩 페이지 엔드포인트 (프론트엔드 요청 대응)
@app.get("/onboarding")
def get_onboarding_info():
    """
    온보딩 페이지 정보 제공 (인증 불필요)
    
    - 프론트엔드에서 /onboarding 경로 요청 시 응답
    """
    return {
        "message": "온보딩 페이지입니다",
        "available_categories": CATEGORY_KO_LIST
    }
