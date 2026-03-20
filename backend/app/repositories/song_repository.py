"""Song 레포지토리 - 상황 태깅용 DB 접근 레이어"""
import logging
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.song import Song

logger = logging.getLogger(__name__)


class SongRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_untagged_batch(self, batch_size: int, offset: int) -> List[Song]:
        """situationLabel이 없는 곡을 batch_size 단위로 조회.

        tags가 NULL이거나 tags JSONB 내에 'situationLabel' 키가 없는 경우 포함.
        """
        stmt = (
            select(Song)
            .where(Song.tags["situationLabel"].is_(None))
            .order_by(Song.created_at)
            .limit(batch_size)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_untagged(self) -> int:
        """태깅 대상 곡 전체 수 반환 (진행률 표시용)"""
        from sqlalchemy import func
        stmt = select(func.count()).select_from(Song).where(
            Song.tags["situationLabel"].is_(None)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def merge_tags(self, song: Song, new_tags: dict) -> None:
        """기존 tags JSONB에 new_tags를 merge 저장 (기존 키 보존).

        SQLAlchemy JSON 변경 감지를 위해 새 dict 객체로 교체.
        """
        current = dict(song.tags or {})
        current.update(new_tags)
        song.tags = current
        await self.db.flush()
        logger.debug("[%s] tags 저장 완료: %s", song.id, new_tags)
