#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# test/test_collection_simulation.py

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# .env 파일에서 환경변수 로드
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

def simulate_news_collection():
    """실제 뉴스 수집 로직 시뮬레이션"""
    
    # 가상의 기사 40개 생성 (실제보다 많은 상황)
    mock_articles = []
    for i in range(40):
        mock_articles.append({
            "news_id": f"news_{i+1}",
            "content_url": f"https://example.com/news/{i+1}",
            "content": f"이것은 기사 {i+1}번의 본문입니다. " * 100,  # 약 1600자
            "title": f"기사 제목 {i+1}"
        })
    
    print(f" 총 수집된 기사 수: {len(mock_articles)}개")
    
    # 실제 generate_frequency.py 로직 시뮬레이션
    full_contents = []
    processed_count = 0
    target_count = 30  # 정확히 30개로 제한
    
    for i, article in enumerate(mock_articles):
        if len(full_contents) >= target_count:
            print(f" 목표 달성: {target_count}개 수집 완료")
            break
            
        processed_count += 1
        news_id = article.get("news_id")
        url = article.get("content_url")
        content = article.get("content", "").strip()

        if not news_id or not url:
            print(f" #{processed_count} URL 또는 ID 없음 → 스킵")
            continue

        if not content or len(content) < 300:
            print(f" #{processed_count} 본문 길이 부족 → 스킵")
            continue

        # 토큰 최적화: 1500자로 단축
        trimmed = content[:1500]
        full_contents.append(trimmed)
        print(f" #{len(full_contents)} 본문 사용 완료 ({len(trimmed)}자)")

    print(f"\n 최종 수집 결과:")
    print(f"  - 처리된 기사: {processed_count}개")
    print(f"  - 수집된 기사: {len(full_contents)}개")
    print(f"  - 목표 기사: {target_count}개")
    
    # 테스트 결과 검증
    if len(full_contents) == target_count:
        print(f" 수집 개수 테스트 통과: 정확히 {target_count}개")
    elif len(full_contents) < target_count:
        print(f" 수집 개수 부족: {len(full_contents)}개 (유효 기사 부족)")
    else:
        print(f" 수집 개수 초과: {len(full_contents)}개 (로직 오류)")
    
    # 토큰 길이 테스트
    total_length = sum(len(content) for content in full_contents)
    avg_length = total_length / len(full_contents) if full_contents else 0
    
    print(f"\n 토큰 길이 분석:")
    print(f"  - 총 길이: {total_length}자")
    print(f"  - 평균 길이: {avg_length:.0f}자")
    print(f"  - 최대 길이: {max(len(c) for c in full_contents) if full_contents else 0}자")
    
    if avg_length <= 1500:
        print(f" 토큰 길이 제한 준수: 평균 {avg_length:.0f}자")
    else:
        print(f" 토큰 길이 초과: 평균 {avg_length:.0f}자")

def test_edge_cases():
    """엣지 케이스 테스트"""
    print("\n 엣지 케이스 테스트")
    
    # 케이스 1: 기사가 30개보다 적은 경우
    print("\n 케이스 1: 기사 부족 (10개)")
    mock_articles_few = [
        {"news_id": f"news_{i}", "content_url": f"url_{i}", "content": "내용 " * 100}
        for i in range(10)
    ]
    
    full_contents = []
    target_count = 30
    
    for article in mock_articles_few:
        if len(full_contents) >= target_count:
            break
        content = article.get("content", "")
        if content and len(content) >= 300:
            full_contents.append(content[:1500])
    
    print(f"수집 결과: {len(full_contents)}개 (목표: {target_count}개)")
    
    # 케이스 2: 빈 content가 많은 경우
    print("\n 케이스 2: 빈 content 많음")
    mock_articles_empty = []
    for i in range(40):
        content = "내용 " * 100 if i % 3 == 0 else ""  # 1/3만 유효 content
        mock_articles_empty.append({
            "news_id": f"news_{i}",
            "content_url": f"url_{i}",
            "content": content
        })
    
    full_contents = []
    for article in mock_articles_empty:
        if len(full_contents) >= target_count:
            break
        content = article.get("content", "")
        if content and len(content) >= 300:
            full_contents.append(content[:1500])
    
    print(f"수집 결과: {len(full_contents)}개 (목표: {target_count}개)")

if __name__ == "__main__":
    print(" 뉴스 수집 시뮬레이션 테스트 시작\n")
    simulate_news_collection()
    test_edge_cases()
    print("\n 시뮬레이션 테스트 완료") 