"""홈 라우터 — 이번주 차트 / 라이브 띠배너"""
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.busking import BuskingRoom
from app.models.library import WishlistItem
from app.models.user import User

router = APIRouter(prefix="/api/v1", tags=["Home"])


# ── 스키마 ────────────────────────────────────────────
class WeeklySong(BaseModel):
    rank: int
    name: str
    artist: str
    album_image: Optional[str] = None
    uri: Optional[str] = None
    wish_count: int

class LiveTickerItem(BaseModel):
    room_id: str
    title: str
    thumbnail: Optional[str] = None
    viewer_count: int

class HomeFeedsResponse(BaseModel):
    weekly: List[WeeklySong]
    live_ticker: List[LiveTickerItem]


# ── GET /api/v1/home/feeds ────────────────────────────
@router.get("/home/feeds", response_model=HomeFeedsResponse)
async def get_home_feeds(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    weekly = await _get_weekly_chart(db)
    live_ticker = await _get_live_ticker(db)
    return HomeFeedsResponse(weekly=weekly, live_ticker=live_ticker)


# ── GET /api/v1/busking/live-ticker ──────────────────
@router.get("/busking/live-ticker", response_model=List[LiveTickerItem])
async def get_live_ticker(
    db: AsyncSession = Depends(get_db),
):
    return await _get_live_ticker(db)


# ── 내부 함수 ─────────────────────────────────────────
async def _get_weekly_chart(db: AsyncSession) -> List[WeeklySong]:
    since = datetime.now(timezone.utc) - timedelta(days=7)

    result = await db.execute(
        select(WishlistItem.song_data)
        .where(WishlistItem.created_at >= since)
    )
    rows = result.scalars().all()

    # 이번 주 데이터가 부족하면 전체 기간으로 fallback
    if len(rows) < 5:
        result = await db.execute(select(WishlistItem.song_data))
        rows = result.scalars().all()

    counter: Counter = Counter()
    song_map: Dict[str, Any] = {}

    for data in rows:
        if not isinstance(data, dict):
            continue
        # uri가 있으면 uri, 없으면 name::artist 로 동일 곡 판별
        key = data.get("uri") or f"{data.get('name', '')}::{data.get('artist', '')}"
        if not key or key == "::":
            continue
        counter[key] += 1
        song_map[key] = data

    top5 = counter.most_common(5)
    return [
        WeeklySong(
            rank=i + 1,
            name=song_map[key].get("name", ""),
            artist=song_map[key].get("artist", ""),
            album_image=song_map[key].get("album_image"),
            uri=song_map[key].get("uri"),
            wish_count=count,
        )
        for i, (key, count) in enumerate(top5)
    ]


async def _get_live_ticker(db: AsyncSession) -> List[LiveTickerItem]:
    result = await db.execute(
        select(BuskingRoom)
        .where(BuskingRoom.status == "LIVE")
        .order_by(BuskingRoom.total_viewers.desc())
        .limit(10)
    )
    rooms = result.scalars().all()
    return [
        LiveTickerItem(
            room_id=str(r.id),
            title=r.title,
            thumbnail=r.thumbnail,
            viewer_count=r.total_viewers or 0,
        )
        for r in rooms
    ]
