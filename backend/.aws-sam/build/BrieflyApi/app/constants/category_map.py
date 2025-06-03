# app/constants/category_map.py

# ✅ 사용자에게 보여지는 한글 카테고리명과 API 연동을 위한 영문 카테고리명 + 섹션 정보를 매핑
# - 'api_name': API 요청 시 사용되는 영문 카테고리명
# - 'section': 딥서치 API의 섹션 구분 ('domestic' 또는 'international')
CATEGORY_MAP = {
    "정치": {"api_name": "politics", "section": "domestic"},
    "경제": {"api_name": "economy", "section": "domestic"},
    "사회": {"api_name": "society", "section": "domestic"},
    "생활/문화": {"api_name": "culture", "section": "domestic"},
    "IT/과학": {"api_name": "tech", "section": "domestic"},
    "연예": {"api_name": "entertainment", "section": "domestic"},
    # "세계": {"api_name": "world", "section": "international"},  ← 제거됨
    # "스포츠": {"api_name": "sports", "section": "international"},  ← 제거됨
}

# ✅ 한글 카테고리명 목록 (예: ["정치", "경제", ...])
CATEGORY_KO_LIST = list(CATEGORY_MAP.keys())

# ✅ 영문 카테고리명 목록 (예: ["politics", "economy", ...])
CATEGORY_EN_LIST = [v["api_name"] for v in CATEGORY_MAP.values()]

# ✅ 영문 카테고리명 → 한글 카테고리명 역매핑 딕셔너리
# 예: {"politics": "정치", "economy": "경제", ...}
REVERSE_CATEGORY_MAP = {v["api_name"]: k for k, v in CATEGORY_MAP.items()}
 