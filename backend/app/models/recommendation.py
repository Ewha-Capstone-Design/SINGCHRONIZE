"""Recommendation 모델 — 추천 파이프라인 로그"""
import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.database import Base


class Recommendation(Base):
    __tablename__ = "recommendation_logs"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    base_report_id = Column(Uuid, nullable=True)   # analysis_jobs 참조 (선택)

    # QUEUED | RUNNING_STAGE1 | WAITING_FEEDBACK | RUNNING_STAGE2 | DONE | FAILED
    status = Column(String(30), nullable=True)

    # 워커가 채우는 추천 결과 (DB 컬럼명과 일치)
    first_recommended_songs = Column(JSONB, nullable=True)   # 1차 상위 3곡
    recommended_songs = Column(JSONB, nullable=True)         # 2차 장르별 최대 4곡

    # 2차 추천 피드백
    input_preferences = Column(JSONB, nullable=True)         # { reranking_top3: [song_id, ...] }
    selected_genre = Column(JSONB, nullable=True)            # DB 타입이 JSONB
    selected_keyword = Column(JSONB, nullable=True)          # DB 타입이 JSONB

    # deprecated — DB에 존재하므로 유지
    voice_url = Column(String, nullable=True)

    # 실패 정보
    error_message = Column(Text, nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)

    # 단계별 타임스탬프
    stage1_started_at = Column(DateTime(timezone=True), nullable=True)
    stage1_completed_at = Column(DateTime(timezone=True), nullable=True)
    stage2_started_at = Column(DateTime(timezone=True), nullable=True)
    stage2_completed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
