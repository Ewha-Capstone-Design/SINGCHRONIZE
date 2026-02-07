"""인증 서비스 - 소셜 로그인, JWT, RTR"""
import uuid
import logging
from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.services.oauth import get_oauth_provider

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ──────────────────────────────────────────────
    # 소셜 로그인
    # ──────────────────────────────────────────────

    async def social_login(
        self,
        provider: str,
        access_token: str,
        fcm_token: str | None = None,
    ) -> tuple[User, str, str, bool]:
        """
        1) OAuth 액세스 토큰으로 제공자 사용자 정보 조회
        2) DB 유저 조회/생성
        3) FCM 토큰 저장 (settings JSONB 머지)
        4) 우리 서비스 JWT 발급

        Returns: (user, access_token, refresh_token, is_new_user)
        """
        # 1. OAuth 제공자에서 사용자 정보 조회
        oauth_provider = get_oauth_provider(provider)
        user_info = await oauth_provider.get_user_info(access_token)

        # 2. 기존 유저 조회
        stmt = select(User).where(
            User.provider == provider,
            User.provider_id == user_info.oauth_id,
        )
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        is_new_user = user is None

        if is_new_user:
            user = User(
                provider=provider,
                provider_id=user_info.oauth_id,
                nickname=user_info.nickname or f"user_{uuid.uuid4().hex[:8]}",
                email=user_info.email,
                profile_img=user_info.profile_image_url,
                settings={"push_enabled": True},
            )
            self.db.add(user)
            await self.db.flush()
            logger.info(f"신규 유저 생성: provider={provider}, id={user.id}")
        else:
            logger.info(f"기존 유저 로그인: provider={provider}, id={user.id}")

        # 3. FCM 토큰 저장
        if fcm_token:
            current_settings = dict(user.settings or {})
            current_settings["fcm_token"] = fcm_token
            user.settings = current_settings

        # 4. JWT 발급
        jwt_access = self._create_access_token(str(user.id))
        jwt_refresh = await self._create_refresh_token(user.id)

        return user, jwt_access, jwt_refresh, is_new_user

    # ──────────────────────────────────────────────
    # RTR (Refresh Token Rotation)
    # ──────────────────────────────────────────────

    async def refresh_tokens(self, refresh_token: str) -> tuple[str, str]:
        """기존 refresh token 폐기 → 새 토큰 쌍 발급"""
        stmt = select(RefreshToken).where(RefreshToken.token == refresh_token)
        result = await self.db.execute(stmt)
        record = result.scalar_one_or_none()

        if not record:
            raise ValueError("유효하지 않은 리프레시 토큰입니다.")
        if record.revoked:
            raise ValueError("이미 사용된 리프레시 토큰입니다.")
        if record.expires_at < datetime.now(timezone.utc):
            raise ValueError("만료된 리프레시 토큰입니다.")

        # 기존 토큰 폐기
        record.revoked = True

        # 새 토큰 발급
        new_access = self._create_access_token(str(record.user_id))
        new_refresh = await self._create_refresh_token(record.user_id)

        return new_access, new_refresh

    # ──────────────────────────────────────────────
    # 회원 탈퇴
    # ──────────────────────────────────────────────

    async def withdraw(self, user_id: uuid.UUID, reason: str | None = None) -> None:
        """유저 삭제 (CASCADE → refresh_tokens 함께 삭제)"""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("사용자를 찾을 수 없습니다.")

        if reason:
            logger.info(f"회원 탈퇴: user_id={user_id}, reason={reason}")

        await self.db.delete(user)

    # ──────────────────────────────────────────────
    # JWT 유틸
    # ──────────────────────────────────────────────

    def _create_access_token(self, user_id: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        payload = {"sub": user_id, "exp": expire, "type": "access"}
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    async def _create_refresh_token(self, user_id: uuid.UUID) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        payload = {"sub": str(user_id), "exp": expire, "type": "refresh"}
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

        record = RefreshToken(user_id=user_id, token=token, expires_at=expire)
        self.db.add(record)
        await self.db.flush()

        return token

    @staticmethod
    def verify_access_token(token: str) -> str:
        """액세스 토큰 검증 → user_id(str) 반환"""
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            if payload.get("type") != "access":
                raise ValueError("액세스 토큰이 아닙니다.")
            user_id = payload.get("sub")
            if not user_id:
                raise ValueError("토큰에 사용자 정보가 없습니다.")
            return user_id
        except JWTError:
            raise ValueError("유효하지 않은 토큰입니다.")
