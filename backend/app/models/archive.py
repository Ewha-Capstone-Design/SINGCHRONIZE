"""Archive 모델 - 부른 노래 기록"""
import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Uuid
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.sql import func

from app.database import Base


class Archive(Base):
    __tablename__ = "archives"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # Spotify 검색 결과 JSON 그대로 저장 { name, artist, album_image, uri }
    song_data = Column(JSONB, nullable=False)
    tags = Column(ARRAY(String), default=list)
    memo = Column(Text, nullable=True)
    recorded_date = Column(DateTime(timezone=True), server_default=func.now())
