"""Singer 스키마"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


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


# ── Blocked Singer ───────────────────────────────────

class BlockSingerRequest(BaseModel):
    type: str        # "ARTIST" | "SONG"
    target_id: str   # singer_id (문자열로 수신)


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
