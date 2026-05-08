"""녹음 버스킹 모델"""
import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Uuid, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.database import Base


class RecordedBusking(Base):
    __tablename__ = "recorded_buskings"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    host_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    thumbnail = Column(String(500), nullable=True)
    recording_url = Column(String(500), nullable=False)
    s3_key = Column(String(500), nullable=False)
    song_data = Column(JSONB, nullable=False)  # { name, artist, album_image, uri }
    vote_ends_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RecordedBuskingComment(Base):
    __tablename__ = "recorded_busking_comments"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    busking_id = Column(Uuid, ForeignKey("recorded_buskings.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RecordedBuskingReaction(Base):
    __tablename__ = "recorded_busking_reactions"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    busking_id = Column(Uuid, ForeignKey("recorded_buskings.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    value = Column(String(10), nullable=False)  # 'match' | 'mismatch'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("busking_id", "user_id", name="uq_rec_busking_reaction_user"),)
