"""인증 관련 스키마"""
from pydantic import BaseModel, Field
from typing import Optional


class SocialLoginRequest(BaseModel):
    """POST /auth/login/{provider} 요청"""
    access_token: str = Field(..., description="OAuth 제공자 액세스 토큰")
    fcm_token: Optional[str] = Field(None, description="FCM 디바이스 토큰 (푸시알림)")


class TokenResponse(BaseModel):
    """토큰 응답 (공통)"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginResponse(TokenResponse):
    """POST /auth/login/{provider} 응답"""
    is_new_user: bool


class WithdrawRequest(BaseModel):
    """POST /auth/withdraw 요청"""
    reason: Optional[str] = Field(None, max_length=500, description="탈퇴 사유")
