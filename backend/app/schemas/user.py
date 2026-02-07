"""사용자 관련 스키마"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

<<<<<<< HEAD

=======
>>>>>>> 37619415d32128e6eb47e75d2ff2f2a1d689c018
class UserResponse(BaseModel):
    """GET /users/me 응답 - 보컬 캐시 포함"""
    id: UUID
    nickname: str
    email: Optional[str] = None
    profile_img: Optional[str] = None
    provider: str
    vocal_summary: Optional[Dict[str, Any]] = Field(
        None, validation_alias="vocal_summary_cache"
    )
    settings: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True, "populate_by_name": True}


class UserUpdateRequest(BaseModel):
    """PATCH /users/me 요청"""
    nickname: Optional[str] = Field(None, min_length=1, max_length=20)


class SettingsUpdateRequest(BaseModel):
    """PATCH /users/me/settings 요청 - JSONB 부분 업데이트"""
    push_enabled: Optional[bool] = None
    marketing_agree: Optional[bool] = None
