#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# insert_test_news.py - 테스트용 뉴스 데이터 삽입

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# .env 파일에서 환경변수 로드
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

# 기본값이 필요한 환경변수들 설정
if not os.getenv('DDB_NEWS_TABLE'):
    os.environ['DDB_NEWS_TABLE'] = 'NewsCards'
if not os.getenv('DDB_FREQ_TABLE'):
    os.environ['DDB_FREQ_TABLE'] = 'Frequencies'
if not os.getenv('DDB_USERS_TABLE'):
    os.environ['DDB_USERS_TABLE'] = 'Users'
if not os.getenv('DDB_BOOKMARKS_TABLE'):
    os.environ['DDB_BOOKMARKS_TABLE'] = 'Bookmarks'
if not os.getenv('S3_BUCKET'):
    os.environ['S3_BUCKET'] = 'briefly-news-audio'

from app.services.deepsearch_service import fetch_valid_articles_by_category
from app.utils.dynamo import save_news_card
from app.utils.date import get_today_kst
from app.constants.category_map import CATEGORY_MAP
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def insert_test_news_data():
    """
    테스트용 뉴스 데이터를 DynamoDB에 삽입
    """
    print("테스트용 뉴스 데이터 삽입 시작\n")
    
    today = get_today_kst()
    print(f"수집 날짜: {today}")
    
    # 시간 범위 설정 (전체 하루)
    start_time = f"{today}T00:00:00"
    end_time = f"{today}T23:59:59"
    
    total_saved = 0
    
    # 각 카테고리별로 뉴스 수집 및 저장
    for category_ko, config in CATEGORY_MAP.items():
        category_en = config["api_name"]
        section = config["section"]
        
        print(f"\n[{category_ko}] 뉴스 수집 시작")
        
        try:
            # 뉴스 수집 (30개 목표)
            articles = fetch_valid_articles_by_category(
                category=category_en,
                start_time=start_time,
                end_time=end_time,
                size=40,                # 오버페치
                sort="popular",
                section=section,
                min_content_length=300,
                limit=30               # 최종 30개
            )
            
            print(f"수집된 기사 수: {len(articles)}개")
            
            saved_count = 0
            
            # 각 기사를 DynamoDB에 저장
            for rank, article in enumerate(articles, start=1):
                news_id = article.get("id")
                content = article.get("content", "")
                
                if not news_id:
                    print(f"#{rank} ID 없음 → 스킵")
                    continue
                    
                if not content or len(content) < 300:
                    print(f"#{rank} 본문 부족 → 스킵")
                    continue
                
                # 뉴스 아이템 구성
                news_item = {
                    "id": news_id,
                    "sections": article.get("sections", []),
                    "rank": rank,
                    "title": article.get("title"),
                    "title_ko": None,
                    "summary": article.get("summary"),
                    "summary_ko": None,
                    "image_url": article.get("image_url"),
                    "thumbnail_url": article.get("thumbnail_url") or article.get("thumbnail"),
                    "content_url": article.get("content_url"),
                    "publisher": article.get("publisher"),
                    "author": article.get("author"),
                    "published_at": article.get("published_at"),
                    "companies": article.get("companies", []),
                    "esg": article.get("esg", []),
                    "content": content[:1500]  # 토큰 최적화
                }
                
                try:
                    # DynamoDB에 저장
                    save_news_card(category_en, news_item, today)
                    saved_count += 1
                    print(f"#{rank} 저장 완료: {news_item['title'][:50]}...")
                    
                except Exception as e:
                    print(f"#{rank} 저장 실패: {e}")
            
            print(f"[{category_ko}] 최종 저장: {saved_count}개")
            total_saved += saved_count
            
        except Exception as e:
            print(f"[{category_ko}] 수집 실패: {e}")
            continue
    
    print(f"\n전체 뉴스 데이터 삽입 완료!")
    print(f"총 저장된 기사: {total_saved}개")
    print(f"평균 카테고리별: {total_saved / len(CATEGORY_MAP):.1f}개")
    
    return total_saved

if __name__ == "__main__":
    insert_test_news_data() 