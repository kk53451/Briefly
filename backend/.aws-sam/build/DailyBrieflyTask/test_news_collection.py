#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# .env 파일에서 환경변수 로드
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

# 기본값이 필요한 환경변수들 설정 (테스트용)
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
from app.utils.date import get_today_kst
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_single_category_collection():
    """
    단일 카테고리 뉴스 수집 테스트
    """
    print("🚀 실제 뉴스 수집 테스트 시작\n")
    
    # 테스트할 카테고리 (정치)
    category = "politics"
    section = "domestic"
    today = get_today_kst()
    
    print(f"📅 수집 날짜: {today}")
    print(f"📰 카테고리: {category} ({section})")
    print(f"🎯 목표: 30개 기사\n")
    
    # 시간 범위 설정 (오늘 자정~현재)
    start_time = f"{today}T00:00:00"
    end_time = f"{today}T23:59:59"
    
    print(f"⏰ 시간 범위: {start_time} ~ {end_time}\n")
    
    try:
        print("📡 DeepSearch API 호출 중...")
        articles = fetch_valid_articles_by_category(
            category=category,
            start_time=start_time,
            end_time=end_time,
            size=50,                # 오버페치 후 필터링
            sort="popular",
            section=section,
            min_content_length=300,
            limit=30               # 최종 30개
        )
        
        print(f"✅ 수집 완료! 총 {len(articles)}개 기사")
        
        # 결과 분석
        if articles:
            print("\n📊 수집된 기사 분석:")
            for i, article in enumerate(articles[:5], 1):  # 처음 5개만 미리보기
                title = article.get('title', 'N/A')
                content_len = len(article.get('content', ''))
                publisher = article.get('publisher', 'N/A')
                print(f"  {i}. [{publisher}] {title[:50]}... ({content_len}자)")
            
            if len(articles) > 5:
                print(f"  ... 그 외 {len(articles)-5}개 기사")
                
            print(f"\n📏 평균 본문 길이: {sum(len(a.get('content', '')) for a in articles) // len(articles)}자")
            print(f"📰 출처: {set(a.get('publisher') for a in articles if a.get('publisher'))}")
        
        return articles
        
    except Exception as e:
        print(f"❌ 수집 실패: {e}")
        return []

def preview_article_content(articles, index=0):
    """
    특정 기사의 내용을 미리보기
    """
    if not articles or index >= len(articles):
        print("❌ 유효하지 않은 기사 인덱스")
        return
        
    article = articles[index]
    print(f"\n📰 기사 #{index+1} 상세:")
    print(f"📌 제목: {article.get('title', 'N/A')}")
    print(f"📰 출처: {article.get('publisher', 'N/A')}")
    print(f"👤 기자: {article.get('author', 'N/A')}")
    print(f"📅 발행: {article.get('published_at', 'N/A')}")
    print(f"🔗 URL: {article.get('content_url', 'N/A')}")
    print(f"📏 본문 길이: {len(article.get('content', ''))}자")
    print(f"📝 본문 미리보기:\n{article.get('content', '')[:500]}...")

if __name__ == "__main__":
    # 실제 뉴스 수집 테스트
    articles = test_single_category_collection()
    
    if articles:
        print(f"\n🎉 수집 성공! {len(articles)}개 기사가 수집되었습니다.")
        
        # 첫 번째 기사 상세 보기
        preview_article_content(articles, 0)
        
        # 다음 단계 안내
        print(f"\n🚀 다음 단계:")
        print(f"1. DynamoDB에 저장 (collect_news.py)")
        print(f"2. GPT로 대본 생성 (generate_frequency.py)")
        print(f"3. TTS 음성 변환")
        
    else:
        print("\n❌ 수집된 기사가 없습니다. API 키나 네트워크를 확인해주세요.")
    
    print(f"\n🏁 테스트 완료!") 