# app/services/openai_service.py

import os
import openai
import numpy as np   # 임베딩 계산용
import logging

openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # 🔧 환경변수로 모델 설정 가능

logger = logging.getLogger(__name__)

def get_embedding(text: str) -> list:
    """
    텍스트의 임베딩 벡터를 생성합니다.
    """
    try:
        res = openai.embeddings.create(
            input=[text],
            model="text-embedding-3-small"
        )
        return res.data[0].embedding
    except openai.RateLimitError as e:
        logger.warning(f"⚠️ OpenAI Rate Limit 초과: {e}")
        return []
    except openai.APIError as e:
        logger.warning(f"⚠️ OpenAI API 오류: {e}")
        return []
    except openai.AuthenticationError as e:
        logger.warning(f"⚠️ OpenAI 인증 오류: {e}")
        return []
    except Exception as e:
        logger.warning(f"⚠️ 임베딩 생성 예상치 못한 오류: {e}")
        return []

def cosine_similarity(vec1, vec2):
    """
    두 벡터 간의 코사인 유사도를 계산합니다.
    """
    try:
        if not vec1 or not vec2:
            return 0.0
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    except (ValueError, ZeroDivisionError, np.linalg.LinAlgError) as e:
        logger.warning(f"⚠️ 코사인 유사도 계산 오류: {e}")
        return 0.0
    except Exception as e:
        logger.warning(f"⚠️ 코사인 유사도 예상치 못한 오류: {e}")
        return 0.0

def cluster_similar_texts(texts, threshold=0.75):
    """
    유사한 텍스트들을 클러스터링하여 중복 내용을 그룹화합니다.
    """
    if len(texts) <= 1:
        return [texts]
    
    try:
        logger.info(f"🔄 {len(texts)}개 텍스트 클러스터링 시작...")
        embeddings = []
        
        # 임베딩 생성 (실패한 것들은 제외)
        valid_texts = []
        for i, text in enumerate(texts):
            emb = get_embedding(text[:1000])  # 🔧 토큰 제한: 1500자 → 1000자
            if emb:
                embeddings.append(emb)
                valid_texts.append(text)
        
        if len(embeddings) <= 1:
            return [valid_texts]
            
        clusters = []
        for idx, emb in enumerate(embeddings):
            added = False
            for cluster in clusters:
                if cosine_similarity(emb, cluster['embedding']) > threshold:
                    cluster['indices'].append(idx)
                    added = True
                    break
            if not added:
                clusters.append({'embedding': emb, 'indices': [idx]})
        
        # 클러스터별로 텍스트 그룹화
        grouped = [[valid_texts[i] for i in c['indices']] for c in clusters]
        logger.info(f"✅ {len(texts)}개 → {len(grouped)}개 클러스터로 그룹화")
        return grouped
        
    except MemoryError as e:
        logger.warning(f"⚠️ 메모리 부족으로 클러스터링 실패: {e}")
        return [texts]
    except (ValueError, TypeError) as e:
        logger.warning(f"⚠️ 데이터 형식 오류로 클러스터링 실패: {e}")
        return [texts]
    except Exception as e:
        logger.warning(f"⚠️ 클러스터링 예상치 못한 오류, 원본 반환: {e}")
        return [texts]

def summarize_group(texts: list, category: str) -> str:
    """
    클러스터된 유사 기사들을 하나의 요약으로 통합합니다.
    """
    if len(texts) == 1:
        return texts[0]
    
    # 🔧 토큰 최적화: 각 텍스트 길이 제한
    limited_texts = [text[:800] for text in texts]  # 각 기사 800자로 제한
        
    prompt = (
        f"다음은 '{category}' 분야에서 비슷한 내용의 뉴스 기사들입니다. "
        f"중복되는 내용을 제거하고, 핵심 정보만을 담아 "
        f"하나의 자연스러운 요약(500자~700자)으로 작성해주세요.\n\n"
        + "\n\n".join(limited_texts)
    )
    
    try:
        response = openai.chat.completions.create(
            model=MODEL_NAME,  # 🔧 환경변수 모델 사용
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=700  # 🔧 토큰 제한: 900 → 700
        )
        return response.choices[0].message.content.strip()
    except openai.RateLimitError as e:
        logger.warning(f"⚠️ OpenAI Rate Limit 초과 (그룹 요약): {e}")
        return texts[0]
    except openai.APIError as e:
        logger.warning(f"⚠️ OpenAI API 오류 (그룹 요약): {e}")
        return texts[0]
    except openai.AuthenticationError as e:
        logger.warning(f"⚠️ OpenAI 인증 오류 (그룹 요약): {e}")
        return texts[0]
    except Exception as e:
        logger.warning(f"⚠️ 그룹 요약 예상치 못한 오류: {e}")
        return texts[0]  # 실패시 첫 번째 텍스트 반환

def summarize_articles(texts: list[str], category: str) -> str:
    """
    GPT-4o-mini를 사용하여 여러 개의 뉴스 요약을 바탕으로
    하나의 흐름을 가진 팟캐스트 대본을 생성합니다.
    """
    
    # 🔄 [2차 클러스터링] GPT 요약문 기반 의미적 중복 제거
    try:
        if len(texts) > 5:  # 5개 이상일 때만 클러스터링 적용
            logger.info(f"🔄 2차 클러스터링 시작: {len(texts)}개 요약문")
            clustered_groups = cluster_similar_texts(texts, threshold=0.75)
            
            # 각 클러스터를 하나의 요약으로 통합
            consolidated_texts = []
            for group_idx, group in enumerate(clustered_groups):
                if len(group) > 1:
                    # 여러 유사 요약문을 하나로 통합
                    try:
                        summary = summarize_group(group, category)
                        consolidated_texts.append(summary)
                        logger.info(f"📊 2차 그룹 #{group_idx+1}: {len(group)}개 요약 → 통합 ({len(summary)}자)")
                    except Exception as e:
                        logger.warning(f"⚠️ 2차 그룹 #{group_idx+1} 요약 실패, 첫 번째 사용: {e}")
                        consolidated_texts.append(group[0][:1000])  # 🔧 길이 제한
                else:
                    # 단일 요약은 그대로 사용 (길이 제한)
                    consolidated_texts.append(group[0][:1000])  # 🔧 단일 기사도 1000자로 제한
                    logger.info(f"📄 2차 그룹 #{group_idx+1}: 단일 요약 ({len(group[0][:1000])}자)")
            
            final_texts = consolidated_texts
            logger.info(f"✅ 2차 클러스터링 완료: {len(texts)}개 → {len(final_texts)}개 그룹")
        else:
            # 🔧 클러스터링 안할 때도 길이 제한
            final_texts = [text[:1000] for text in texts]
            logger.info(f"📝 2차 클러스터링 생략, 원본 요약 수: {len(final_texts)}")
            
    except Exception as e:
        logger.warning(f"⚠️ 2차 클러스터링 과정 실패, 원본 사용: {e}")
        final_texts = [text[:1000] for text in texts]  # 🔧 실패시에도 길이 제한

    # 🎙️ 최종 팟캐스트 대본 생성
    prompt = (
        f"당신은 지적이면서도 친근한 말투로 정보를 전달하는 프로 팟캐스트 진행자입니다. "
        f"청취자는 '{category}' 분야에 관심은 있지만 전문가는 아닌 일반 대중입니다.\n\n"
        "다음은 해당 카테고리의 오늘의 주요 뉴스 본문 요약 리스트입니다:\n\n"
        "{{뉴스_요약_리스트}}\n\n"
        "각 기사의 내용을 바탕으로 청취자에게 전달력 있게 구성된 팟캐스트 대본을 작성해주세요. "
        "스크립트는 하나의 이야기 흐름처럼 자연스럽게 이어지도록 하며, 전체 분량은 **반드시 최소 1800자 이상**이어야 합니다.\n\n"
        "**길이 요구사항:**\n"
        "- 최소 1800자 이상 (필수)\n"
        "- 최대 2200자 이하 (권장)\n"
        "- 만약 1800자에 미달하면 각 주제에 대한 설명을 더 자세히 풀어써 주세요\n\n"
        "**작성 조건:**\n"
        "- 말하듯 자연스럽고 따뜻한 진행 톤 유지\n"
        "- 뉴스 기사들을 단순 나열하지 말고, 주제 간 연결 문장을 활용해 하나의 흐름으로 연결\n"
        f"- 도입부에는 '오늘 {category} 분야에서는 이런 이슈들이 있었습니다.'와 같은 멘트 포함\n"
        "- 각 뉴스 항목마다 충분한 설명과 분석을 포함하여 상세히 다뤄주세요\n"
        "- 뉴스의 배경, 의미, 파급효과 등을 포함하여 심도 있게 설명해주세요\n"
        "- 마무리에서는 종합적인 요약과 청취자에게 생각할 거리를 남기는 말로 끝내기\n"
        "- 문단 구분과 리듬을 고려하여 실제 음성으로 읽기 좋게 구성\n"
        "- 충분한 길이를 확보하기 위해 설명을 풍부하게 해주세요\n\n"
        "**중요:** 최종 대본이 1800자 미만이면 안 됩니다. 각 주제를 충분히 자세히 설명하여 목표 길이를 달성해주세요.\n\n"
        "Take a deep breath and let's work this out in a step by step way to be sure we have the right answer."
    )

    # 뉴스 요약 리스트를 문자열로 정리
    article_list = "\n".join([f"- {text}" for text in final_texts])
    context = prompt.replace("{{뉴스_요약_리스트}}", article_list)

    try:
        response = openai.chat.completions.create(
            model=MODEL_NAME,  # 🔧 환경변수 모델 사용
            messages=[{"role": "user", "content": context}],
            temperature=0.7,
            max_tokens=2000  # 🔧 토큰 제한: 2200 → 2000
        )
        
        result = response.choices[0].message.content.strip()
        logger.info(f"📏 생성된 대본 길이: {len(result)}자 (모델: {MODEL_NAME})")  # 🔧 사용 모델 로그 추가
        return result
        
    except openai.RateLimitError as e:
        logger.warning(f"⚠️ OpenAI Rate Limit 초과 (대본 생성): {e}")
        return f"오늘 {category} 분야의 주요 소식들을 전해드렸습니다."
    except openai.APIError as e:
        logger.warning(f"⚠️ OpenAI API 오류 (대본 생성): {e}")
        return f"오늘 {category} 분야의 주요 소식들을 전해드렸습니다."
    except openai.AuthenticationError as e:
        logger.warning(f"⚠️ OpenAI 인증 오류 (대본 생성): {e}")
        return f"오늘 {category} 분야의 주요 소식들을 전해드렸습니다."
    except Exception as e:
        logger.warning(f"⚠️ 대본 생성 예상치 못한 오류: {e}")
        return f"오늘 {category} 분야의 주요 소식들을 전해드렸습니다."