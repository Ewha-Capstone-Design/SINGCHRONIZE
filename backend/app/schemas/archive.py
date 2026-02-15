"""Archive 스키마 - 부른 노래 기록"""
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime


class ArchiveCreate(BaseModel):
    song_id: UUID
    tags: List[str] = []
    memo: Optional[str] = None


class ArchiveUpdate(BaseModel):
    tags: Optional[List[str]] = None
    memo: Optional[str] = None


class ArchiveSongInfo(BaseModel):
    id: UUID
    title: str
    artist: str
    album_cover: Optional[str] = None

    model_config = {"from_attributes": True}


class ArchiveResponse(BaseModel):
    id: UUID
    user_id: UUID
    song: Optional[ArchiveSongInfo] = None
    tags: List[str] = []
    memo: Optional[str] = None
    recorded_date: datetime

    model_config = {"from_attributes": True}
