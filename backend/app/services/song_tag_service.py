"""SongTagService - 상황 라벨 배치 처리 오케스트레이터"""
import asyncio
import logging
from dataclasses import dataclass, field
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.song import Song
from app.repositories.song_repository import SongRepository
from app.utils.openai_client import SituationClassifier

logger = logging.getLogger(__name__)


@dataclass
class BatchResult:
    success: int = 0
    failed: int = 0
    errors: List[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.success + self.failed


class SongTagService:
    def __init__(self, classifier: SituationClassifier, db: AsyncSession):
        self._classifier = classifier
        self._repo = SongRepository(db)
        self._db = db

    async def process_batch(self, songs: List[Song], sleep_ms: int = 200) -> BatchResult:
        """주어진 곡 목록에 대해 상황 라벨 분류 후 DB 저장.

        각 곡의 실패는 개별 catch로 처리 → 한 곡 실패가 배치 전체에 영향 없음.
        성공한 곡들은 배치 끝에 일괄 commit.
        """
        result = BatchResult()

        for song in songs:
            try:
                classification = await self._classifier.classify(
                    title=song.title,
                    artist=song.artist,
                    genre=song.genre,
                )
                await self._repo.merge_tags(song, {
                    "situationLabel": classification["label"],
                    "situationReason": classification["reason"],
                })
                result.success += 1
                logger.info("[OK] %s - %s → %s", song.artist, song.title, classification["label"])
            except Exception as e:
                result.failed += 1
                msg = f"[FAIL] {song.artist} - {song.title}: {e}"
                result.errors.append(msg)
                logger.warning(msg)

            if sleep_ms > 0:
                await asyncio.sleep(sleep_ms / 1000)

        if result.success > 0:
            try:
                await self._db.commit()
            except Exception as e:
                logger.error("DB commit 실패, 롤백: %s", e)
                await self._db.rollback()
                result.failed += result.success
                result.success = 0
                result.errors.append(f"DB commit 실패: {e}")

        return result

    async def run_all(self, batch_size: int = 20, sleep_ms: int = 200, limit: int = 0) -> BatchResult:
        """전체 미태깅 곡을 배치로 순회 처리.

        Args:
            batch_size: 한 번에 처리할 곡 수
            sleep_ms:   OpenAI 호출 사이 대기 ms
            limit:      최대 처리 곡 수 (0 = 전체)
        """
        accumulated = BatchResult()
        processed = 0

        total_untagged = await self._repo.count_untagged()
        target = min(total_untagged, limit) if limit else total_untagged
        logger.info("처리 대상: %d곡 / 전체 미태깅: %d곡 (batch=%d)", target, total_untagged, batch_size)

        while True:
            fetch_size = min(batch_size, target - processed) if limit else batch_size

            # 항상 offset=0: commit 후 해당 곡이 untagged 집합에서 제거되므로
            songs = await self._repo.get_untagged_batch(fetch_size, offset=0)
            if not songs:
                logger.info("처리할 곡이 없습니다. 완료.")
                break

            remaining = await self._repo.count_untagged()
            logger.info("▶ 배치 처리 | 남은 미태깅: %d곡 | 이번 배치: %d곡", remaining, len(songs))

            try:
                batch_result = await self.process_batch(songs, sleep_ms=sleep_ms)
            except Exception as e:
                logger.error("배치 처리 중 복구 불가 오류: %s", e)
                break

            accumulated.success += batch_result.success
            accumulated.failed += batch_result.failed
            accumulated.errors.extend(batch_result.errors)
            processed += batch_result.total

            logger.info("✓ 누적 성공: %d  실패: %d", accumulated.success, accumulated.failed)

            if limit and processed >= target:
                break

        return accumulated
