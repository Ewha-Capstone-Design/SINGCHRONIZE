"""아티스트 선호/차단 스키마"""
from pydantic import BaseModel, field_validator
from typing import List, Literal
from uuid import UUID
from datetime import datetime


class ArtistActionRequest(BaseModel):
    artist_name: str
    action: Literal["PREFER", "BLOCK"]


class ArtistActionResponse(BaseModel):
    id: UUID
    artist_name: str
    action: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ArtistActionsListResponse(BaseModel):
    actions: List[ArtistActionResponse]
