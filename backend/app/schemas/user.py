"""사용자 관련 스키마"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from app.schemas.singer import BlockedSongItem, SingerInfo


class UserResponse(BaseModel):
    """기본 유저 응답 - 인증/수정 결과 반환용"""
    id: UUID
    nickname: str
    email: Optional[str] = None
    profile_img: Optional[str] = None
    bio: Optional[str] = None
    provider: str
    vocal_summary: Optional[Dict[str, Any]] = Field(
        None, validation_alias="vocal_summary_cache"
    )
    settings: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True, "populate_by_name": True}


class UserMeResponse(UserResponse):
    """GET /users/me 전용 - 선호 가수, 차단 가수, 차단 곡, 연동 SNS 포함"""
    favorite_singers: List[SingerInfo] = []
    blocked_singers: List[SingerInfo] = []
    blocked_songs: List[BlockedSongItem] = []
    linked_providers: List[str] = []   # e.g. ["kakao", "naver"]


class UserUpdateRequest(BaseModel):
    """PATCH /users/me 요청"""
    nickname: Optional[str] = Field(None, min_length=1, max_length=20)


class SettingsUpdateRequest(BaseModel):
    """PATCH /users/me/settings 요청 - JSONB 부분 업데이트"""
    push_enabled: Optional[bool] = None
    marketing_agree: Optional[bool] = None
