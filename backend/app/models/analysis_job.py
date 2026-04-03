"""AnalysisJob 모델 — 보컬 분석 작업"""
import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.database import Base


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    recording_id = Column(Uuid, nullable=True)  # DB는 NOT NULL이나 백엔드 생성 시 선택적
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # status: DB USER-DEFINED enum — QUEUED|UPLOADING|ANALYZING|FINDING_SONGS|DONE|FAILED
    status = Column(String(30), nullable=False)

    # 워커가 채워넣는 분석 결과 { version, result, scoring_song_aligned }
    result_data = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
