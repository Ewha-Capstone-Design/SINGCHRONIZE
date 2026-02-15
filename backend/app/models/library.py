"""Library 모델 - Folder & WishlistItem"""
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Uuid, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Folder(Base):
    __tablename__ = "folders"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    items = relationship("WishlistItem", back_populates="folder", cascade="all, delete-orphan")


class WishlistItem(Base):
    __tablename__ = "wishlist_items"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    folder_id = Column(Uuid, ForeignKey("folders.id", ondelete="SET NULL"), nullable=True, index=True)
    song_id = Column(Uuid, ForeignKey("songs.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    folder = relationship("Folder", back_populates="items")
    song = relationship("Song")

    __table_args__ = (
        UniqueConstraint("folder_id", "song_id", name="uq_folder_song"),
    )
