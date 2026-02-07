"""User 모델 - JSONB 활용 (PostgreSQL), JSON 폴백 (SQLite)"""
import uuid
from sqlalchemy import Column, String, DateTime, JSON, Uuid, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    nickname = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    profile_img = Column(String, nullable=True)

    # Auth
    provider = Column(String, nullable=False)       # kakao, naver
    provider_id = Column(String, nullable=False)

    # JSON - 보컬 분석 캐시 (마이페이지 성능)
<<<<<<< HEAD
=======
    # PostgreSQL에서는 JSONB 인덱싱 활용 가능, SQLite에서는 TEXT 저장
>>>>>>> 37619415d32128e6eb47e75d2ff2f2a1d689c018
    vocal_summary_cache = Column(JSON, nullable=True)

    # JSON - 설정 통합
    settings = Column(JSON, default=lambda: {"push_enabled": True})

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    refresh_tokens = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("provider", "provider_id", name="uq_provider_provider_id"),
    )
