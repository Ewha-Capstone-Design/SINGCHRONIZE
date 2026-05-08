"""Archive 스키마 - 부른 노래 기록"""
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime


class ArchiveCreate(BaseModel):
    # Spotify 검색 결과 그대로: { name, artist, album_image, uri }
    song_data: Dict[str, Any]
    tags: List[str] = []
    memo: Optional[str] = None


class ArchiveUpdate(BaseModel):
    tags: Optional[List[str]] = None
    memo: Optional[str] = None


class ArchiveResponse(BaseModel):
    id: UUID
    user_id: UUID
    song_data: Dict[str, Any]
    tags: List[str] = []
    memo: Optional[str] = None
    recorded_date: datetime
    is_liked: bool = False

    model_config = {"from_attributes": True}
