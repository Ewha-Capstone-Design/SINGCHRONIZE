#!/usr/bin/env python
"""songs 테이블의 곡을 8개 상황 라벨로 분류하여 tags JSONB에 저장하는 배치 스크립트.

사용법:
    cd backend
    python scripts/tag_songs.py [옵션]

옵션:
    --batch-size    한 번에 처리할 곡 수 (기본: 20)
    --sleep-ms      OpenAI 호출 사이 대기 시간 ms (기본: 200)
    --limit         최대 처리 곡 수, 0=전체 (기본: 0)
    --model         OpenAI 모델명 (기본: gpt-4o-mini)
    --dry-run       DB 저장 없이 분류 결과만 출력 (최대 3곡 샘플)

환경 변수:
    OPENAI_API_KEY  (필수, .env 또는 환경 변수)
    DATABASE_URL    (필수, .env)
"""
import argparse
import asyncio
import logging
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="노래 상황 라벨 분류 배치")
    parser.add_argument("--batch-size", type=int, default=20, help="배치 크기 (기본: 20)")
    parser.add_argument("--sleep-ms", type=int, default=200, help="OpenAI 호출 간격 ms (기본: 200)")
    parser.add_argument("--limit", type=int, default=0, help="최대 처리 수, 0=전체 (기본: 0)")
    parser.add_argument("--model", type=str, default="gpt-4o-mini", help="OpenAI 모델 (기본: gpt-4o-mini)")
    parser.add_argument("--dry-run", action="store_true", help="DB 저장 없이 최대 3곡 결과만 출력")
    return parser.parse_args()


async def main(args: argparse.Namespace) -> None:
    from app.config import settings
    from app.database import AsyncSessionLocal
    from app.services.song_tag_service import SongTagService
    from app.utils.openai_client import SituationClassifier

    if not settings.OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY가 설정되지 않았습니다. .env를 확인하세요.")
        sys.exit(1)

    classifier = SituationClassifier(api_key=settings.OPENAI_API_KEY, model=args.model)

    if args.dry_run:
        await _dry_run(classifier)
        return

    async with AsyncSessionLocal() as db:
        service = SongTagService(classifier=classifier, db=db)
        logger.info(
            "시작 | model=%s  batch=%d  sleep=%dms  limit=%s",
            args.model, args.batch_size, args.sleep_ms,
            args.limit if args.limit else "전체",
        )
        result = await service.run_all(
            batch_size=args.batch_size,
            sleep_ms=args.sleep_ms,
            limit=args.limit,
        )

    logger.info("=" * 50)
    logger.info("완료 | 성공: %d  실패: %d", result.success, result.failed)
    if result.errors:
        logger.warning("실패 목록:")
        for err in result.errors:
            logger.warning("  %s", err)


async def _dry_run(classifier: "SituationClassifier") -> None:
    """DB 없이 미태깅 3곡 샘플로 OpenAI 응답만 확인"""
    from app.database import AsyncSessionLocal
    from app.repositories.song_repository import SongRepository

    logger.info("[DRY-RUN] DB 저장 없이 최대 3곡 분류 결과만 출력")
    async with AsyncSessionLocal() as db:
        repo = SongRepository(db)
        songs = await repo.get_untagged_batch(batch_size=3, offset=0)

    if not songs:
        logger.info("처리할 곡이 없습니다 (모두 이미 태깅됨).")
        return

    for song in songs:
        try:
            result = await classifier.classify(song.title, song.artist, song.genre)
            logger.info(
                "[DRY-RUN] %s - %s\n  → label : %s\n  → reason: %s",
                song.artist, song.title, result["label"], result["reason"],
            )
        except Exception as e:
            logger.warning("[DRY-RUN] 실패: %s - %s: %s", song.artist, song.title, e)


if __name__ == "__main__":
    asyncio.run(main(parse_args()))
