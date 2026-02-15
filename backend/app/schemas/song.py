from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime


class SongBase(BaseModel):
    id: UUID
    title: str
    artist: str
    tags: Optional[str] = None
    features: Optional[str] = None
    album_cover: Optional[str] = None
    genre: Optional[str] = None
    youtube_url: Optional[str] = None
    raw_s3_key: Optional[str] = None
    download_status: Optional[str] = None
    embedding_status: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SongResponse(BaseModel):
    songs: List[SongBase]
