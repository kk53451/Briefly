"""Supabase client singleton.

서비스 롤 키를 사용하므로 RLS를 우회합니다 (파이프라인 전용).
모바일에는 ANON 키를 별도로 사용해야 합니다.

env 값 검증을 초기화 시점에 수행해 placeholder/빈 값으로 파이프라인을 끝까지
돌리고서야 HTTP 헤더 인코딩 에러로 실패하는 상황을 방지합니다.
"""

import os
from functools import lru_cache

from supabase import Client, create_client


def _validate_url(url: str) -> None:
    if not url:
        raise RuntimeError(
            "SUPABASE_URL 가 .env 에 비어 있습니다. "
            "https://<project-ref>.supabase.co 형식으로 지정하세요."
        )
    if not url.startswith("https://") or not url.endswith(".supabase.co"):
        raise RuntimeError(
            f"SUPABASE_URL 형식이 올바르지 않습니다: {url!r}. "
            "Supabase Dashboard → Project Settings → API → Project URL 값을 복사하세요."
        )


def _validate_service_role_key(key: str) -> None:
    if not key:
        raise RuntimeError(
            "SUPABASE_SERVICE_ROLE_KEY 가 .env 에 비어 있습니다."
        )
    # JWT 는 base64(url-safe) 3 파트를 '.' 으로 이어붙인 ASCII 문자열.
    # placeholder 한글이나 임의 non-ASCII 가 들어오면 httpx 가 Authorization 헤더
    # 인코딩 단계에서 'ascii codec' 에러로 늦게 실패하므로 여기서 차단.
    if not key.isascii():
        raise RuntimeError(
            "SUPABASE_SERVICE_ROLE_KEY 에 비-ASCII 문자가 포함돼 있습니다. "
            "실제 JWT 키가 아니라 placeholder 가 그대로 남아 있을 가능성이 높습니다. "
            "Supabase Dashboard → Project Settings → API → service_role (secret) 값으로 교체하세요."
        )
    if key.count(".") != 2:
        raise RuntimeError(
            "SUPABASE_SERVICE_ROLE_KEY 가 JWT 형식이 아닙니다 (dot 3분할 실패). "
            "Supabase Dashboard → Project Settings → API → service_role (secret) 값을 재확인하세요."
        )
    if key.startswith("<") or "붙여넣기" in key or "여기에" in key:
        raise RuntimeError(
            "SUPABASE_SERVICE_ROLE_KEY 가 placeholder 문자열로 보입니다. 실제 키로 교체하세요."
        )


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    url = (os.environ.get("SUPABASE_URL") or "").strip()
    key = (os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
    _validate_url(url)
    _validate_service_role_key(key)
    return create_client(url, key)


def get_audio_bucket() -> str:
    return os.getenv("SUPABASE_AUDIO_BUCKET", "briefly-audio")
