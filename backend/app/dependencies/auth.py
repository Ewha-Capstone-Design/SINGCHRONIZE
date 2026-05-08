"""인증 의존성"""
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.user_service import UserService

bearer_scheme = HTTPBearer()
bearer_scheme_optional = HTTPBearer(auto_error=False)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme_optional),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Authorization 헤더가 없거나 토큰이 유효하지 않으면 None 반환"""
    if not credentials:
        return None
    try:
        user_id = AuthService.verify_access_token(credentials.credentials)
        user_service = UserService(db)
        return await user_service.get_user(UUID(user_id))
    except Exception:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Authorization 헤더에서 액세스 토큰 검증 → User 반환"""
    try:
        user_id = AuthService.verify_access_token(credentials.credentials)
        user_service = UserService(db)
        return await user_service.get_user(UUID(user_id))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
