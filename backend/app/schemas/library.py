"""Library 스키마 - Folder & Wishlist"""
from pydantic import BaseModel, computed_field
from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime


# ── Folder ──────────────────────────────────────────

class FolderCreate(BaseModel):
    name: str


class FolderUpdate(BaseModel):
    name: str


class FolderResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    is_system: bool
    created_at: datetime
    item_count: int = 0
    thumbnails: List[str] = []   # 최신 찜 항목 앨범 커버 최대 4개

    model_config = {"from_attributes": True}


# ── WishlistItem ────────────────────────────────────

class WishlistItemCreate(BaseModel):
    # Spotify 검색 결과 그대로: { name, artist, album_image, uri }
    song_data: Dict[str, Any]
    folder_id: Optional[UUID] = None


class WishlistItemResponse(BaseModel):
    id: UUID
    user_id: UUID
    folder_id: Optional[UUID] = None
    song_data: Dict[str, Any]
    created_at: datetime

    @computed_field
    @property
    def song_id(self) -> UUID:
        return self.id

    model_config = {"from_attributes": True}
