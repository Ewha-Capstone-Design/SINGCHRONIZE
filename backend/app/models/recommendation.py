import uuid 
from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID  
from app.database import Base

class Recommendation(Base):
    __tablename__ = "recommendation_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    
    # 1차 추천 시 사용할 목소리 파일 경로
    voice_url = Column(String, nullable=True) 
    status = Column(String, default="QUEUED")
    # AI가 분석 후 채워넣어줄 결과 (리스트 형태)
    recommended_songs = Column(JSON, nullable=True)
    
    # 2차 추천 시 유저의 피드백/취향 저장
    input_preferences = Column(JSON, nullable=True)
    
    # 작업 상태 관리 (상태 컬럼이 없었다면 추가하는 게 관리하기 편해요!)
    status = Column(String, default="QUEUED") # QUEUED, ANALYZING, DONE, FAILED
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # (선택) 유저와의 관계 설정
    # user = relationship("User", back_populates="recommendations")