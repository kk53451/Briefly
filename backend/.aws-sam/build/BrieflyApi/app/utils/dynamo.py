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

# ============================================
# 1. NewsCards 관련 함수
# ============================================

def save_news_card(category: str, article: dict, date_str: str):
    """
    뉴스 기사 1건을 NewsCards 테이블에 저장
    """
    item = {
        "news_id": article["id"],
        "category_date": f"{category}#{date_str}",  # GSI용 복합 키
        "category": category,
        "section": article.get("sections", [])[0] if article.get("sections") else "domestic",
        "rank": article.get("rank"),
        "title": article.get("title"),
        "title_ko": article.get("title_ko"),
        "summary": article.get("summary"),
        "summary_ko": article.get("summary_ko"),
        "image_url": article.get("image_url"),
        "thumbnail_url": article.get("thumbnail_url") or article.get("thumbnail"),
        "content_url": article.get("content_url"),
        "publisher": article.get("publisher"),
        "author": article.get("author"),
        "published_at": article.get("published_at"),
        "collected_at": datetime.utcnow().isoformat(),
        "companies": article.get("companies", []),
        "esg": article.get("esg", []),
        "content": article.get("content", "")
    }

    try:
        news_table.put_item(Item=deep_convert(item))
    except ClientError as e:
        raise Exception(f"[NewsCards 저장 실패] {e.response['Error']['Message']}")

def get_news_by_category_and_date(category: str, date: str):
    """
    category와 date 기준으로 뉴스 목록 조회 (최신 30~60건)
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
    content_url 기준으로 뉴스 조회 (중복 확인용)
    """
    try:
        response = news_table.scan(
            FilterExpression="content_url = :url",
            ExpressionAttributeValues={":url": content_url}
        )
        items = response.get("Items", [])
        return items[0] if items else None
    except ClientError as e:
        raise Exception(f"[URL로 뉴스 조회 실패] {e.response['Error']['Message']}")

def get_today_news_grouped():
    """
    오늘 날짜 기준으로 카테고리별 뉴스 6건씩 묶어서 반환
    """
    today = datetime.now().strftime("%Y-%m-%d")
    result = {}
    for ko_category, en_category in CATEGORY_MAP.items():
        items = get_news_by_category_and_date(en_category["api_name"], today)
        result[ko_category] = items[:6]
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
    content_url 기준으로 뉴스 찾아서 본문 업데이트
    (뉴스 ID를 모를 때 사용)
    """
    try:
        response = news_table.scan(
            FilterExpression="content_url = :url",
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