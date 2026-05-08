"""홈 라우터 — 이번주 차트 / 라이브 띠배너"""
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user, get_optional_user
from app.models.busking import BuskingRoom
from app.models.library import WishlistItem
from app.models.recorded_busking import RecordedBusking, RecordedBuskingReaction
from app.models.user import User
from app.routers.busking import manager as busking_manager
from app.schemas.recorded_busking import RecordedBuskingPreview, VoteRemaining

router = APIRouter(prefix="/api/v1", tags=["Home"])


# ── 스키마 ────────────────────────────────────────────
class WeeklySong(BaseModel):
    rank: int
    name: str
    artist: str
    album_image: Optional[str] = None
    uri: Optional[str] = None
    wish_count: int
    is_liked: bool = False

class LiveTickerItem(BaseModel):
    room_id: str
    title: str
    thumbnail: Optional[str] = None
    viewer_count: int

class HomeFeedsResponse(BaseModel):
    weekly: List[WeeklySong]
    live_ticker: List[LiveTickerItem]
    recorded_buskings: List[RecordedBuskingPreview] = []


# ── GET /api/v1/home/feeds ────────────────────────────
@router.get("/home/feeds", response_model=HomeFeedsResponse)
async def get_home_feeds(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    liked_rows = (await db.execute(
        select(WishlistItem.song_data).where(WishlistItem.user_id == current_user.id)
    )).scalars().all()
    liked_uris = {r.get("uri") for r in liked_rows if isinstance(r, dict) and r.get("uri")}

    weekly = await _get_weekly_chart(db, liked_uris)
    live_ticker = await _get_live_ticker(db)
    recorded_buskings = await _get_recorded_buskings(db)
    return HomeFeedsResponse(weekly=weekly, live_ticker=live_ticker, recorded_buskings=recorded_buskings)


# ── GET /api/v1/busking/live-ticker ──────────────────
@router.get("/busking/live-ticker", response_model=List[LiveTickerItem])
async def get_live_ticker(
    db: AsyncSession = Depends(get_db),
):
    return await _get_live_ticker(db)


# ── 내부 함수 ─────────────────────────────────────────
async def _get_weekly_chart(db: AsyncSession, liked_uris: Optional[set] = None) -> List[WeeklySong]:
    liked_uris = liked_uris or set()
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
            is_liked=song_map[key].get("uri") in liked_uris,
        )
        for i, (key, count) in enumerate(top5)
    ]


async def _get_recorded_buskings(db: AsyncSession, limit: int = 10) -> List[RecordedBuskingPreview]:
    from sqlalchemy import func
    items = (await db.execute(
        select(RecordedBusking)
        .order_by(RecordedBusking.created_at.desc())
        .limit(limit)
    )).scalars().all()
    if not items:
        return []

    busking_ids = [i.id for i in items]
    host_ids = list({i.host_id for i in items})

    hosts = {
        u.id: u for u in (await db.execute(
            select(User).where(User.id.in_(host_ids))
        )).scalars().all()
    }

    reaction_rows = (await db.execute(
        select(
            RecordedBuskingReaction.busking_id,
            RecordedBuskingReaction.value,
            func.count().label("cnt"),
        )
        .where(RecordedBuskingReaction.busking_id.in_(busking_ids))
        .group_by(RecordedBuskingReaction.busking_id, RecordedBuskingReaction.value)
    )).all()
    match_map: dict = {}
    mismatch_map: dict = {}
    for row in reaction_rows:
        if row.value == "match":
            match_map[row.busking_id] = row.cnt
        else:
            mismatch_map[row.busking_id] = row.cnt

    now = datetime.now(timezone.utc)

    def _remaining(vote_ends_at) -> VoteRemaining:
        if vote_ends_at.tzinfo is None:
            vote_ends_at = vote_ends_at.replace(tzinfo=timezone.utc)
        delta = vote_ends_at - now
        if delta.total_seconds() <= 0:
            return VoteRemaining(days=0, hours=0, minutes=0, is_ended=True)
        total = int(delta.total_seconds())
        return VoteRemaining(days=total // 86400, hours=(total % 86400) // 3600, minutes=(total % 3600) // 60, is_ended=False)

    result = []
    for item in items:
        host = hosts.get(item.host_id)
        if not host:
            continue
        result.append(RecordedBuskingPreview(
            id=item.id,
            host_nickname=host.nickname,
            host_profile_img=host.profile_img,
            title=item.title,
            thumbnail=item.thumbnail,
            song_data=item.song_data,
            vote_remaining=_remaining(item.vote_ends_at),
            match_count=match_map.get(item.id, 0),
            mismatch_count=mismatch_map.get(item.id, 0),
            created_at=item.created_at,
        ))
    return result


async def _get_live_ticker(db: AsyncSession) -> List[LiveTickerItem]:
    result = await db.execute(
        select(BuskingRoom).where(BuskingRoom.status == "LIVE").limit(20)
    )
    rooms = result.scalars().all()
    ticker = [
        LiveTickerItem(
            room_id=str(r.id),
            title=r.title,
            thumbnail=r.thumbnail,
            viewer_count=busking_manager.viewer_count(r.id),
        )
        for r in rooms
    ]
    ticker.sort(key=lambda x: x.viewer_count, reverse=True)
    return ticker[:10]
