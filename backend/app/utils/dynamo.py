import os
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.constants.category_map import CATEGORY_MAP, REVERSE_CATEGORY_MAP

# ================================
# Decimal 변환 유틸 함수
# ================================
def deep_convert(obj: Any) -> Any:
    """
    float → Decimal 변환 (DynamoDB 저장 시 오류 방지용)
    """
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, list):
        return [deep_convert(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: deep_convert(v) for k, v in obj.items()}
    return obj

# ================================
# DynamoDB 연결 및 테이블 객체
# ================================
dynamodb = boto3.resource("dynamodb")

news_table = dynamodb.Table(os.getenv("DDB_NEWS_TABLE", "NewsCards"))
freq_table = dynamodb.Table(os.getenv("DDB_FREQ_TABLE", "Frequencies"))
users_table = dynamodb.Table(os.getenv("DDB_USERS_TABLE", "Users"))
bookmark_table = dynamodb.Table(os.getenv("DDB_BOOKMARKS_TABLE", "Bookmarks"))

# ================================
# 이미지 URL 변환 유틸 함수
# ================================
BIGKINDS_IMAGE_BASE_URL = "https://www.bigkinds.or.kr/resources/images"

def parse_image_urls(images: Any) -> list:
    """
    DynamoDB 이미지 데이터를 BigKinds 전체 URL로 변환

    입력 형식:
      - 단일: [{"S": "/path/to/image.jpg"}]
      - 여러: [{"S": "/path1.jpg\n/path2.jpg\n/path3.jpg"}]
    출력 형식: ["https://www.bigkinds.or.kr/resources/images/path1.jpg", ...]
    """
    if not images:
        return []

    urls = []
    try:
        if isinstance(images, list):
            for img in images:
                # DynamoDB JSON 형식: {"S": "/path"} 또는 {"S": "/path1\n/path2"}
                if isinstance(img, dict) and "S" in img:
                    paths_str = img["S"]
                    # \n으로 구분된 여러 경로 처리
                    paths = paths_str.split("\n") if "\n" in paths_str else [paths_str]

                    for path in paths:
                        path = path.strip()
                        if not path:
                            continue
                        # 경로가 /로 시작하면 그대로, 아니면 / 추가
                        if path.startswith("/"):
                            full_url = f"{BIGKINDS_IMAGE_BASE_URL}{path}"
                        else:
                            full_url = f"{BIGKINDS_IMAGE_BASE_URL}/{path}"
                        urls.append(full_url)

                # 이미 문자열인 경우 (Python SDK 자동 변환)
                elif isinstance(img, str):
                    if img.startswith("http"):
                        urls.append(img)
                    else:
                        # \n으로 구분된 여러 경로 처리
                        paths = img.split("\n") if "\n" in img else [img]
                        for path in paths:
                            path = path.strip()
                            if not path:
                                continue
                            if path.startswith("/"):
                                full_url = f"{BIGKINDS_IMAGE_BASE_URL}{path}"
                            else:
                                full_url = f"{BIGKINDS_IMAGE_BASE_URL}/{path}"
                            urls.append(full_url)
    except Exception as e:
        print(f"⚠️ 이미지 URL 파싱 오류: {e}")
        return []

    return urls


# ============================================
# 1. NewsCards 관련 함수
# ============================================

def save_news_card(category: str, article: dict, date_str: str):
    """
    뉴스 기사 1건을 NewsCards 테이블에 저장 (BigKinds 기준)
    - 이미지는 첫 번째만 URL로 변환하여 저장
    """
    # 이미지 URL 변환: 첫 번째만 사용
    raw_images = article.get("images", [])
    parsed_urls = parse_image_urls(raw_images)
    image_url = parsed_urls[0] if parsed_urls else ""

    item = {
        "news_id": article["id"],
        "category_date": f"{category}#{date_str}",  # GSI용 복합 키
        "category": category,
        "rank": article.get("rank"),
        "title": article.get("title"),
        "images": image_url,  # 첫 번째 이미지 URL만 문자열로 저장
        "provider_link_page": article.get("provider_link_page"),
        "provider": article.get("provider"),
        "byline": article.get("byline"),
        "published_at": article.get("published_at"),
        "hilight": article.get("hilight"),
        "collected_at": datetime.utcnow().isoformat(),
        "content": article.get("content", "")
    }

    try:
        news_table.put_item(Item=deep_convert(item))
    except ClientError as e:
        raise Exception(f"[NewsCards 저장 실패] {e.response['Error']['Message']}")

def get_news_by_category_and_date(category: str, date: str):
    """
    category와 date 기준으로 뉴스 목록 조회 (최신 70개 이상)
    """
    key = f"{category}#{date}"
    try:
        response = news_table.query(
            IndexName="category_date-index",
            KeyConditionExpression="category_date = :key",
            ExpressionAttributeValues={":key": key}
        )
        return response.get("Items", [])
    except ClientError as e:
        raise Exception(f"[NewsCards 조회 실패] {e.response['Error']['Message']}")

def get_news_card_by_id(news_id: str):
    """
    news_id 기준으로 뉴스 상세 조회
    """
    try:
        response = news_table.get_item(Key={"news_id": news_id})
        return response.get("Item")
    except ClientError as e:
        raise Exception(f"[뉴스 상세 조회 실패] {e.response['Error']['Message']}")

def get_news_card_by_content_url(content_url: str):
    """
    provider_link_page 기준으로 뉴스 조회 (중복 확인용)
    """
    try:
        response = news_table.scan(
            FilterExpression="provider_link_page = :url",
            ExpressionAttributeValues={":url": content_url}
        )
        items = response.get("Items", [])
        return items[0] if items else None
    except ClientError as e:
        raise Exception(f"[URL로 뉴스 조회 실패] {e.response['Error']['Message']}")

def get_today_news_grouped():
    """
    오늘 날짜 기준으로 카테고리별 뉴스 6건씩 묶어서 반환
    - 이미지가 있는 기사만 선별
    """
    today = datetime.now().strftime("%Y-%m-%d")
    result = {}
    for ko_category, en_category in CATEGORY_MAP.items():
        items = get_news_by_category_and_date(en_category["api_name"], today)
        # 이미지가 있는 기사만 필터링 (빈 문자열 제외)
        items_with_image = [
            item for item in items
            if item.get("images")  # 문자열이므로 빈 문자열은 자동으로 False
        ]
        result[ko_category] = items_with_image[:6]
    return result

def get_news_grouped_by_provider(date: str = None, limit_per_provider: int = 6):
    """
    언론사별로 뉴스를 그룹핑하여 반환 (Home 탭용)

    - 각 언론사별 첫 번째 기사는 이미지 있는 것으로 우선 배치
    - 나머지 기사는 이미지 유무 상관없이 최신순

    Args:
        date (str): 조회할 날짜 (YYYY-MM-DD), 기본값은 오늘
        limit_per_provider (int): 언론사별 최대 뉴스 개수 (기본 6개)

    Returns:
        dict: {"연합뉴스": [...], "조선일보": [...], ...}
    """
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    # 모든 카테고리에서 해당 날짜의 뉴스 수집
    all_news = []
    for ko_category, en_category in CATEGORY_MAP.items():
        items = get_news_by_category_and_date(en_category["api_name"], date)
        all_news.extend(items)

    # 언론사별로 그룹화
    provider_groups = {}
    for news in all_news:
        provider = news.get("provider")
        if not provider:
            continue

        if provider not in provider_groups:
            provider_groups[provider] = []

        provider_groups[provider].append(news)

    # 각 언론사 그룹 내에서 정렬 및 선별
    result = {}
    for provider, news_list in provider_groups.items():
        # 발행 시간 기준 최신순 정렬
        sorted_news = sorted(
            news_list,
            key=lambda x: x.get("published_at", ""),
            reverse=True
        )

        # 이미지 있는 기사와 없는 기사 분리
        news_with_image = [
            item for item in sorted_news
            if item.get("images")  # 문자열이므로 빈 문자열은 자동으로 False
        ]
        news_without_image = [
            item for item in sorted_news
            if not item.get("images")  # 빈 문자열 또는 None
        ]

        # 첫 번째는 이미지 있는 것 우선, 나머지는 최신순
        final_list = []
        if news_with_image:
            final_list.append(news_with_image[0])  # 첫 번째는 이미지 있는 기사
            # 나머지는 전체에서 최신순으로 (첫 번째 제외)
            remaining = [n for n in sorted_news if n != news_with_image[0]]
            final_list.extend(remaining[:limit_per_provider - 1])
        else:
            # 이미지 있는 기사가 하나도 없으면 그냥 최신순
            final_list = sorted_news[:limit_per_provider]

        result[provider] = final_list[:limit_per_provider]

    return result

def update_news_card_content(news_id: str, content: str):
    """
    news_id 기준으로 본문(content) 필드 업데이트
    """
    try:
        news_table.update_item(
            Key={"news_id": news_id},
            UpdateExpression="SET content = :c",
            ExpressionAttributeValues={":c": content}
        )
    except ClientError as e:
        raise Exception(f"[본문 업데이트 실패] {e.response['Error']['Message']}")

def update_news_card_content_by_url(content_url: str, content: str):
    """
    provider_link_page 기준으로 뉴스 찾아서 본문 업데이트
    (뉴스 ID를 모를 때 사용)
    """
    try:
        response = news_table.scan(
            FilterExpression="provider_link_page = :url",
            ExpressionAttributeValues={":url": content_url}
        )
        items = response.get("Items", [])
        if not items:
            raise Exception(f"[본문 업데이트 실패] URL로 해당 뉴스 없음 → {content_url}")
        news_id = items[0]["news_id"]
        update_news_card_content(news_id, content)
    except ClientError as e:
        raise Exception(f"[URL로 본문 업데이트 실패] {e.response['Error']['Message']}")

# ============================================
# 2. Frequencies 관련 함수
# ============================================

def save_frequency_summary(item: dict):
    """
    공유 요약 스크립트 및 음성 정보 저장
    """
    try:
        freq_table.put_item(Item=deep_convert(item))
    except ClientError as e:
        raise Exception(f"[Frequencies 저장 실패] {e.response['Error']['Message']}")

def get_frequency_by_category_and_date(category: str, date: str):
    """
    카테고리/날짜 기준 공유 요약 스크립트 조회
    """
    frequency_id = f"{category}#{date}"
    try:
        response = freq_table.get_item(Key={"frequency_id": frequency_id})
        return response.get("Item")
    except ClientError as e:
        raise Exception(f"[Frequencies 조회 실패] {e.response['Error']['Message']}")

def get_frequency_history_by_categories(categories: list, limit: int = 30):
    """
    사용자 관심 카테고리별 주파수 히스토리 조회 (최근 N일)
    """
    try:
        all_frequencies = []
        
        # 각 카테고리별로 데이터 수집
        for category in categories:
            # category로 시작하는 모든 frequency_id를 조회 (category#YYYY-MM-DD 형태)
            response = freq_table.scan(
                FilterExpression="begins_with(frequency_id, :category)",
                ExpressionAttributeValues={
                    ":category": f"{category}#"
                }
            )
            
            items = response.get("Items", [])
            all_frequencies.extend(items)
        
        # 날짜별로 정렬 (최신순)
        all_frequencies.sort(key=lambda x: x.get("date", ""), reverse=True)
        
        # 제한 개수만 반환
        return all_frequencies[:limit]
        
    except ClientError as e:
        raise Exception(f"[Frequency History 조회 실패] {e.response['Error']['Message']}")

# ============================================
# 3. Users 관련 함수
# ============================================

def save_user(user: dict):
    """
    사용자 정보 저장 (신규 또는 업데이트)
    - created_at, profile_image 기본값 자동 설정
    """
    if "created_at" not in user:
        user["created_at"] = datetime.utcnow().isoformat()
    if "profile_image" not in user:
        user["profile_image"] = ""

    try:
        users_table.put_item(Item=deep_convert(user))
    except ClientError as e:
        raise Exception(f"[Users 저장 실패] {e.response['Error']['Message']}")

def get_user(user_id: str):
    """
    user_id 기준 사용자 정보 조회
    - 기본값 자동 설정 (nickname, profile_image, interests 등)
    """
    try:
        response = users_table.get_item(Key={"user_id": user_id})
        item = response.get("Item")
        if not item:
            return None

        # 기본값 설정
        item.setdefault("nickname", "")
        item.setdefault("profile_image", "")
        item.setdefault("created_at", "")
        item.setdefault("interests", [])
        item.setdefault("onboarding_completed", False)

        return item
    except ClientError as e:
        raise Exception(f"[Users 조회 실패] {e.response['Error']['Message']}")

# ============================================
# 4. Bookmarks 관련 함수
# ============================================

def add_bookmark(user_id: str, news_id: str):
    """
    북마크 추가 (user_id + news_id 조합)
    """
    item = {
        "user_id": user_id,
        "news_id": news_id,
        "bookmarked_at": datetime.utcnow().isoformat()
    }
    try:
        bookmark_table.put_item(Item=item)
    except ClientError as e:
        raise Exception(f"[Bookmark 추가 실패] {e.response['Error']['Message']}")

def get_user_bookmarks(user_id: str):
    """
    user_id 기준으로 북마크 목록 조회 및 뉴스 상세 정보 포함
    """
    try:
        # 북마크 목록 조회
        response = bookmark_table.query(
            KeyConditionExpression="user_id = :uid",
            ExpressionAttributeValues={":uid": user_id},
            ScanIndexForward=False  # 최신 순 정렬
        )
        bookmark_items = response.get("Items", [])
        
        # 각 북마크에 대해 뉴스 상세 정보 조회
        bookmarked_news = []
        for bookmark in bookmark_items:
            news_id = bookmark.get("news_id")
            if news_id:
                try:
                    # 뉴스 상세 정보 조회
                    news_response = news_table.get_item(Key={"news_id": news_id})
                    news_item = news_response.get("Item")
                    if news_item:
                        # 북마크 시간 추가
                        news_item["bookmarked_at"] = bookmark.get("bookmarked_at")
                        bookmarked_news.append(news_item)
                except ClientError as e:
                    print(f"뉴스 상세 조회 실패 (news_id: {news_id}): {e}")
                    continue
        
        return bookmarked_news
    except ClientError as e:
        raise Exception(f"[Bookmark 조회 실패] {e.response['Error']['Message']}")

def remove_bookmark(user_id: str, news_id: str):
    """
    북마크 삭제 (user_id + news_id 키)
    """
    try:
        bookmark_table.delete_item(Key={"user_id": user_id, "news_id": news_id})
    except ClientError as e:
        raise Exception(f"[Bookmark 삭제 실패] {e.response['Error']['Message']}")


# ============================================
# 5. Headlines 관련 함수
# ============================================
headlines_table = dynamodb.Table(os.getenv("DDB_HEADLINES_TABLE", "Headlines"))


def save_headlines(category: str, date: str, headlines: list):
    """
    카테고리별 헤드라인 저장

    Args:
        category: 카테고리 (영문: politics, economy 등)
        date: 날짜 (YYYY-MM-DD)
        headlines: 헤드라인 리스트 [{
            "headline_id": str,
            "title": str,           # GPT 생성 헤드라인
            "summary": str,         # GPT 생성 요약 (~요, ~해요 체)
            "cluster_size": int,    # 클러스터 크기
            "representative_news_id": str,  # 대표 기사 ID
            "news_ids": List[str]   # 클러스터 내 기사 ID 목록
        }, ...]
    """
    item = {
        "category_date": f"{category}#{date}",  # PK
        "headlines": headlines,
        "created_at": datetime.utcnow().isoformat()
    }

    try:
        headlines_table.put_item(Item=deep_convert(item))
    except ClientError as e:
        raise Exception(f"[Headlines 저장 실패] {e.response['Error']['Message']}")


def get_headlines_by_category_and_date(category: str, date: str):
    """
    카테고리/날짜 기준 헤드라인 조회

    Args:
        category: 카테고리 (영문: politics, economy 등)
        date: 날짜 (YYYY-MM-DD)

    Returns:
        dict: {
            "category_date": "politics#2024-01-15",
            "headlines": [...],
            "created_at": "..."
        } 또는 None
    """
    key = f"{category}#{date}"
    try:
        response = headlines_table.get_item(Key={"category_date": key})
        return response.get("Item")
    except ClientError as e:
        raise Exception(f"[Headlines 조회 실패] {e.response['Error']['Message']}")


def get_all_headlines_by_date(date: str):
    """
    특정 날짜의 모든 카테고리 헤드라인 조회

    Args:
        date: 날짜 (YYYY-MM-DD)

    Returns:
        list: 모든 카테고리의 헤드라인 (클러스터 크기 기준 정렬됨)
    """
    all_headlines = []

    try:
        # 모든 카테고리에서 해당 날짜의 헤드라인 수집
        for ko_category, en_category in CATEGORY_MAP.items():
            category = en_category["api_name"]
            item = get_headlines_by_category_and_date(category, date)
            if item and item.get("headlines"):
                for headline in item["headlines"]:
                    headline["category"] = category
                    headline["category_ko"] = ko_category
                    all_headlines.append(headline)

        # 클러스터 크기 기준 내림차순 정렬
        all_headlines.sort(key=lambda x: x.get("cluster_size", 0), reverse=True)

        return all_headlines
    except Exception as e:
        raise Exception(f"[전체 Headlines 조회 실패] {e}")