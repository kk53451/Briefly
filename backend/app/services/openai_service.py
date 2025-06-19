# app/services/openai_service.py

import os
import openai
import numpy as np   # 임베딩 계산용
import logging

openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # 환경변수로 모델 설정 가능

logger = logging.getLogger(__name__)

# Few-shot 예시들
FEW_SHOT_EXAMPLES = {
    "경제": {
        "input": [
            "[기사 1] 삼성전자가 3분기 영업이익 10조원을 기록했다고 28일 발표했다. 이는 전년 동기 대비 30% 증가한 수치다.",
            "[기사 2] 삼성전자 3분기 실적 발표 후 주가가 3% 상승했다. 시장 예상치 9.5조원을 크게 상회한 결과다.",
            "[기사 3] 반도체 업황 회복으로 삼성전자 실적이 개선됐다. 메모리 반도체 가격 상승이 주요 요인으로 분석된다."
        ],
        "output": "삼성전자가 28일 3분기 영업이익 10조원을 기록했다고 발표했다. 이는 전년 동기 대비 30% 증가한 수치로 시장 예상치 9.5조원을 크게 상회했다. 실적 발표 직후 삼성전자 주가는 전일 대비 3% 상승하며 투자자들의 긍정적 반응을 보였다. 반도체 업황 회복과 메모리 반도체 가격 상승이 이번 실적 개선의 주요 동력으로 분석되고 있어, 4분기에도 이런 상승세가 이어질지 주목된다."
    },
    "정치": {
        "input": [
            "[기사 1] 정부가 부동산 정책 개편안을 29일 발표할 예정이다. 주택 공급 확대가 핵심 내용으로 알려졌다.",
            "[기사 2] 야당은 정부 부동산 정책이 서민 주거 안정에 도움이 되지 않는다고 비판했다.",
            "[기사 3] 부동산업계는 새 정책이 시장 안정화에 기여할 것으로 기대한다고 밝혔다."
        ],
        "output": "정부가 29일 부동산 정책 개편안을 발표할 예정이다. 주택 공급 확대를 핵심으로 하는 이번 정책에 대해 여야와 업계의 반응이 엇갈리고 있다. 정부는 주택 공급 확대를 통한 시장 안정화를 목표로 한다고 밝혔으나, 야당은 서민 주거 안정에 실질적 도움이 되지 않을 것이라고 비판했다. 반면 부동산업계는 새 정책이 시장 안정화에 긍정적 영향을 미칠 것으로 기대한다고 입장을 표했다."
    },
    "사회": {
        "input": [
            "[기사 1] 서울시가 청년 주거 지원을 위해 월세 보조금을 30만원으로 확대한다고 발표했다.",
            "[기사 2] 청년들은 월세 보조금 확대에 환영 의사를 표했지만 여전히 부족하다는 반응이다.",
            "[기사 3] 시민단체는 근본적인 주거비 해결책이 필요하다고 지적했다."
        ],
        "output": "서울시가 청년 주거 부담 완화를 위해 월세 보조금을 기존보다 확대해 30만원으로 지원한다고 발표했다. 이번 정책에 대해 청년들은 환영 의사를 표했지만, 여전히 높은 주거비에 비해 부족하다는 반응을 보이고 있다. 시민단체들은 일시적 보조금보다는 주거비 상승의 근본적 원인을 해결하는 정책이 필요하다고 지적하며, 보다 체계적인 청년 주거 정책 마련을 촉구했다."
    },
    "IT": {
        "input": [
            "[기사 1] 네이버가 새로운 AI 검색 서비스 '하이퍼클로바X'를 공개했다. 생성형 AI 기술을 활용한 것이 특징이다.",
            "[기사 2] 하이퍼클로바X는 기존 검색과 달리 대화형으로 답변을 제공한다고 네이버가 설명했다.",
            "[기사 3] IT업계는 네이버의 AI 검색이 구글과의 경쟁에서 차별화 요소가 될 것으로 전망했다."
        ],
        "output": "네이버가 생성형 AI 기술을 활용한 새로운 검색 서비스 '하이퍼클로바X'를 공개했다. 기존 키워드 검색과 달리 사용자와 대화하듯 자연스럽게 답변을 제공하는 것이 핵심 특징이다. IT업계에서는 이번 서비스가 구글 등 글로벌 검색 엔진과의 경쟁에서 네이버만의 차별화 요소로 작용할 것으로 분석하고 있어, 국내 검색 시장에 새로운 변화를 가져올지 주목된다."
    },
    "문화": {
        "input": [
            "[기사 1] BTS 멤버 지민의 솔로 앨범이 빌보드 200 차트 2위에 올랐다.",
            "[기사 2] 지민은 한국 솔로 가수 최초로 빌보드 200 톱3에 진입하는 기록을 세웠다.",
            "[기사 3] 팬들은 SNS를 통해 지민의 성과를 축하하며 응원 메시지를 전했다."
        ],
        "output": "BTS 멤버 지민의 솔로 앨범이 빌보드 200 차트 2위에 오르며 한국 솔로 가수 최초로 톱3 진입이라는 역사적 기록을 달성했다. 이는 K-팝 솔로 아티스트로서는 전례 없는 성과로, 지민의 글로벌 영향력을 다시 한번 입증했다. 전 세계 팬들은 SNS를 통해 축하와 응원 메시지를 쏟아내며 이번 성과를 함께 기뻐하고 있어, K-팝의 글로벌 위상을 더욱 높이는 계기가 되고 있다."
    },
    "스포츠": {
        "input": [
            "[기사 1] 손흥민이 토트넘과의 경기에서 2골을 넣으며 팀 승리를 이끌었다.",
            "[기사 2] 이번 경기로 손흥민은 시즌 15골을 기록하며 개인 최고 기록에 근접했다.",
            "[기사 3] 토트넘 팬들은 손흥민의 활약에 열광하며 'Son is the King'이라고 외쳤다."
        ],
        "output": "손흥민이 토트넘 경기에서 멀티골을 터뜨리며 팀 승리의 주역으로 나섰다. 이번 2골로 시즌 15골을 기록한 손흥민은 개인 최고 기록 경신을 눈앞에 두고 있어 더욱 의미가 크다. 경기장을 가득 메운 토트넘 팬들은 'Son is the King'을 연호하며 손흥민의 환상적인 활약에 열광했고, 그의 꾸준한 득점 행진이 팀의 상위권 도약에 핵심 동력이 되고 있다."
    }
}



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
        logger.warning(f" OpenAI Rate Limit 초과: {e}")
        return []
    except openai.APIError as e:
        logger.warning(f" OpenAI API 오류: {e}")
        return []
    except openai.AuthenticationError as e:
        logger.warning(f" OpenAI 인증 오류: {e}")
        return []
    except Exception as e:
        logger.warning(f" 임베딩 생성 예상치 못한 오류: {e}")
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
        logger.warning(f" 코사인 유사도 계산 오류: {e}")
        return 0.0
    except Exception as e:
        logger.warning(f" 코사인 유사도 예상치 못한 오류: {e}")
        return 0.0

def cluster_similar_texts(texts, threshold=0.75):
    """
    유사한 텍스트들을 클러스터링하여 중복 내용을 그룹화합니다.
    """
    if len(texts) <= 1:
        return [texts]
    
    try:
        logger.info(f"{len(texts)}개 텍스트 클러스터링 시작...")
        embeddings = []
        
        # 임베딩 생성 (실패한 것들은 제외)
        valid_texts = []
        for i, text in enumerate(texts):
            emb = get_embedding(text[:1000])  # 토큰 제한: 1500자에서 1000자로 단축
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
        logger.info(f"{len(texts)}개 텍스트를 {len(grouped)}개 클러스터로 그룹화 완료")
        return grouped
        
    except MemoryError as e:
        logger.warning(f" 메모리 부족으로 클러스터링 실패: {e}")
        return [texts]
    except (ValueError, TypeError) as e:
        logger.warning(f" 데이터 형식 오류로 클러스터링 실패: {e}")
        return [texts]
    except Exception as e:
        logger.warning(f" 클러스터링 예상치 못한 오류, 원본 반환: {e}")
        return [texts]

def summarize_group(texts: list, category: str) -> str:
    """
    클러스터된 유사 기사들을 하나의 요약으로 통합합니다.
    Few-shot learning과 품질 검증을 포함합니다.
    """
    if len(texts) == 1:
        return texts[0]
    
    # 토큰 최적화를 위해 각 텍스트 길이 제한
    limited_texts = [text[:800] for text in texts]  # 각 기사 800자로 제한
    
    # 카테고리별 특화 요약 스타일
    category_context = {
        "정치": "정책의 배경과 영향, 다양한 관점을 균형있게",
        "경제": "경제 지표의 의미와 일반인에게 미치는 영향을 중심으로",
        "사회": "사회적 이슈의 원인과 파급효과, 시민들의 반응을",
        "문화": "문화적 의미와 트렌드, 대중의 관심사를",
        "IT": "기술의 혁신성과 실생활 적용 가능성을",
        "스포츠": "경기 결과와 선수들의 스토리, 팬들의 반응을"
    }.get(category, "핵심 사실과 그 의미를")
    
    # Few-shot 예시 추가
    few_shot_example = ""
    if category in FEW_SHOT_EXAMPLES:
        example = FEW_SHOT_EXAMPLES[category]
        few_shot_example = (
            f"**좋은 통합 요약 예시 ({category} 분야):**\n"
            + "\n".join(example["input"]) + "\n\n"
            f"→ **통합 요약**: {example['output']}\n\n"
            "위 예시처럼 중복을 제거하고 핵심 정보를 논리적으로 연결하여 작성해주세요.\n\n"
        )
        
    prompt = (
        f"당신은 뉴스 요약 전문가입니다. '{category}' 분야의 유사한 뉴스 기사들을 "
        f"하나의 완성도 높은 요약으로 통합해주세요.\n\n"
        
        f"{few_shot_example}"
        
        f"**통합 요약 작성 가이드:**\n"
        f"1. **핵심 사실 추출**: 가장 중요한 사실들을 우선순위대로 정리\n"
        f"2. **중복 제거**: 반복되는 내용은 한 번만 언급하되 중요도에 따라 강조\n"
        f"3. **맥락 제공**: {category_context} 포함\n"
        f"4. **논리적 구조**: 시간순/중요도순으로 자연스럽게 연결\n"
        f"5. **구체적 정보**: 날짜, 수치, 인명 등 구체적 정보 보존\n"
        f"6. **균형잡힌 시각**: 여러 관점이 있다면 공정하게 제시\n\n"
        
        f"**품질 기준:**\n"
        f"- 독립적으로 읽어도 이해되는 완성된 요약\n"
        f"- 중요한 정보 누락 없이 간결하게\n"
        f"- 자연스러운 한국어 문체\n"
        f"- 500-700자 분량 (음성 변환 최적화)\n\n"
        
        f"**통합할 기사들:**\n"
        + "\n\n".join([f"[기사 {i+1}]\n{text}" for i, text in enumerate(limited_texts)])
        + "\n\n위 기사들을 바탕으로 통합 요약을 작성해주세요:"
    )
    
    max_attempts = 3
    
    for attempt in range(max_attempts):
        try:
            # Temperature를 점진적으로 조정 (첫 시도는 낮게, 실패시 높게)
            temp = 0.3 + (attempt * 0.2)  # 0.3 -> 0.5 -> 0.7
            
            response = openai.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=temp,
                max_tokens=700
            )
            
            summary = response.choices[0].message.content.strip()
            logger.info(f"시도 {attempt + 1}: 온도={temp:.1f}, 요약 생성 완료 ({len(summary)}자)")
            return summary
                
        except openai.RateLimitError as e:
            logger.warning(f" OpenAI Rate Limit 초과 (그룹 요약, 시도 {attempt + 1}): {e}")
            if attempt == max_attempts - 1:
                return texts[0]
            continue
        except openai.APIError as e:
            logger.warning(f" OpenAI API 오류 (그룹 요약, 시도 {attempt + 1}): {e}")
            if attempt == max_attempts - 1:
                return texts[0]
            continue
        except openai.AuthenticationError as e:
            logger.warning(f" OpenAI 인증 오류 (그룹 요약): {e}")
            return texts[0]
        except Exception as e:
            logger.warning(f" 그룹 요약 예상치 못한 오류 (시도 {attempt + 1}): {e}")
            if attempt == max_attempts - 1:
                return texts[0]
            continue
    
    # 모든 시도 실패시 첫 번째 원본 텍스트 반환
    logger.warning("모든 요약 시도 실패, 원본 텍스트 반환")
    return texts[0]

def get_category_specific_style(category: str) -> str:
    """
    카테고리별 특화된 진행 스타일과 톤 반환
    """
    category_styles = {
        "정치": {
            "tone": "신중하고 균형잡힌",
            "style": "복잡한 정치 상황을 쉽게 풀어서 설명하고, 다양한 관점을 제시",
            "examples": "'이 정책이 우리 생활에 어떤 영향을 줄지', '양쪽 입장을 정리해보면'"
        },
        "경제": {
            "tone": "전문적이지만 친근한",
            "style": "경제 용어를 일상 언어로 번역하고, 실생활 연관성 강조",
            "examples": "'쉽게 말하면', '우리 지갑에는 어떤 의미일까요', '예를 들어'"
        },
        "사회": {
            "tone": "따뜻하고 공감적인",
            "style": "사람들의 이야기에 집중하고, 감정적 공감대 형성",
            "examples": "'정말 안타까운 일이네요', '많은 분들이 공감하실 텐데', '우리 모두의 관심이 필요한'"
        },
        "문화": {
            "tone": "밝고 흥미진진한",
            "style": "재미있고 생동감 있게, 문화적 의미와 트렌드 설명",
            "examples": "'정말 흥미롭네요', '요즘 핫한', '문화적으로 보면'"
        },
        "IT": {
            "tone": "호기심 가득한",
            "style": "기술을 쉽게 설명하고, 미래 전망과 일상 연관성 강조",
            "examples": "'기술적으로는', '미래에는 어떻게 될까요', '우리 생활이 어떻게 바뀔지'"
        },
        "스포츠": {
            "tone": "열정적이고 역동적인",
            "style": "현장감 있게 전달하고, 선수와 팀의 스토리 강조",
            "examples": "'정말 대단한', '감동적인 순간이었는데', '팬들은 열광했을 것 같아요'"
        }
    }
    
    if category in category_styles:
        style_info = category_styles[category]
        return (
            f"**{category} 분야 특화 스타일:**\n"
            f"- 톤: {style_info['tone']} 느낌으로\n"
            f"- 접근법: {style_info['style']}\n"
            f"- 자주 사용할 표현: {style_info['examples']}\n\n"
        )
    else:
        return "**일반적인 뉴스 브리핑 스타일:**\n- 톤: 친근하고 신뢰감 있는\n- 접근법: 균형잡힌 시각으로 정보 전달\n\n"

def summarize_articles(texts: list[str], category: str) -> str:
    """
    GPT-4o-mini를 사용하여 여러 개의 뉴스 요약을 바탕으로
    하나의 흐름을 가진 팟캐스트 대본을 생성합니다.
    """
    
    # 2차 클러스터링: GPT 요약문 기반 의미적 중복 제거
    try:
        if len(texts) > 5:  # 5개 이상일 때만 클러스터링 적용
            logger.info(f"2차 클러스터링 시작: {len(texts)}개 요약문")
            clustered_groups = cluster_similar_texts(texts, threshold=0.75)
            
            # 각 클러스터를 하나의 요약으로 통합
            consolidated_texts = []
            for group_idx, group in enumerate(clustered_groups):
                if len(group) > 1:
                    # 여러 유사 요약문을 하나로 통합
                    try:
                        summary = summarize_group(group, category)
                        consolidated_texts.append(summary)
                        logger.info(f"2차 그룹 #{group_idx+1}: {len(group)}개 요약을 통합 ({len(summary)}자)")
                    except Exception as e:
                        logger.warning(f" 2차 그룹 #{group_idx+1} 요약 실패, 첫 번째 사용: {e}")
                        consolidated_texts.append(group[0][:1000])  # 길이 제한
                else:
                    # 단일 요약은 그대로 사용 (길이 제한)
                    consolidated_texts.append(group[0][:1000])  # 단일 기사도 1000자로 제한
                    logger.info(f"2차 그룹 #{group_idx+1}: 단일 요약 ({len(group[0][:1000])}자)")
            
            final_texts = consolidated_texts
            logger.info(f"2차 클러스터링 완료: {len(texts)}개를 {len(final_texts)}개 그룹으로 축소")
        else:
            # 클러스터링 안할 때도 길이 제한
            final_texts = [text[:1000] for text in texts]
            logger.info(f"2차 클러스터링 생략, 원본 요약 수: {len(final_texts)}")
            
    except Exception as e:
        logger.warning(f" 2차 클러스터링 과정 실패, 원본 사용: {e}")
        final_texts = [text[:1000] for text in texts]  # 실패시에도 길이 제한

    # 최종 팟캐스트 대본 생성
    category_style = get_category_specific_style(category)
    
    prompt = (
        f"당신은 친근하고 신뢰감 있는 뉴스 브리핑 진행자입니다. "
        f"마치 친구에게 오늘 있었던 중요한 소식을 전해주듯이 자연스럽고 따뜻한 톤으로 말해주세요.\n\n"
        
        f"**청취자:** '{category}' 분야에 관심 있는 일반인\n"
        f"**목표:** 복잡한 뉴스를 쉽고 재미있게 전달\n"
        f"**스타일:** 대화하듯 자연스럽고, 때로는 감탄사나 추임새 포함\n\n"
        
        f"{category_style}"
        
        "**오늘의 뉴스 요약:**\n"
        "{{뉴스_요약_리스트}}\n\n"
        
        "**대본 작성 가이드:**\n"
        "1. **자연스러운 시작**: '안녕하세요, 오늘도 함께해주셔서 감사합니다' 같은 인사\n"
        f"2. **카테고리 소개**: '오늘 {category} 분야에는 정말 흥미로운 소식들이 많네요'\n"
        "3. **뉴스 전달**: 각 뉴스마다 '그런데 말이에요', '정말 놀라운 건', '이게 왜 중요하냐면' 같은 자연스러운 연결어 사용\n"
        "4. **감정 표현**: '와, 이건 정말...', '음, 생각해보니...', '아, 그리고 또...' 같은 자연스러운 반응\n"
        "5. **쉬운 설명**: 어려운 용어는 '쉽게 말하면', '즉', '다시 말해' 같은 표현으로 풀어서 설명\n"
        "6. **개인적 의견**: '개인적으로는', '저는 이 부분이 인상적이었는데요' 같은 진행자의 관점 포함\n"
        "7. **자연스러운 마무리**: '오늘 브리핑은 여기까지입니다. 내일도 좋은 소식으로 찾아뵐게요'\n\n"
        
        "**TTS 최적화 요소:**\n"
        "- 문장을 너무 길게 하지 말고, 자연스러운 호흡 지점에서 끊어주세요\n"
        "- 강조하고 싶은 부분은 '정말로', '바로', '특히' 같은 부사 활용\n"
        "- 숫자나 전문용어 앞뒤로 잠깐의 여유 두기\n"
        "- 감탄사 활용: '아', '오', '음', '그런데', '하지만' 등\n\n"
        
        "**길이 요구사항:**\n"
        "- 최소 1800자 이상 (음성으로 약 3-4분 분량)\n"
        "- 최대 2200자 이하\n"
        "- 각 뉴스당 충분한 설명과 배경 정보 포함\n\n"
        
        "**중요:** 실제로 사람이 말하는 것처럼 자연스럽고 친근하게 작성해주세요. "
        "딱딱한 뉴스 앵커가 아닌, 친구가 흥미로운 이야기를 들려주는 느낌으로!"
    )

    # 뉴스 요약 리스트를 문자열로 정리
    article_list = "\n".join([f"- {text}" for text in final_texts])
    context = prompt.replace("{{뉴스_요약_리스트}}", article_list)

    try:
        response = openai.chat.completions.create(
            model=MODEL_NAME,  # 환경변수 모델 사용
            messages=[{"role": "user", "content": context}],
            temperature=0.7,
            max_tokens=2000  # 토큰 제한: 2200에서 2000으로 단축
        )
        
        result = response.choices[0].message.content.strip()
        logger.info(f"생성된 대본 길이: {len(result)}자 (모델: {MODEL_NAME})")  # 사용 모델 로그 추가
        return result
        
    except openai.RateLimitError as e:
        logger.warning(f" OpenAI Rate Limit 초과 (대본 생성): {e}")
        return f"오늘 {category} 분야의 주요 소식들을 전해드렸습니다."
    except openai.APIError as e:
        logger.warning(f" OpenAI API 오류 (대본 생성): {e}")
        return f"오늘 {category} 분야의 주요 소식들을 전해드렸습니다."
    except openai.AuthenticationError as e:
        logger.warning(f" OpenAI 인증 오류 (대본 생성): {e}")
        return f"오늘 {category} 분야의 주요 소식들을 전해드렸습니다."
    except Exception as e:
        logger.warning(f" 대본 생성 예상치 못한 오류: {e}")
        return f"오늘 {category} 분야의 주요 소식들을 전해드렸습니다."