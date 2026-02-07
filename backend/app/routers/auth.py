"""인증 라우터"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import (
    SocialLoginRequest,
    LoginResponse,
    TokenResponse,
    WithdrawRequest,
)
from app.services.auth_service import AuthService
from app.services.oauth.kakao import KakaoOAuthError
from app.services.oauth.naver import NaverOAuthError

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])
logger = logging.getLogger(__name__)
bearer_scheme = HTTPBearer()


# ─────────────────────────────────────
# POST /api/v1/auth/login/{provider}
# ─────────────────────────────────────
@router.post(
    "/login/{provider}",
    response_model=LoginResponse,
    summary="소셜 로그인 (카카오 / 네이버)",
    description="프론트엔드가 발급받은 OAuth 액세스 토큰을 전달하면, "
    "사용자 정보를 조회하고 우리 서비스 JWT를 발급합니다.",
)
async def social_login(
    provider: str,
    body: SocialLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    if provider not in ("kakao", "naver"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"지원하지 않는 provider: {provider}",
        )

    try:
        auth = AuthService(db)
        user, access_token, refresh_token, is_new = await auth.social_login(
            provider=provider,
            access_token=body.access_token,
            fcm_token=body.fcm_token,
        )

        logger.info(f"로그인 성공: provider={provider}, user={user.id}, new={is_new}")

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            is_new_user=is_new,
        )

    except (KakaoOAuthError, NaverOAuthError) as e:
        logger.error(f"OAuth 에러: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ─────────────────────────────────────
# POST /api/v1/auth/refresh
# ─────────────────────────────────────
@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="토큰 갱신 (RTR)",
    description="Authorization 헤더에 리프레시 토큰을 담아 보내면, "
    "기존 토큰을 폐기하고 새 토큰 쌍을 발급합니다.",
)
async def refresh(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    try:
        auth = AuthService(db)
        new_access, new_refresh = await auth.refresh_tokens(credentials.credentials)
        return TokenResponse(access_token=new_access, refresh_token=new_refresh)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


# ─────────────────────────────────────
# POST /api/v1/auth/withdraw
# ─────────────────────────────────────
@router.post(
    "/withdraw",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="회원 탈퇴",
    description="현재 로그인된 사용자를 탈퇴 처리합니다.",
)
async def withdraw(
    body: WithdrawRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    auth = AuthService(db)
    await auth.withdraw(current_user.id, reason=body.reason)
    logger.info(f"회원 탈퇴: user={current_user.id}")
