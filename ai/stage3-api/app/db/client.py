import os
from functools import lru_cache
from typing import Any


@lru_cache(maxsize=1)
def get_supabase() -> Any:
    url = (os.getenv("SUPABASE_URL") or "").strip()
    key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL 및 SUPABASE_SERVICE_ROLE_KEY 환경 변수가 필요합니다."
        )
    from supabase import create_client

    return create_client(url, key)
