#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# test/test_content_extraction.py

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# .env 파일에서 환경변수 로드
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

from app.services.deepsearch_service import (
    is_korean_text, 
    clean_text_noise,
    extract_content_with_bs4,
    extract_content_flexibly
)

def test_korean_text_detection():
    """한글 텍스트 감지 테스트"""
    print(" [테스트 1] 한글 텍스트 감지")
    
    test_cases = [
        ("안녕하세요. 한국어 뉴스 기사입니다.", True, "순수 한글"),
        ("Hello, this is English text.", False, "영어 텍스트"),
        ("안녕하세요 hello world 반갑습니다.", True, "한영 혼합 (한글 우세)"),
        ("Hello 안녕 world test 반가워", False, "한영 혼합 (영어 우세)"),
        ("123456789", False, "숫자만"),
        ("", False, "빈 문자열"),
        ("안녕하세요! 오늘의 뉴스를 전해드립니다. 정치, 경제, 사회 분야의 소식이 있습니다.", True, "긴 한글 텍스트")
    ]
    
    for text, expected, description in test_cases:
        result = is_korean_text(text, threshold=0.7)
        status = "" if result == expected else ""
        print(f"  {status} {description}: {result} (예상: {expected})")
        if text:
            korean_ratio = len([c for c in text if '가' <= c <= '힣']) / len([c for c in text if c.isalpha() or '가' <= c <= '힣']) if any(c.isalpha() or '가' <= c <= '힣' for c in text) else 0
            print(f"    → 한글 비율: {korean_ratio:.2f}")
    print()

def test_text_noise_cleaning():
    """텍스트 노이즈 제거 테스트"""
    print(" [테스트 2] 텍스트 노이즈 제거")
    
    noisy_text = """
이것은 실제 뉴스 기사 본문입니다.
중요한 정보가 포함되어 있습니다.

김기자 reporter@news.com
홍길동기자
전화: 02-1234-5678

[카카오톡] @newschannel
[메일] contact@example.com

Copyright 2024 News Corp. All rights reserved.
무단전재 및 재배포 금지
재배포 금지

이 기사의 댓글 정책을 결정합니다
앱 다운로드 링크
네이버 AI 뉴스 알고리즘

실제 뉴스 내용이 여기에 있습니다.
분석과 의견이 포함되어 있습니다.
"""
    
    cleaned = clean_text_noise(noisy_text)
    
    print("원본 텍스트 줄 수:", len(noisy_text.strip().split('\n')))
    print("정제 후 줄 수:", len(cleaned.strip().split('\n')))
    print("\n정제된 텍스트:")
    print(cleaned)
    
    # 노이즈 제거 확인
    noise_keywords = ["기자", "@", "Copyright", "무단전재", "카카오톡", "댓글 정책", "앱 다운"]
    remaining_noise = [kw for kw in noise_keywords if kw in cleaned]
    
    if remaining_noise:
        print(f" 남은 노이즈: {remaining_noise}")
    else:
        print(" 노이즈 제거 완료")
    print()

def test_content_extraction_simulation():
    """본문 추출 시뮬레이션 테스트"""
    print(" [테스트 3] 본문 추출 시뮬레이션")
    
    # 실제 URL 테스트는 외부 의존성이 있으므로 시뮬레이션
    test_urls = [
        "https://newsis.com/article/123",
        "https://yna.co.kr/article/456", 
        "https://kbs.co.kr/news/789",
        "https://unknown-site.com/article/999"
    ]
    
    print(" 테스트 URL 목록:")
    for i, url in enumerate(test_urls, 1):
        domain = url.split('/')[2].replace('www.', '')
        print(f"  {i}. {domain} ({url})")
    
    print(f"\n selector 지원 도메인 확인:")
    from app.services.deepsearch_service import ARTICLE_SELECTORS
    
    supported_count = 0
    for url in test_urls:
        domain = url.split('/')[2].replace('www.', '')
        has_selector = domain in ARTICLE_SELECTORS
        status = "" if has_selector else ""
        print(f"  {status} {domain}: {'지원됨' if has_selector else '일반 추출'}")
        if has_selector:
            supported_count += 1
    
    print(f"\n selector 지원률: {supported_count}/{len(test_urls)} ({supported_count/len(test_urls)*100:.0f}%)")
    print()

def test_article_selectors():
    """기사 selector 정의 테스트"""
    print(" [테스트 4] 기사 selector 정의")
    
    from app.services.deepsearch_service import ARTICLE_SELECTORS
    
    print(f" 총 지원 도메인: {len(ARTICLE_SELECTORS)}개")
    print("\n지원 도메인 목록:")
    
    major_domains = ["newsis.com", "yna.co.kr", "kbs.co.kr", "donga.com", "joongang.co.kr"]
    
    for i, (domain, selector) in enumerate(ARTICLE_SELECTORS.items(), 1):
        is_major = "⭐" if domain in major_domains else "  "
        print(f"{is_major} {i:2d}. {domain:<20} → {selector}")
    
    print(f"\n 주요 언론사 지원: {sum(1 for d in major_domains if d in ARTICLE_SELECTORS)}/{len(major_domains)}개")
    print()

def test_unwanted_keywords():
    """불필요 키워드 패턴 테스트"""
    print(" [테스트 5] 불필요 키워드 패턴")
    
    from app.services.deepsearch_service import UNWANTED_KEYWORDS
    
    test_sentences = [
        "이 기사의 댓글 정책을 결정합니다",
        "앱 다운로드를 권합니다", 
        "네이버 AI 뉴스 알고리즘이 추천한 기사",
        "실제 뉴스 내용입니다",
        "프리미엄콘텐츠 구독 안내",
        "정치 분야의 중요한 소식입니다"
    ]
    
    print(f" 총 불필요 키워드: {len(UNWANTED_KEYWORDS)}개")
    print("\n테스트 문장 필터링:")
    
    for sentence in test_sentences:
        is_unwanted = any(kw in sentence for kw in UNWANTED_KEYWORDS)
        status = "🚫" if is_unwanted else ""
        action = "제거됨" if is_unwanted else "유지됨"
        print(f"  {status} {sentence} → {action}")
    
    print()

def main():
    """본문 추출 테스트 실행"""
    print(" 본문 추출 서비스 테스트 시작\n")
    
    test_korean_text_detection()
    test_text_noise_cleaning()
    test_content_extraction_simulation()
    test_article_selectors()
    test_unwanted_keywords()
    
    print(" 테스트 요약:")
    print(" 한글 텍스트 감지: 다양한 케이스 검증")
    print(" 노이즈 제거: 기자정보, 저작권, 광고 텍스트 필터링")
    print(" Selector 지원: 주요 언론사 도메인 대응")
    print(" 키워드 필터: 불필요한 안내문구 제거")
    
    print("\n 본문 추출 테스트 완료!")

if __name__ == "__main__":
    main() 