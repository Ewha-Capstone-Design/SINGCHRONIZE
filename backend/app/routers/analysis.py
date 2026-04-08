"""보컬 분석 라우터 — 업로드 URL 발급 / Job 생성 / 상태 조회"""
import json
import uuid
import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.analysis_job import AnalysisJob
from app.models.user_vocal_profile import UserVocalProfile
from app.schemas.analysis import (
    AnalysisJobCreate,
    AnalysisJobResponse,
    UploadUrlResponse,
    VocalProfileResponse,
)
from app.utils.aws import generate_presigned_url, send_vocal_sqs_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analysis", tags=["Analysis"])


@router.post("/upload-url", response_model=UploadUrlResponse)
async def get_upload_url(
    current_user: User = Depends(get_current_user),
):
    """
    S3 presigned PUT URL 발급.
    프론트엔드는 이 URL로 직접 오디오 파일을 업로드하고,
    반환된 s3_key로 POST /jobs를 호출한다.
    """
    s3_key = f"recordings/{current_user.id}/{uuid.uuid4()}.m4a"
    url = generate_presigned_url(s3_key, content_type="audio/m4a")
    if not url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "S3_URL_FAILED", "message": "업로드 URL 생성에 실패했습니다."},
        )
    return UploadUrlResponse(upload_url=url, s3_key=s3_key)


@router.post("/jobs", response_model=AnalysisJobResponse, status_code=status.HTTP_201_CREATED)
async def create_analysis_job(
    body: AnalysisJobCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    보컬 분석 Job 생성 + SQS 전송.
    1. analysis_jobs 테이블에 레코드 생성 (QUEUED)
    2. Vocal Analysis SQS에 { job_id, s3_key } 전송
    """
    job = AnalysisJob(
        user_id=current_user.id,
        s3_key=body.s3_key,
        recording_id=body.recording_id,
        status="QUEUED",
    )
    db.add(job)
    await db.flush()   # id 확보
    await db.refresh(job)

    # SQS 전송 — 실패 시 FAILED 처리 (프론트에서 폴링으로 확인 가능)
    message = json.dumps({"job_id": str(job.id), "s3_key": body.s3_key})
    msg_id = send_vocal_sqs_message(message)
    if not msg_id:
        logger.error("Vocal SQS 전송 실패 — job_id=%s", job.id)
        job.status = "FAILED"
        job.result_data = {
            "error": "SQS 전송 실패: 분석 작업을 큐에 등록하지 못했습니다. 잠시 후 다시 시도해 주세요.",
            "failed_at": datetime.now(timezone.utc).isoformat(),
        }

    await db.commit()
    await db.refresh(job)
    return _to_job_response(job)


@router.get("/jobs/{job_id}", response_model=AnalysisJobResponse)
async def get_analysis_job(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """분석 Job 상태 및 결과 조회. 프론트엔드 폴링용."""
    result = await db.execute(
        select(AnalysisJob).where(
            AnalysisJob.id == job_id,
            AnalysisJob.user_id == current_user.id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "JOB_NOT_FOUND", "message": "분석 작업을 찾을 수 없습니다."},
        )
    return _to_job_response(job)


@router.get("/profile", response_model=VocalProfileResponse)
async def get_vocal_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """보컬 프로필 조회 — UI 렌더링에 필요한 필드만 반환."""
    profile_row = await db.execute(
        select(UserVocalProfile).where(UserVocalProfile.user_id == current_user.id)
    )
    profile = profile_row.scalar_one_or_none()

    if not profile:
        return VocalProfileResponse(user_id=current_user.id, has_profile=False)

    # analysis_jobs.result_data 에서 UI 필드만 추출
    _TIMBRE_LABELS = {"밝기", "따뜻함", "두께감"}
    avg_note: str | None = None
    traits = None
    genre_fit = None
    timbre = None
    range_info = None

    if profile.latest_analysis_job_id:
        job_row = await db.execute(
            select(AnalysisJob).where(AnalysisJob.id == profile.latest_analysis_job_id)
        )
        job = job_row.scalar_one_or_none()
        if job and isinstance(job.result_data, dict):
            rd = job.result_data

            # 평균음
            avg_note = (rd.get("range") or {}).get("stats", {}).get("avg")

            # 레이더 차트
            traits = rd.get("traits")

            # 장르 적합도
            genre_fit = rd.get("genreFit")

            # 음색 — 밝기·따뜻함·두께감만
            raw_timbre = rd.get("timbre") or []
            timbre = [t for t in raw_timbre if t.get("label") in _TIMBRE_LABELS]

            # 음역대 그래프
            raw_range = rd.get("range") or {}
            range_info = {
                "data": raw_range.get("data"),
                "comfort": raw_range.get("comfort"),
            }

    return VocalProfileResponse(
        user_id=current_user.id,
        has_profile=True,
        updated_at=profile.updated_at,
        observed_lowest_note=profile.observed_lowest_note,
        observed_highest_note=profile.observed_highest_note,
        avg_note=avg_note,
        traits=traits,
        genreFit=genre_fit,
        timbre=timbre,
        range=range_info,
    )


# ── 헬퍼 ──────────────────────────────────────────────────────

def _to_job_response(job: AnalysisJob) -> AnalysisJobResponse:
    error_msg = job.result_data.get("error") if job.result_data else None
    return AnalysisJobResponse(
        job_id=job.id,
        status=job.status,
        result_data=job.result_data,
        error_message=error_msg,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )
