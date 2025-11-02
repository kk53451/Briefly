# app/constants/category_map.py

# BigKinds API 8개 카테고리 기준 매핑
# - 'api_name': API 요청 시 사용되는 영문 카테고리명 (내부 식별용)
# - 'bigkinds_code': BigKinds API 카테고리 9자리 코드
# - 'bigkinds_name': BigKinds API 카테고리 한글명 (요청 시 사용)
CATEGORY_MAP = {
    "정치": {
        "api_name": "politics",
        "bigkinds_code": "001000000",
        "bigkinds_name": "정치"
    },
    "경제": {
        "api_name": "economy",
        "bigkinds_code": "002000000",
        "bigkinds_name": "경제"
    },
    "사회": {
        "api_name": "society",
        "bigkinds_code": "003000000",
        "bigkinds_name": "사회"
    },
    "문화": {
        "api_name": "culture",
        "bigkinds_code": "004000000",
        "bigkinds_name": "문화"
    },
    "국제": {
        "api_name": "international",
        "bigkinds_code": "005000000",
        "bigkinds_name": "국제"
    },
    "지역": {
        "api_name": "local",
        "bigkinds_code": "006000000",
        "bigkinds_name": "지역"
    },
    "스포츠": {
        "api_name": "sports",
        "bigkinds_code": "007000000",
        "bigkinds_name": "스포츠"
    },
    "IT/과학": {
        "api_name": "tech",
        "bigkinds_code": "008000000",
        "bigkinds_name": "IT_과학"
    },
}

# 한글 카테고리명 목록 (예: ["정치", "경제", ...])
CATEGORY_KO_LIST = list(CATEGORY_MAP.keys())

# 영문 카테고리명 목록 (예: ["politics", "economy", ...])
CATEGORY_EN_LIST = [v["api_name"] for v in CATEGORY_MAP.values()]

# 영문 카테고리명 → 한글 카테고리명 역매핑 딕셔너리
# 예: {"politics": "정치", "economy": "경제", ...}
REVERSE_CATEGORY_MAP = {v["api_name"]: k for k, v in CATEGORY_MAP.items()}
 