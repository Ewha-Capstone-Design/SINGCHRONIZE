"""Busking 관련 모델 — 라이브 세션 전체 생명주기"""
import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class BuskingRoom(Base):
    __tablename__ = "busking_rooms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    host_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    thumbnail = Column(String, nullable=True)          # S3 URL
    status = Column(String, default="PREPARING")       # PREPARING | LIVE | ENDED
    current_song_index = Column(Integer, default=0)
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    total_viewers = Column(Integer, default=0)         # 현재 뷰어 수 (실시간 반영용 legacy)
    peak_viewer_count = Column(Integer, default=0)
    total_unique_viewers = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BuskingSetlistItem(Base):
    __tablename__ = "busking_setlist_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), ForeignKey("busking_rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    song_id = Column(String, nullable=True)            # 내부 UUID 또는 Spotify ID — 유연하게 String
    title = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    album_art_url = Column(String, nullable=True)
    order_index = Column(Integer, nullable=False)      # 0-based

    __table_args__ = (
        UniqueConstraint("room_id", "order_index", name="uq_busking_room_order"),
    )


class BuskingReaction(Base):
    __tablename__ = "busking_reactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(UUID(as_uuid=True), ForeignKey("busking_rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    song_index = Column(Integer, nullable=True)        # 반응 시점의 current_song_index (0-based)
    value = Column(String, nullable=False)             # "match" | "mismatch"
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BuskingChatMessage(Base):
    __tablename__ = "busking_chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(UUID(as_uuid=True), ForeignKey("busking_rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BuskingResult(Base):
    __tablename__ = "busking_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(UUID(as_uuid=True), ForeignKey("busking_rooms.id", ondelete="CASCADE"), nullable=False, unique=True)
    duration_seconds = Column(Integer, nullable=True)
    match_count = Column(Integer, default=0)
    mismatch_count = Column(Integer, default=0)
    chat_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
