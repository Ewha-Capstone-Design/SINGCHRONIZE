"""추천 파이프라인 스키마"""
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID
from datetime import datetime


class RecommendationCreate(BaseModel):
    """
    기본 (1차 DB 프로필 기반): job_id + user_id만 SQS에 전송.
    s3_key는 FIRST_REC_FORCE_PIPELINE 환경변수가 있는 AI 워커 폴백용.
    base_report_id는 연관된 analysis_jobs.id.
    """
    s3_key: Optional[str] = None
    base_report_id: Optional[UUID] = None


class RecommendationStatusResponse(BaseModel):
    job_id: UUID
    status: Optional[str] = None
    first_recommended_songs: Optional[List[Dict[str, Any]]] = None
    recommended_songs: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RecommendationFeedback(BaseModel):
    """
    유저가 1차 추천 중 선택한 곡 ID 목록 (최대 3개).
    워커가 recommendation_logs.input_preferences.reranking_top3 를 읽어 2차 추천에 활용.
    """
    reranking_top3: List[str]
    selected_genre: Optional[Any] = None    # JSONB — 문자열 또는 객체
    selected_keyword: Optional[Any] = None  # JSONB — 문자열 또는 객체


class Stage3SimilarPicksRequest(BaseModel):
    period: Literal["today", "week", "month"] = "week"
    limit: int = Field(default=10, ge=1, le=100)
    interaction_since: Optional[datetime] = None
    interaction_until: Optional[datetime] = None


class Stage3PickItem(BaseModel):
    song_id: str
    score: float


class Stage3SimilarPicksResponse(BaseModel):
    """source: stage3 성공 / fallback_stage2 는 최근 DONE job 의 2차 결과 / unconfigured 는 URL 미설정."""

    source: Literal["stage3", "fallback_stage2", "unconfigured"]
    results: List[Stage3PickItem]
    detail: Optional[str] = None
