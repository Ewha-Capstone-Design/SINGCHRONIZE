"""Singer 스키마"""
from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import datetime
from uuid import UUID


# ── Random Singers ───────────────────────────────────

class SingerInfo(BaseModel):
    singer_id: int
    name: str
    photo_url: Optional[str] = None

    model_config = {"from_attributes": True}


class RandomSingersResponse(BaseModel):
    singers: List[SingerInfo]


class SingerSearchResponse(BaseModel):
    singers: List[SingerInfo]


# ── Favorite Singers (온보딩 2단계) ──────────────────

class FavoriteSingersSelectRequest(BaseModel):
    singer_ids: List[int]

    @field_validator("singer_ids")
    @classmethod
    def validate_singer_ids(cls, v: List[int]) -> List[int]:
        if not v:
            raise ValueError("가수를 최소 1명 이상 선택해야 합니다.")
        if len(v) != len(set(v)):
            raise ValueError("중복된 가수 ID가 포함되어 있습니다.")
        return v


class FavoriteSingersSelectResponse(BaseModel):
    singers: List[SingerInfo]


# ── Blocked Singer ───────────────────────────────────

class BlockSingerRequest(BaseModel):
    singer_id: int


class BlockSingerResponse(BaseModel):
    id: str
    created_at: datetime


class BlockedSingerItem(BaseModel):
    block_id: int
    singer_id: int
    name: str
    photo_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class BlockedSingersListResponse(BaseModel):
    blocked_singers: List[BlockedSingerItem]


# ── Blocked Song ──────────────────────────────────────

class BlockSongRequest(BaseModel):
    song_id: UUID


class BlockedSongItem(BaseModel):
    block_id: int
    song_id: UUID
    title: str
    artist: str
    album_cover: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class BlockedSongsListResponse(BaseModel):
    blocked_songs: List[BlockedSongItem]
