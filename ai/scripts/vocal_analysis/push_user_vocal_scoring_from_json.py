#!/usr/bin/env python3
"""
로컬/수동: 파이프라인 결과 JSON → user_vocal_profiles 의 1차 추천용 컬럼 반영.

실행 (vocal_analysis 디렉터리에서):
  python push_user_vocal_scoring_from_json.py --user-id <uuid> --json output/<id>_result.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

_env_paths = [
    Path(__file__).resolve().parent.parent.parent / ".env",
    Path(__file__).resolve().parent.parent.parent.parent / ".env",
]
for _p in _env_paths:
    if _p.exists():
        load_dotenv(_p)
        break
else:
    load_dotenv()

from user_song_aligned_features import build_scoring_song_aligned_from_pipeline_result
from user_vocal_profile_sync import (
    ANALYSIS_JOBS_USER_COLUMN,
    USER_VOCAL_PROFILES_TABLE,
    profile_columns_from_scoring_song_aligned,
    sync_user_vocal_profile_after_job,
)


def _extract_scoring_aligned_from_loaded(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not isinstance(data, dict):
        return None
    inner = data.get("scoring_song_aligned")
    if isinstance(inner, dict) and inner.get("vocal_repr_embedding"):
        return inner
    rd = data.get("result_data")
    if isinstance(rd, dict):
        inner2 = rd.get("scoring_song_aligned")
        if isinstance(inner2, dict) and inner2.get("vocal_repr_embedding"):
            return inner2
    return build_scoring_song_aligned_from_pipeline_result(data)


def _get_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY 가 .env 에 필요합니다.")
    from supabase import create_client

    return create_client(url, key)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="파이프라인 JSON → user_vocal_profiles 1차 추천용 컬럼 반영"
    )
    parser.add_argument("--user-id", type=str, required=True)
    parser.add_argument("--json", type=str, required=True)
    parser.add_argument(
        "--full-sync",
        action="store_true",
        help="analysis_jobs 이력으로 리포트 누적 필드까지 재집계",
    )
    args = parser.parse_args()

    json_path = Path(args.json)
    if not json_path.is_file():
        print(f"❌ 파일 없음: {json_path}", file=sys.stderr)
        return 1

    with open(json_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    aligned = _extract_scoring_aligned_from_loaded(raw)
    if not aligned:
        print("❌ scoring_song_aligned 를 만들 수 없습니다 (features 필요).", file=sys.stderr)
        return 1

    cols = profile_columns_from_scoring_song_aligned(aligned)
    if not cols.get("vocal_repr_embedding"):
        print("❌ vocal_repr_embedding 이 비었습니다.", file=sys.stderr)
        return 1

    supabase = _get_supabase()
    uid = args.user_id.strip()
    now = datetime.now(timezone.utc).isoformat()
    patch = {**cols, "updated_at": now}

    try:
        existing = (
            supabase.table(USER_VOCAL_PROFILES_TABLE)
            .select(ANALYSIS_JOBS_USER_COLUMN)
            .eq(ANALYSIS_JOBS_USER_COLUMN, uid)
            .limit(1)
            .execute()
        )
        has_row = bool(existing.data)
        if has_row:
            supabase.table(USER_VOCAL_PROFILES_TABLE).update(patch).eq(
                ANALYSIS_JOBS_USER_COLUMN, uid
            ).execute()
            print(f"✓ UPDATE {USER_VOCAL_PROFILES_TABLE} user_id={uid}")
        else:
            supabase.table(USER_VOCAL_PROFILES_TABLE).insert(
                {ANALYSIS_JOBS_USER_COLUMN: uid, **patch}
            ).execute()
            print(f"✓ INSERT {USER_VOCAL_PROFILES_TABLE} user_id={uid}")
    except Exception as e:
        print(f"❌ DB 실패: {e}", file=sys.stderr)
        return 1

    if args.full_sync:
        sync_user_vocal_profile_after_job(supabase, user_id=uid)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
