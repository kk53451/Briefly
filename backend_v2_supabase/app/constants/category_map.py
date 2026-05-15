"""
카테고리 매핑 (v2)

6개 카테고리. 지역·스포츠 제외.
Naver 뉴스 섹션 ID 추가.
"""

CATEGORY_MAP = {
    "정치": {
        "api_name": "politics",
        "naver_sid": "100",
    },
    "경제": {
        "api_name": "economy",
        "naver_sid": "101",
    },
    "사회": {
        "api_name": "society",
        "naver_sid": "102",
    },
    "문화": {
        "api_name": "culture",
        "naver_sid": "103",
    },
    "국제": {
        "api_name": "international",
        "naver_sid": "104",
    },
    "IT/과학": {
        "api_name": "tech",
        "naver_sid": "105",
    },
}

# 역방향 매핑 (api_name → 한글)
API_TO_KO = {v["api_name"]: k for k, v in CATEGORY_MAP.items()}

# Naver sid → api_name
SID_TO_API = {v["naver_sid"]: v["api_name"] for k, v in CATEGORY_MAP.items()}
