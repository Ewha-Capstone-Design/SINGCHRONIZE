"""보컬 분석 스키마"""
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime


class UploadUrlResponse(BaseModel):
    upload_url: str
    s3_key: str


class AnalysisJobCreate(BaseModel):
    s3_key: str
    recording_id: Optional[UUID] = None


class AnalysisJobResponse(BaseModel):
    job_id: UUID
    status: str
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VocalProfileResponse(BaseModel):
    user_id: UUID
    has_profile: bool
    updated_at: Optional[datetime] = None

    # 음역대 요약 (음역대 분석 카드 우측 3종)
    observed_lowest_note: Optional[str] = None   # 최저음
    observed_highest_note: Optional[str] = None  # 최고음
    avg_note: Optional[str] = None               # 평균음

    # 레이더 차트 (보컬 특성 카드)
    # [{label: "음정 안정성", value: 70}, ...]
    traits: Optional[List[Dict[str, Any]]] = None

    # 장르 적합도 카드
    # data: [{genre: "락/메탈", score: 77}, ...]  /  bestGenre: "락/메탈"
    genreFit: Optional[Dict[str, Any]] = None

    # 음색 분석 카드 — 밝기·따뜻함·두께감 3개만
    # [{label: "밝기", value: 65}, ...]
    timbre: Optional[List[Dict[str, Any]]] = None

    # 음역대 그래프
    # data: [{note: "C#2", score: 0}, ...]  /  comfort: {from: "G4", to: "C#5"}
    range: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}
