import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class BuskingRoom(Base):
    __tablename__ = "busking_rooms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    host_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    thumbnail = Column(String, nullable=True)
    status = Column(String, default="PREPARING") # PREPARING, LIVE, ENDED
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    total_viewers = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 관계 설정 (셋리스트)
    # setlist = relationship("BuskingSetlistItem", back_populates="room")