from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime

# 1. 방 생성 요청
class BuskingRoomCreate(BaseModel):
    title: str
    thumbnail: Optional[str] = None

# 2. 셋리스트 아이템 추가 요청
class SetlistItemCreate(BaseModel):
    song_id: UUID
    order_num: int # 1, 2, 3... 순서

# 3. 방 조회 응답 (리스트용)
class BuskingRoomResponse(BaseModel):
    id: UUID
    host_id: UUID
    title: str
    thumbnail: Optional[str]
    status: str # PREPARING, LIVE, ENDED
    total_viewers: int
    started_at: Optional[datetime]

    class Config:
        from_attributes = True