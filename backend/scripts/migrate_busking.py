"""
busking 관련 DB 마이그레이션 스크립트

기존 busking_rooms 테이블에 신규 컬럼을 추가하고,
신규 테이블(busking_setlist_items, busking_reactions,
busking_chat_messages, busking_results)을 생성합니다.

실행:
    cd backend
    python scripts/migrate_busking.py
"""
import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ── busking_rooms 신규 컬럼 ────────────────────────────────────
ALTER_BUSKING_ROOMS = [
    "ALTER TABLE busking_rooms ADD COLUMN IF NOT EXISTS current_song_index INTEGER DEFAULT 0",
    "ALTER TABLE busking_rooms ADD COLUMN IF NOT EXISTS peak_viewer_count INTEGER DEFAULT 0",
    "ALTER TABLE busking_rooms ADD COLUMN IF NOT EXISTS total_unique_viewers INTEGER DEFAULT 0",
]

# ── 신규 테이블 ────────────────────────────────────────────────
CREATE_SETLIST = """
CREATE TABLE IF NOT EXISTS busking_setlist_items (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id       UUID NOT NULL REFERENCES busking_rooms(id) ON DELETE CASCADE,
    song_id       TEXT,
    title         TEXT NOT NULL,
    artist        TEXT NOT NULL,
    album_art_url TEXT,
    order_index   INTEGER NOT NULL,
    CONSTRAINT uq_busking_room_order UNIQUE (room_id, order_index)
);
CREATE INDEX IF NOT EXISTS ix_busking_setlist_room_id ON busking_setlist_items(room_id);
"""

CREATE_REACTIONS = """
CREATE TABLE IF NOT EXISTS busking_reactions (
    id         SERIAL PRIMARY KEY,
    room_id    UUID NOT NULL REFERENCES busking_rooms(id) ON DELETE CASCADE,
    user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    value      TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_busking_reactions_room_id ON busking_reactions(room_id);
"""

CREATE_CHAT = """
CREATE TABLE IF NOT EXISTS busking_chat_messages (
    id         SERIAL PRIMARY KEY,
    room_id    UUID NOT NULL REFERENCES busking_rooms(id) ON DELETE CASCADE,
    user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message    TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_busking_chat_room_id ON busking_chat_messages(room_id);
"""

CREATE_RESULTS = """
CREATE TABLE IF NOT EXISTS busking_results (
    id               SERIAL PRIMARY KEY,
    room_id          UUID NOT NULL UNIQUE REFERENCES busking_rooms(id) ON DELETE CASCADE,
    duration_seconds INTEGER,
    match_count      INTEGER DEFAULT 0,
    mismatch_count   INTEGER DEFAULT 0,
    chat_count       INTEGER DEFAULT 0,
    created_at       TIMESTAMPTZ DEFAULT now()
);
"""


async def run():
    async with engine.begin() as conn:
        logger.info("busking_rooms 컬럼 추가 중...")
        for stmt in ALTER_BUSKING_ROOMS:
            await conn.execute(text(stmt))
            logger.info("  OK: %s", stmt[:60])

        logger.info("신규 테이블 생성 중...")
        for name, ddl in [
            ("busking_setlist_items", CREATE_SETLIST),
            ("busking_reactions", CREATE_REACTIONS),
            ("busking_chat_messages", CREATE_CHAT),
            ("busking_results", CREATE_RESULTS),
        ]:
            await conn.execute(text(ddl))
            logger.info("  OK: %s", name)

    logger.info("마이그레이션 완료")


if __name__ == "__main__":
    asyncio.run(run())
