"""Library 스키마 - Folder & Wishlist"""
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime


# ── Folder ──────────────────────────────────────────

class FolderCreate(BaseModel):
    name: str


class FolderResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    is_system: bool
    created_at: datetime
    item_count: int = 0

    model_config = {"from_attributes": True}


# ── WishlistItem ────────────────────────────────────

class WishlistItemCreate(BaseModel):
    song_id: UUID
    folder_id: Optional[UUID] = None


class WishlistSongInfo(BaseModel):
    id: UUID
    title: str
    artist: str
    album_cover: Optional[str] = None

    model_config = {"from_attributes": True}


class WishlistItemResponse(BaseModel):
    id: UUID
    user_id: UUID
    folder_id: Optional[UUID] = None
    song: WishlistSongInfo
    created_at: datetime

    model_config = {"from_attributes": True}
