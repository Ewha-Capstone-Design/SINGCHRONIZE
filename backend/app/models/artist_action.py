"""ArtistUserAction 모델 — 아티스트 선호/차단"""
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Uuid, UniqueConstraint
from sqlalchemy.sql import func

from app.database import Base


class ArtistUserAction(Base):
    __tablename__ = "artist_user_actions"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    artist_name = Column(String(200), nullable=False)
    action = Column(String(10), nullable=False)   # 'PREFER' | 'BLOCK'

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "artist_name", name="uq_user_artist_action"),
    )
