"""Singer & BlockedSinger & BlockedSong & FavoriteSinger 모델"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Uuid, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Singer(Base):
    __tablename__ = "singers"

    singer_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    gender = Column(String(10), nullable=False)   # "male" | "female" | "unknown"
    aliases = Column(String, nullable=True)
    photo_url = Column(String(500), nullable=True)
    vocal_type = Column(String(50), nullable=True)
    vocal_vector = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    blocked_by = relationship("BlockedSinger", back_populates="singer", cascade="all, delete-orphan")
    favorited_by = relationship("FavoriteSinger", back_populates="singer", cascade="all, delete-orphan")


class BlockedSinger(Base):
    __tablename__ = "blocked_singers"

    block_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    singer_id = Column(Integer, ForeignKey("singers.singer_id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    singer = relationship("Singer", back_populates="blocked_by")

    __table_args__ = (
        UniqueConstraint("user_id", "singer_id", name="uq_user_singer_block"),
    )


class BlockedSong(Base):
    __tablename__ = "blocked_songs"

    block_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    song_id = Column(Uuid, ForeignKey("songs.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "song_id", name="uq_user_song_block"),
    )


class FavoriteSinger(Base):
    __tablename__ = "favorite_singers"

    favorite_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    singer_id = Column(Integer, ForeignKey("singers.singer_id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    singer = relationship("Singer", back_populates="favorited_by")

    __table_args__ = (
        UniqueConstraint("user_id", "singer_id", name="uq_user_singer_favorite"),
    )
