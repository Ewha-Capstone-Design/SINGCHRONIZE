from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, field_validator


# ── Request ───────────────────────────────────────────────────

class SetlistItemCreate(BaseModel):
    song_id: Optional[str] = None
    title: str
    artist: str
    album_art_url: Optional[str] = None
    order_index: int


class BuskingRoomCreate(BaseModel):
    title: str
    thumbnail_url: Optional[str] = None
    setlist: List[SetlistItemCreate]

    @field_validator("setlist")
    @classmethod
    def validate_setlist_length(cls, v: list) -> list:
        if not (3 <= len(v) <= 5):
            raise ValueError("셋리스트는 3~5곡이어야 합니다.")
        return v


# ── Response ──────────────────────────────────────────────────

class SetlistItemResponse(BaseModel):
    id: UUID
    song_id: Optional[str]
    title: str
    artist: str
    album_art_url: Optional[str]
    order_index: int

    class Config:
        from_attributes = True


class BuskingRoomResponse(BaseModel):
    id: UUID
    host_id: UUID
    title: str
    thumbnail: Optional[str]
    status: str
    current_song_index: int
    total_viewers: int
    peak_viewer_count: int
    started_at: Optional[datetime]
    ended_at: Optional[datetime]

    class Config:
        from_attributes = True


class BuskingRoomDetailResponse(BuskingRoomResponse):
    setlist: List[SetlistItemResponse] = []


class BuskingResultResponse(BaseModel):
    live_id: UUID
    title: str
    duration_seconds: Optional[int]
    peak_viewer_count: int
    total_unique_viewers: int
    setlist: List[SetlistItemResponse]
    reactions: dict
    chat_count: int
    started_at: Optional[datetime]
    ended_at: Optional[datetime]


class ThumbnailPresignedResponse(BaseModel):
    upload_url: str
    s3_url: str
    key: str


class BuskingRoomCreateResponse(BuskingRoomDetailResponse):
    """방 생성 응답 — LiveKit 호스트 토큰 포함."""
    livekit_token: str
    livekit_url: str


class LiveKitJoinResponse(BaseModel):
    """뷰어 입장 응답 — LiveKit 뷰어 토큰 포함."""
    livekit_token: str
    livekit_url: str
    room_id: UUID
