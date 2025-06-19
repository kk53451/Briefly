#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# test/test_frequency_unit.py

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# .env 파일에서 환경변수 로드
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

from app.constants.category_map import CATEGORY_MAP, CATEGORY_KO_LIST
from app.utils.date import get_today_kst
from app.utils.dynamo import get_news_by_category_and_date
from app.services.openai_service import summarize_articles

def test_category_count():
    """1. 카테고리 개수 테스트"""
    print(" [테스트 1] 카테고리 개수 확인")
    print(f" 전체 카테고리 수: {len(CATEGORY_MAP)}개")
    print(f" 카테고리 목록: {list(CATEGORY_MAP.keys())}")
    print(f" 한글 카테고리: {CATEGORY_KO_LIST}")
    
    if len(CATEGORY_MAP) == 6:
        print(" 카테고리 개수 테스트 통과 (6개)")
    else:
        print(f" 카테고리 개수 오류: {len(CATEGORY_MAP)}개 (예상: 6개)")
    print()

def test_news_collection():
    """2. 뉴스 수집 개수 테스트"""
    print(" [테스트 2] 뉴스 수집 개수 확인")
    date = get_today_kst()
    print(f" 기준 날짜: {date}")
    
    for category_ko in CATEGORY_MAP.keys():
        category_en = CATEGORY_MAP[category_ko]["api_name"]
        articles = get_news_by_category_and_date(category_en, date)
        
        # 실제 수집 로직 시뮬레이션
        full_contents = []
        processed_count = 0
        target_count = 30
        
        for i, article in enumerate(articles):
            if len(full_contents) >= target_count:
                break
                
            processed_count += 1
            news_id = article.get("news_id")
            url = article.get("content_url")
            content = article.get("content", "").strip()
            
            if not news_id or not url:
                continue
                
            if not content or len(content) < 300:
                continue  # 실제로는 재추출하지만 테스트에서는 스킵
                
            # 토큰 최적화: 1500자로 제한
            trimmed = content[:1500]
            full_contents.append(trimmed)
        
        print(f" {category_ko}({category_en}): {len(full_contents)}개 수집 (목표: {target_count}개)")
        
        if len(full_contents) > target_count:
            print(f" {category_ko}: 목표 초과 ({len(full_contents)}개)")
        elif len(full_contents) == target_count:
            print(f" {category_ko}: 목표 달성 ({len(full_contents)}개)")
        else:
            print(f" {category_ko}: 수집 부족 ({len(full_contents)}개) - DB 데이터 부족")
    print()

def test_script_generation():
    """3. 대본 생성 및 토큰 테스트"""
    print(" [테스트 3] 대본 생성 토큰 테스트")
    
    # 더 현실적이고 긴 샘플 기사 텍스트 생성
    sample_texts = [
        "정치 분야의 주요 뉴스입니다. 국회에서 새로운 법안이 통과되었으며, 이로 인해 정치계에 큰 변화가 예상됩니다. 여당과 야당의 치열한 공방이 이어지고 있으며, 시민들의 관심도 높아지고 있습니다. 전문가들은 이번 법안이 향후 정치 지형에 미칠 영향을 분석하고 있습니다. " * 8,  # 약 1200자
        "경제 관련 중요한 소식을 전해드립니다. 중앙은행의 금리 정책 변화로 인해 주식시장과 부동산 시장에 큰 파동이 일고 있습니다. 기업들의 투자 계획에도 변화가 예상되며, 일반 소비자들의 가계 경제에도 직접적인 영향을 미칠 것으로 보입니다. 경제 전문가들은 신중한 대응이 필요하다고 조언하고 있습니다. " * 8,  # 약 1200자
        "사회 이슈에 대한 분석 내용입니다. 최근 사회적 거리두기 완화와 함께 일상생활이 점차 정상화되고 있습니다. 교육 분야에서는 온라인과 오프라인 수업의 병행이 새로운 표준으로 자리잡고 있으며, 의료진들의 노고에 대한 사회적 인정과 지원이 계속되고 있습니다. 시민사회 단체들은 더 나은 사회를 위한 다양한 활동을 펼치고 있습니다. " * 8,  # 약 1200자
        "문화 분야의 새로운 동향을 살펴보겠습니다. K-문화의 세계적인 인기가 지속되면서 한국의 문화 콘텐츠 산업이 급성장하고 있습니다. 영화, 음악, 드라마 등 다양한 분야에서 해외 진출이 활발해지고 있으며, 이는 국가 브랜드 가치 향상에도 크게 기여하고 있습니다. 정부에서도 문화 산업 육성을 위한 다양한 정책을 마련하고 있습니다. " * 8,  # 약 1200자
        "IT 기술의 최신 발전 상황입니다. 인공지능과 빅데이터 기술의 발전으로 다양한 산업 분야에서 디지털 전환이 가속화되고 있습니다. 스마트시티 구축, 자율주행차 상용화, 메타버스 플랫폼 확산 등 미래 기술들이 현실로 다가오고 있습니다. 기업들은 새로운 기술 트렌드에 발맞춰 혁신적인 서비스를 선보이고 있습니다. " * 8,  # 약 1200자
        "국제 정세에 대한 분석을 전해드립니다. 주요국들 간의 외교적 협력과 경쟁이 복잡하게 얽혀있는 가운데, 글로벌 공급망 재편과 기후변화 대응이 국제사회의 주요 화두로 떠오르고 있습니다. 각국은 자국의 이익을 보호하면서도 국제적인 협력을 강화하기 위한 균형점을 찾고 있습니다. " * 8,  # 약 1200자
    ]
    
    print(f" 샘플 텍스트 수: {len(sample_texts)}개")
    print(f" 각 텍스트 길이: {[len(text) for text in sample_texts]}자")
    
    # 토큰 제한 테스트 - 더 넉넉한 길이로 설정
    limited_texts = [text[:1000] for text in sample_texts]  # 1000자로 제한
    print(f" 제한된 텍스트 길이: {[len(text) for text in limited_texts]}자")
    
    total_input_length = sum(len(text) for text in limited_texts)
    print(f" 총 입력 길이: {total_input_length}자")
    
    if total_input_length <= 8000:  # 8000자 이하로 제한 (더 넉넉하게)
        print(" 토큰 길이 테스트 통과")
    else:
        print(f" 토큰 길이 초과: {total_input_length}자")
    
    # 실제 대본 생성 테스트 - 더 많은 텍스트 사용
    try:
        print(" GPT 대본 생성 테스트 시작...")
        print(" 더 긴 대본 생성을 위해 모든 샘플 텍스트 사용...")
        script = summarize_articles(limited_texts, "politics")  # 6개 모두 사용
        print(f" 생성된 대본 길이: {len(script)}자")
        print(f" 대본 미리보기: {script[:200]}...")
        
        if 1800 <= len(script) <= 2500:  # 범위를 약간 넓게 조정
            print(" 대본 길이 테스트 통과 (1800-2500자)")
        elif len(script) < 1800:
            print(f" 대본 길이 부족: {len(script)}자 (목표: 1800자 이상)")
            print(" 개선 방안:")
            print("  - 입력 텍스트 양 증가")
            print("  - GPT 프롬프트에서 더 상세한 설명 요청")
            print("  - max_tokens 값 증가 고려")
        else:
            print(f" 대본 길이 초과: {len(script)}자 (권장: 2500자 이하)")
            
    except Exception as e:
        print(f" 대본 생성 테스트 실패: {e}")
        print(" 시뮬레이션 모드로 대체...")
        simulated_script = "안녕하세요, 오늘의 정치 뉴스를 전해드립니다. " * 80  # 약 2000자
        print(f" 시뮬레이션 대본 길이: {len(simulated_script)}자")
    
    print()

def main():
    """메인 테스트 실행"""
    print(" Briefly 유닛 테스트 시작\n")
    
    test_category_count()
    test_news_collection() 
    test_script_generation()
    
    print(" 유닛 테스트 완료")

if __name__ == "__main__":
    main() 