"""Supabase storage_service 단순 smoke test (ML 모델 없이).

실행:
    cd backend_v2_supabase
    pip install supabase python-dotenv
    PYTHONIOENCODING=utf-8 python -m test.test_supabase_storage_smoke

선결 조건:
    .env 의 SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY 가 채워져 있을 것.

통합 브리핑 리워크(2026-04-19) 이후 변경 사항:
- `save_pipeline_result` 는 제거됨 → 새 `save_podcast` 사용.
- `frequencies` 테이블은 `podcasts` 로 이름 변경, category 컬럼 제거.
- 실제 프로덕션 데이터와 충돌을 피하려고 `TEST_DATE` 를 원거리 미래 날짜로 고정.
"""
import os
import sys
import tempfile
from datetime import date

from dotenv import load_dotenv

load_dotenv()

for var in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"):
    if not os.getenv(var) or os.getenv(var, "").startswith("<"):
        print(f"❌ {var} 가 .env에 비어있거나 placeholder 입니다.")
        sys.exit(1)

from app.services.supabase_storage_service import (
    save_news_cards,
    save_headlines,
    save_podcast,
)
from app.utils.supabase_client import get_supabase

# 실제 파이프라인 데이터(오늘 날짜)와 충돌하지 않도록 원거리 미래 날짜 고정.
# podcasts 는 UNIQUE(date, slot) 라 실제 오늘 row 와 같은 date+slot 을 upsert하면 덮어씁니다.
TEST_DATE = "2099-12-31"
SLOT = "AM"
FEED_CATEGORY = "smoke_test"  # news_cards / headlines 는 category 가 살아 있음


def test_news_cards():
    fake_topics = [
        {
            "size": 5,
            "representative_article": {
                "title": f"Smoke test 기사 {i}",
                "link": f"https://news.naver.com/article/001/000000000{i}",
                "press": "테스트통신",
                "thumbnail": "https://example.com/img.jpg",
                "lede": "테스트 본문 요약",
                "content": "전체 본문" * 10,
                "published_at": "2099-12-31T08:00:00+09:00",
            },
        }
        for i in range(3)
    ]
    saved = save_news_cards(fake_topics, FEED_CATEGORY, TEST_DATE, max_cards=3, slot=SLOT)
    assert saved == 3, f"news_cards 저장 개수 불일치: {saved}"
    print(f"✅ save_news_cards: {saved}건")


def test_headlines():
    fake_headlines = [
        {
            "topic_id": 1,
            "headline": "테스트 헤드라인",
            "summary": "테스트 요약",
            "size": 5,
            "representative_article": {
                "news_id": "smoke_001",
                "title": "테스트 대표 기사",
                "press": "테스트통신",
            },
            "keywords": [("키워드1", 0.9), ("키워드2", 0.8)],
        }
    ]
    ok = save_headlines(FEED_CATEGORY, TEST_DATE, fake_headlines, slot=SLOT)
    assert ok, "headlines 저장 실패"
    print(f"✅ save_headlines: 1건")


def test_podcast_no_audio():
    res = save_podcast(TEST_DATE, SLOT, "테스트 대본입니다.", audio_path=None)
    assert res["saved"], f"podcasts 저장 실패: {res}"
    assert res["audio_path"] is None
    assert res["podcast_id"] == f"{TEST_DATE}#{SLOT}"
    print(f"✅ save_podcast (대본만): {res['podcast_id']}")


def test_podcast_with_audio():
    # 최소한의 mp3 헤더만 있는 더미 파일 (재생 안 되지만 업로드/경로 검증용)
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(b"ID3\x04\x00\x00\x00\x00\x00\x00")
        f.write(b"\x00" * 1024)
        temp_mp3 = f.name

    try:
        res = save_podcast(TEST_DATE, SLOT, "오디오 포함 테스트 대본", audio_path=temp_mp3)
        assert res["saved"], f"podcasts 저장 실패: {res}"
        assert res["audio_path"] == f"{TEST_DATE}/briefing_{SLOT}.mp3"
        print(f"✅ save_podcast (오디오 포함): {res['audio_path']}")

        url = (
            get_supabase()
            .storage.from_("briefly-audio")
            .get_public_url(res["audio_path"])
        )
        print(f"  → public URL: {url}")
    finally:
        os.unlink(temp_mp3)


def cleanup():
    sb = get_supabase()
    sb.table("news_cards").delete().eq("category", FEED_CATEGORY).execute()
    sb.table("headlines").delete().eq("category", FEED_CATEGORY).execute()
    sb.table("podcasts").delete().eq("date", TEST_DATE).execute()
    try:
        sb.storage.from_("briefly-audio").remove([f"{TEST_DATE}/briefing_{SLOT}.mp3"])
    except Exception:
        pass
    print("🧹 cleanup 완료")


if __name__ == "__main__":
    print(f"=== Supabase smoke test (test_date={TEST_DATE}, feed_category={FEED_CATEGORY}) ===")
    try:
        test_news_cards()
        test_headlines()
        test_podcast_no_audio()
        test_podcast_with_audio()
        print("\n🎉 모든 테스트 통과")
    finally:
        cleanup()
