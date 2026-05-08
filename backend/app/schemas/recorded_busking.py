"""녹음 버스킹 스키마"""
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime


class RecordingUploadUrlResponse(BaseModel):
    upload_url: str
    s3_key: str
    public_url: str


class RecordedBuskingCreate(BaseModel):
    title: str
    thumbnail_url: Optional[str] = None
    s3_key: str                     # upload-url 엔드포인트에서 받은 키
    song_data: Dict[str, Any]       # { name, artist, album_image, uri }
    vote_ends_at: datetime          # 투표 종료 시각 (ISO8601)


class HostProfile(BaseModel):
    id: UUID
    nickname: str
    profile_img: Optional[str] = None


class VoteRemaining(BaseModel):
    days: int
    hours: int
    minutes: int
    is_ended: bool


class RecordedBuskingResponse(BaseModel):
    id: UUID
    host_profile: HostProfile
    title: str
    thumbnail: Optional[str] = None
    recording_url: str
    song_data: Dict[str, Any]
    vote_ends_at: datetime
    vote_remaining: VoteRemaining
    match_count: int
    mismatch_count: int
    comment_count: int
    my_reaction: Optional[str] = None   # 'match' | 'mismatch' | None
    created_at: datetime


class RecordedBuskingPreview(BaseModel):
    """홈 화면 용 경량 응답"""
    id: UUID
    host_nickname: str
    host_profile_img: Optional[str] = None
    title: str
    thumbnail: Optional[str] = None
    song_data: Dict[str, Any]
    vote_remaining: VoteRemaining
    match_count: int
    mismatch_count: int
    created_at: datetime


class CommentCreate(BaseModel):
    content: str


class CommentResponse(BaseModel):
    id: UUID
    user_id: UUID
    nickname: str
    profile_img: Optional[str] = None
    content: str
    created_at: datetime


class ReactionRequest(BaseModel):
    value: str  # 'match' | 'mismatch'
