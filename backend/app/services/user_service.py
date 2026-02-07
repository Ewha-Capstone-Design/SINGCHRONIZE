"""유저 서비스 - 프로필 조회/수정, 설정 JSONB 머지"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user(self, user_id: uuid.UUID) -> User:
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다.")
        return user

    async def update_profile(
        self,
        user_id: uuid.UUID,
        nickname: str | None = None,
    ) -> User:
        user = await self.get_user(user_id)
        if nickname is not None:
            user.nickname = nickname
        await self.db.flush()
        return user

    async def update_settings(
        self,
        user_id: uuid.UUID,
        update_data: dict,
    ) -> dict:
        """
        JSONB 부분 업데이트: 전달된 키만 머지.
        새 dict 객체를 할당해 SQLAlchemy 변경 감지를 트리거.
        """
        user = await self.get_user(user_id)
        current = dict(user.settings or {})
        current.update(update_data)
        user.settings = current
        await self.db.flush()
        return user.settings
