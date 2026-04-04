"""
Supabase(PostgREST) 기반 stage3 데이터 접근.

테이블·컬럼은 기존 백엔드/워커와 동일하게 맞춤:
- user_vocal_profiles.vocal_repr_embedding (vector → API 응답은 문자열/리스트)
- wishlist_items (user_id, song_id, created_at)
- blocked_songs, wishlist_items → 요청 유저 제외 집합
- song_features.song_repr_embedding → 유저-곡 음색 유사도(호환도) 프록시
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple
from zoneinfo import ZoneInfo

import numpy as np

from app.db.client import get_supabase

USER_ID_COL = (os.getenv("STAGE3_USER_ID_COLUMN") or "user_id").strip()
USER_VOCAL_TABLE = (os.getenv("USER_VOCAL_PROFILES_TABLE") or "user_vocal_profiles").strip()
WISHLIST_TABLE = (os.getenv("STAGE3_WISHLIST_TABLE") or "wishlist_items").strip()
BLOCKED_TABLE = (os.getenv("STAGE3_BLOCKED_TABLE") or "blocked_songs").strip()
SONG_FEATURES_TABLE = (os.getenv("STAGE3_SONG_FEATURES_TABLE") or "song_features").strip()
MAX_PROFILE_ROWS = int(os.getenv("STAGE3_MAX_PROFILE_ROWS") or "8000")
IN_CHUNK = int(os.getenv("STAGE3_SUPABASE_IN_CHUNK") or "80")
# period=today 일 때 자정 기준 타임존 (예: Asia/Seoul). 미설정·UTC 는 UTC 자정.
CALENDAR_TZ = (os.getenv("STAGE3_CALENDAR_TZ") or "UTC").strip()


def _parse_vector(value: Any) -> Optional[np.ndarray]:
    if value is None:
        return None
    if isinstance(value, str):
        s = value.strip()
        if s.startswith("[") and s.endswith("]"):
            parts = [p.strip() for p in s.strip("[]").split(",") if p.strip()]
        else:
            parts = [p for p in s.replace(",", " ").split() if p]
        try:
            arr = np.array([float(x) for x in parts], dtype=np.float64)
        except ValueError:
            return None
    elif isinstance(value, (list, tuple)):
        try:
            arr = np.array([float(x) for x in value], dtype=np.float64)
        except (TypeError, ValueError):
            return None
    else:
        return None
    if arr.size == 0:
        return None
    return arr


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def interaction_window_from_period(period: str) -> Tuple[datetime, datetime]:
    """
    위시 집계 구간 [since, until] (둘 다 UTC, 양끝 포함으로 쿼리).

    - until: 항상 «요청 시각» UTC (미래 위시 제외)
    - today: STAGE3_CALENDAR_TZ 자정 ~ 지금 (한국 서비스면 Asia/Seoul 권장)
    - week / month: 지금 기준 과거 N일
    """
    until = datetime.now(timezone.utc)
    p = (period or "week").strip().lower()
    if p == "today":
        tzname = CALENDAR_TZ.upper()
        if tzname in ("UTC", "Z", ""):
            local_now = until
        else:
            local_now = until.astimezone(ZoneInfo(CALENDAR_TZ))
        start_local = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
        since = start_local.astimezone(timezone.utc)
    elif p == "month":
        since = until - timedelta(days=30)
    else:
        since = until - timedelta(days=7)
    return since, until


def resolve_interaction_window(
    period: str,
    interaction_since: Optional[datetime],
    interaction_until: Optional[datetime],
) -> Tuple[datetime, datetime]:
    """
    API 요청 → 실제 DB 필터 구간.

    - interaction_since 가 있으면 하한은 그 값(UTC 변환), 없으면 period 기반
    - interaction_until 이 있으면 상한은 그 값(UTC 변환), 없으면 요청 시각 UTC
    """
    since_default, until_default = interaction_window_from_period(period)
    since = _ensure_utc(interaction_since) if interaction_since is not None else since_default
    until = _ensure_utc(interaction_until) if interaction_until is not None else until_default
    return since, until


def get_user_embedding(user_id: str) -> Optional[np.ndarray]:
    supabase = get_supabase()
    res = (
        supabase.table(USER_VOCAL_TABLE)
        .select(f"{USER_ID_COL}, vocal_repr_embedding")
        .eq(USER_ID_COL, user_id)
        .limit(1)
        .execute()
    )
    row = (res.data or [None])[0]
    if not row:
        return None
    return _parse_vector(row.get("vocal_repr_embedding"))


def get_all_user_embeddings() -> List[Dict[str, Any]]:
    supabase = get_supabase()
    out: List[Dict[str, Any]] = []
    offset = 0
    page = min(1000, max(1, MAX_PROFILE_ROWS))
    while len(out) < MAX_PROFILE_ROWS:
        res = (
            supabase.table(USER_VOCAL_TABLE)
            .select(f"{USER_ID_COL}, vocal_repr_embedding")
            .not_.is_("vocal_repr_embedding", "null")
            .range(offset, offset + page - 1)
            .execute()
        )
        batch = res.data or []
        if not batch:
            break
        for row in batch:
            uid = row.get(USER_ID_COL)
            emb = _parse_vector(row.get("vocal_repr_embedding"))
            if uid is not None and emb is not None:
                out.append({"user_id": str(uid), "embedding": emb})
                if len(out) >= MAX_PROFILE_ROWS:
                    break
        if len(batch) < page:
            break
        offset += page
    return out


def _chunks(seq: Sequence[str], size: int) -> List[List[str]]:
    return [list(seq[i : i + size]) for i in range(0, len(seq), size)]


def get_neighbor_interactions(
    user_ids: Sequence[str],
    period: str,
    interaction_since: Optional[datetime] = None,
    interaction_until: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    if not user_ids:
        return []
    supabase = get_supabase()
    since, until = resolve_interaction_window(period, interaction_since, interaction_until)
    since_iso = since.isoformat()
    until_iso = until.isoformat()
    rows: List[Dict[str, Any]] = []
    for chunk in _chunks(list(user_ids), IN_CHUNK):
        res = (
            supabase.table(WISHLIST_TABLE)
            .select(f"{USER_ID_COL}, song_id, created_at")
            .in_(USER_ID_COL, chunk)
            .gte("created_at", since_iso)
            .lte("created_at", until_iso)
            .execute()
        )
        for r in res.data or []:
            uid = r.get(USER_ID_COL)
            sid = r.get("song_id")
            if uid is None or sid is None:
                continue
            rows.append(
                {
                    "user_id": str(uid),
                    "song_id": str(sid),
                    "weight": 1.0,
                }
            )
    return rows


def get_user_excluded_songs(user_id: str) -> set[str]:
    supabase = get_supabase()
    excluded: set[str] = set()
    try:
        b = (
            supabase.table(BLOCKED_TABLE)
            .select("song_id")
            .eq(USER_ID_COL, user_id)
            .execute()
        )
        for r in b.data or []:
            sid = r.get("song_id")
            if sid is not None:
                excluded.add(str(sid))
    except Exception:
        pass
    try:
        w = (
            supabase.table(WISHLIST_TABLE)
            .select("song_id")
            .eq(USER_ID_COL, user_id)
            .execute()
        )
        for r in w.data or []:
            sid = r.get("song_id")
            if sid is not None:
                excluded.add(str(sid))
    except Exception:
        pass
    return excluded


def get_song_embedding(song_id: str) -> Optional[np.ndarray]:
    supabase = get_supabase()
    res = (
        supabase.table(SONG_FEATURES_TABLE)
        .select("song_id, song_repr_embedding")
        .eq("song_id", song_id)
        .limit(1)
        .execute()
    )
    row = (res.data or [None])[0]
    if not row:
        return None
    return _parse_vector(row.get("song_repr_embedding"))
