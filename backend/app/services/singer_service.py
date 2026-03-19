"""Singer 서비스 레이어 - 랜덤 가수 조회 및 가수 차단 비즈니스 로직"""
from uuid import UUID
from typing import List

from fastapi import HTTPException, status
from sqlalchemy import select, func, text, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.singer import Singer, BlockedSinger, FavoriteSinger


VALID_GENDERS = {"male", "female"}


class SingerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ─── 랜덤 가수 조회 ───────────────────────────────

    async def get_random_singers(self, user_id: UUID, gender: str, limit: int) -> List[Singer]:
        """성별 필터 + 차단 제외 + 랜덤 추출"""
        if gender not in VALID_GENDERS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_GENDER", "message": "gender는 male 또는 female이어야 합니다."},
            )

        # 차단된 singer_id 서브쿼리 (NOT IN엔 scalar_subquery 대신 일반 select 사용)
        blocked_subq = (
            select(BlockedSinger.singer_id)
            .where(BlockedSinger.user_id == user_id)
        )

        stmt = (
            select(Singer)
            .where(
                Singer.gender == gender,
                Singer.singer_id.not_in(blocked_subq),
            )
            .order_by(func.random())
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        return result.scalars().all()

    # ─── 가수 검색 ───────────────────────────────────

    async def search_singers(self, query: str, limit: int) -> List[Singer]:
        """이름 또는 별칭으로 가수 검색 (부분 일치)"""
        q = f"%{query}%"
        stmt = (
            select(Singer)
            .where(or_(Singer.name.ilike(q), Singer.aliases.ilike(q)))
            .order_by(Singer.name)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    # ─── 즐겨찾는 가수 선택 (온보딩 2단계) ──────────────

    async def select_favorite_singers(
        self, user_id: UUID, singer_ids: List[int]
    ) -> List[Singer]:
        """기존 즐겨찾기를 전부 교체 후 새로 저장 (onboarding step2 / 마이페이지 수정 공용)"""
        # 요청된 singer_id가 실제로 존재하는지 한 번에 검증
        exists_result = await self.db.execute(
            select(Singer.singer_id).where(Singer.singer_id.in_(singer_ids))
        )
        found_ids = set(exists_result.scalars().all())
        missing = set(singer_ids) - found_ids
        if missing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "SINGER_NOT_FOUND", "message": f"존재하지 않는 가수 ID: {sorted(missing)}"},
            )

        # 기존 즐겨찾기 전체 삭제 후 재삽입 (교체 방식)
        await self.db.execute(
            delete(FavoriteSinger).where(FavoriteSinger.user_id == user_id)
        )
        self.db.add_all([
            FavoriteSinger(user_id=user_id, singer_id=sid) for sid in singer_ids
        ])
        await self.db.flush()

        # 저장된 Singer 정보 반환
        result = await self.db.execute(
            select(Singer).where(Singer.singer_id.in_(singer_ids)).order_by(Singer.name)
        )
        return result.scalars().all()

    # ─── 가수 차단 등록 ───────────────────────────────

    async def block_singer(self, user_id: UUID, singer_id: int) -> BlockedSinger:
        """가수 차단 - 이미 차단된 경우 409"""
        # 가수 존재 확인
        singer_result = await self.db.execute(
            select(Singer).where(Singer.singer_id == singer_id)
        )
        if not singer_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "SINGER_NOT_FOUND", "message": "존재하지 않는 가수입니다."},
            )

        # 중복 차단 확인
        dup_result = await self.db.execute(
            select(BlockedSinger).where(
                BlockedSinger.user_id == user_id,
                BlockedSinger.singer_id == singer_id,
            )
        )
        if dup_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "ALREADY_BLOCKED", "message": "이미 차단된 가수입니다."},
            )

        blocked = BlockedSinger(user_id=user_id, singer_id=singer_id)
        self.db.add(blocked)
        await self.db.flush()
        await self.db.refresh(blocked)
        return blocked

    # ─── 차단 가수 목록 조회 ──────────────────────────

    async def get_blocked_singers(self, user_id: UUID) -> List[BlockedSinger]:
        """현재 유저의 차단 가수 목록 (Singer 정보 eager load)"""
        stmt = (
            select(BlockedSinger)
            .options(selectinload(BlockedSinger.singer))
            .where(BlockedSinger.user_id == user_id)
            .order_by(BlockedSinger.block_id)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    # ─── 차단 해제 ────────────────────────────────────

    async def unblock_singer(self, user_id: UUID, block_id: int) -> None:
        """차단 해제 - 본인 차단 건만 삭제 가능"""
        result = await self.db.execute(
            select(BlockedSinger).where(BlockedSinger.block_id == block_id)
        )
        blocked = result.scalar_one_or_none()

        if not blocked:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BLOCK_NOT_FOUND", "message": "차단 기록을 찾을 수 없습니다."},
            )

        if blocked.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "본인의 차단 기록만 삭제할 수 있습니다."},
            )

        await self.db.delete(blocked)
