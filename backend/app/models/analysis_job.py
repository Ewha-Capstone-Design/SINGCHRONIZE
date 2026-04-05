"""AnalysisJob 모델 — 보컬 분석 작업"""
import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Uuid
from sqlalchemy.dialects.postgresql import JSONB, ENUM
from sqlalchemy.sql import func

from app.database import Base


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    recording_id = Column(Uuid, nullable=True)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    s3_key = Column(String(500), nullable=True)

    # status: DB USER-DEFINED enum — QUEUED|UPLOADING|ANALYZING|FINDING_SONGS|DONE|FAILED
    status = Column(ENUM('QUEUED', 'UPLOADING', 'ANALYZING', 'FINDING_SONGS', 'DONE', 'FAILED',
                         name='vocal_analysis_status', create_type=False), nullable=False)

    # 워커가 채워넣는 분석 결과 { version, result, scoring_song_aligned }
    result_data = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
