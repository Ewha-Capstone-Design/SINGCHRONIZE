"""Song 모델 - Supabase songs 테이블 매핑"""
import uuid
from sqlalchemy import Column, String, DateTime, Integer, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.database import Base


class Song(Base):
    __tablename__ = "songs"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False, index=True)
    artist = Column(String, nullable=False, index=True)
    tags = Column(JSONB, nullable=True)
    features = Column(String, nullable=True)
    album_cover = Column(String, nullable=True)
    genre = Column(String, nullable=True)
    youtube_url = Column(String, nullable=True)
    raw_s3_key = Column(String, nullable=True)
    download_status = Column(String, nullable=True)
    embedding_status = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
