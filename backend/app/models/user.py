"""User 모델 - PostgreSQL JSONB 활용"""
import uuid
from sqlalchemy import Column, String, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nickname = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    profile_img = Column(String, nullable=True)

    # Auth
    provider = Column(String, nullable=False)       # kakao, naver
    provider_id = Column(String, nullable=False)

    # JSONB - 보컬 분석 캐시 (마이페이지 성능)
    # 예: {"range": "C3~A5", "radar_chart": {"timbre": 80, "pitch": 90, ...}}
    vocal_summary_cache = Column(JSONB, nullable=True)

    # JSONB - 설정 통합 (별도 테이블 불필요)
    # 예: {"push_enabled": true, "marketing_agree": false}
    settings = Column(JSONB, default=lambda: {"push_enabled": True})

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    refresh_tokens = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("provider", "provider_id", name="uq_provider_provider_id"),
    )
