#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# test/test_utils.py

import os
import sys
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# .env 파일에서 환경변수 로드
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# 기본값이 필요한 환경변수들 설정 (테스트용)
if not os.getenv('DDB_NEWS_TABLE'):
    os.environ['DDB_NEWS_TABLE'] = 'NewsCards'
if not os.getenv('DDB_FREQ_TABLE'):
    os.environ['DDB_FREQ_TABLE'] = 'Frequencies'
if not os.getenv('DDB_USER_TABLE'):
    os.environ['DDB_USER_TABLE'] = 'Users'
if not os.getenv('DDB_USERS_TABLE'):
    os.environ['DDB_USERS_TABLE'] = 'Users'
if not os.getenv('DDB_BOOKMARK_TABLE'):
    os.environ['DDB_BOOKMARK_TABLE'] = 'Bookmarks'
if not os.getenv('DDB_BOOKMARKS_TABLE'):
    os.environ['DDB_BOOKMARKS_TABLE'] = 'Bookmarks'
if not os.getenv('S3_BUCKET'):
    os.environ['S3_BUCKET'] = 'briefly-news-audio'

from app.utils.date import get_today_kst
from app.constants.category_map import CATEGORY_MAP, CATEGORY_KO_LIST, REVERSE_CATEGORY_MAP

def test_date_utils():
    """날짜 유틸리티 테스트"""
    print(" [테스트 1] 날짜 유틸리티")
    
    # KST 날짜 테스트
    today = get_today_kst()
    
    print(f" 오늘 날짜 (KST): {today}")
    
    # 날짜 형식 검증
    try:
        datetime.strptime(today, "%Y-%m-%d")
        print(" 날짜 형식 유효: YYYY-MM-DD")
    except ValueError:
        print(" 날짜 형식 오류")
    
    # 날짜 길이 검증
    if len(today) == 10 and today.count('-') == 2:
        print(" 날짜 길이 형식 유효: 10자, 2개 하이픈")
    else:
        print(" 날짜 길이 형식 오류")
    
    print()

def test_category_constants():
    """카테고리 상수 테스트"""
    print(" [테스트 2] 카테고리 상수")
    
    print(f" 카테고리 개수: {len(CATEGORY_MAP)}개")
    print(f" 한글 카테고리: {CATEGORY_KO_LIST}")
    print(f" 영문 카테고리: {[v['api_name'] for v in CATEGORY_MAP.values()]}")
    
    # 역매핑 테스트
    print("\n역매핑 테스트:")
    for ko, en_info in CATEGORY_MAP.items():
        en = en_info["api_name"]
        reverse_ko = REVERSE_CATEGORY_MAP.get(en)
        status = "" if reverse_ko == ko else ""
        print(f"  {status} {ko} ↔ {en} (역: {reverse_ko})")
    
    # 섹션 정보 테스트 - 실제 사용 섹션만 확인
    print("\n섹션 정보:")
    domestic_count = sum(1 for v in CATEGORY_MAP.values() if v["section"] == "domestic")
    intl_count = sum(1 for v in CATEGORY_MAP.values() if v["section"] == "international")
    
    print(f"  - 국내: {domestic_count}개")
    print(f"  - 해외: {intl_count}개")
    
    # 실제로는 국내 섹션만 사용
    if intl_count == 0:
        print(" 해외 섹션 미사용 (국내 섹션만 운영)")
        if domestic_count == len(CATEGORY_MAP):
            print(" 모든 카테고리가 국내 섹션으로 구성됨")
        else:
            print(" 일부 카테고리의 섹션 설정 오류")
    else:
        print(f" 해외 섹션이 {intl_count}개 설정되어 있음 (실제 미사용)")
        print(" 해외 섹션 카테고리:")
        for ko, en_info in CATEGORY_MAP.items():
            if en_info["section"] == "international":
                print(f"    - {ko} ({en_info['api_name']})")
    
    # 카테고리별 섹션 확인
    print(f"\n 카테고리별 섹션:")
    for ko, en_info in CATEGORY_MAP.items():
        section = en_info["section"]
        status = "🇰🇷" if section == "domestic" else "🌍"
        print(f"  {status} {ko}: {section}")
    
    print()

def test_dynamo_table_names():
    """DynamoDB 테이블명 테스트"""
    print(" [테스트 3] DynamoDB 테이블명")
    
    expected_tables = [
        "NewsCards",
        "Frequencies", 
        "Users",
        "Bookmarks"
    ]
    
    # 환경변수에서 테이블명 확인
    for table in expected_tables:
        env_key = f"DDB_{table.upper().replace('S', '')}_TABLE"
        if table == "NewsCards":
            env_key = "DDB_NEWS_TABLE"
        elif table == "Frequencies":
            env_key = "DDB_FREQ_TABLE"
        elif table == "Users":
            env_key = "DDB_USER_TABLE"
        
        expected_name = table
        actual_name = os.getenv(env_key, "NOT_SET")
        
        status = "" if actual_name == expected_name else ""
        print(f"  {status} {env_key}: {actual_name} (예상: {expected_name})")
    
    print()

def test_frequency_id_format():
    """주파수 ID 형식 테스트"""
    print(" [테스트 4] 주파수 ID 형식")
    
    from app.utils.date import get_today_kst
    
    date = get_today_kst()
    
    print(" 주파수 ID 형식 테스트:")
    for ko_category in CATEGORY_KO_LIST:
        en_category = CATEGORY_MAP[ko_category]["api_name"]
        freq_id = f"{en_category}#{date}"
        
        # ID 형식 검증
        parts = freq_id.split('#')
        has_valid_format = (
            len(parts) == 2 and
            parts[0] in [v["api_name"] for v in CATEGORY_MAP.values()] and
            len(parts[1]) == 10 and  # YYYY-MM-DD
            parts[1].count('-') == 2
        )
        
        status = "" if has_valid_format else ""
        print(f"  {status} {ko_category}: {freq_id}")
    
    print()

def test_s3_bucket_config():
    """S3 버킷 설정 테스트"""
    print(" [테스트 5] S3 버킷 설정")
    
    bucket_name = os.getenv("S3_BUCKET", "NOT_SET")
    expected_bucket = "briefly-news-audio"
    
    status = "" if bucket_name == expected_bucket else ""
    print(f"  {status} S3_BUCKET: {bucket_name} (예상: {expected_bucket})")
    
    # 버킷명 규칙 검증
    valid_bucket_format = (
        bucket_name.islower() and 
        '-' in bucket_name and
        not bucket_name.startswith('-') and
        not bucket_name.endswith('-')
    )
    
    format_status = "" if valid_bucket_format else ""
    print(f"  {format_status} 버킷명 형식: {'유효' if valid_bucket_format else '무효'}")
    
    print()

def test_api_key_presence():
    """API 키 존재 여부 테스트"""
    print(" [테스트 6] API 키 존재 여부")
    
    api_keys = [
        ("OPENAI_API_KEY", "sk-proj-"),
        ("ELEVENLABS_API_KEY", "sk_"),
        ("DEEPSEARCH_API_KEY", None),
        ("KAKAO_CLIENT_ID", None)
    ]
    
    for key_name, expected_prefix in api_keys:
        key_value = os.getenv(key_name, "")
        
        # 존재 여부
        exists = bool(key_value and key_value != "NOT_SET")
        
        # 형식 검증
        format_valid = True
        if expected_prefix and exists:
            format_valid = key_value.startswith(expected_prefix)
        
        status = "" if exists and format_valid else ""
        masked_value = f"{key_value[:10]}***" if len(key_value) > 10 else "NOT_SET"
        
        print(f"  {status} {key_name}: {masked_value}")
        
        if not exists:
            print(f"     키가 설정되지 않음")
        elif not format_valid:
            print(f"     형식 오류 (예상 접두사: {expected_prefix})")
    
    print()

def main():
    """유틸리티 테스트 실행"""
    print(" 유틸리티 함수 테스트 시작\n")
    
    test_date_utils()
    test_category_constants()
    test_dynamo_table_names()
    test_frequency_id_format()
    test_s3_bucket_config()
    test_api_key_presence()
    
    print(" 테스트 요약:")
    print(" 날짜 유틸: KST 시간대, 형식 검증")
    print(" 카테고리 상수: 매핑, 역매핑, 섹션 분류")
    print(" DynamoDB 설정: 테이블명 확인")
    print(" 주파수 ID: 형식 및 구조 검증")
    print(" S3 설정: 버킷명 및 규칙 확인")
    print(" API 키: 존재 여부 및 형식 검증")
    
    print("\n 유틸리티 테스트 완료!")

if __name__ == "__main__":
    main() 