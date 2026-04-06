"""보컬 분석 스키마"""
from pydantic import BaseModel
from typing import Any, Dict, List, Optional, Text
from uuid import UUID
from datetime import datetime


class UploadUrlResponse(BaseModel):
    upload_url: str
    s3_key: str


class AnalysisJobCreate(BaseModel):
    s3_key: str                          # SQS에 전달할 S3 오브젝트 키
    recording_id: Optional[UUID] = None  # 선택적 recording 참조


class AnalysisJobResponse(BaseModel):
    job_id: UUID
    status: str
    result_data: Optional[Dict[str, Any]] = None
    # FAILED 시 에러 원인 (result_data["error"] 에서 추출)
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VocalProfileResponse(BaseModel):
    user_id: UUID
    latest_analysis_job_id: Optional[UUID] = None
    latest_recording_id: Optional[UUID] = None
    has_profile: bool

    # 음역대 요약
    observed_lowest_note: Optional[str] = None
    observed_highest_note: Optional[str] = None
    stable_lowest_note: Optional[str] = None
    stable_highest_note: Optional[str] = None

    # 레이더 차트
    radar_median_avg: Optional[float] = None
    radar_median_pitch_stability: Optional[float] = None
    radar_median_rhythm_stability: Optional[float] = None
    radar_median_high_note_stability: Optional[float] = None
    radar_median_dynamic_control: Optional[float] = None
    radar_median_vocal_clarity: Optional[float] = None

    latest_timbre_summary: Optional[str] = None
    latest_best_genre: Optional[str] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
