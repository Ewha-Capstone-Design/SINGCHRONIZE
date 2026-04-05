"""추천 파이프라인 라우터 — Job 생성 / 상태 조회 / 2차 피드백"""
import json
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.recommendation import Recommendation
from app.schemas.recommendation import (
    RecommendationCreate,
    RecommendationFeedback,
    RecommendationStatusResponse,
)
from app.utils.aws import send_sqs_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/recommendations", tags=["Recommendations"])


@router.post("", response_model=RecommendationStatusResponse, status_code=status.HTTP_201_CREATED)
async def create_recommendation(
    body: RecommendationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    추천 Job 생성 + SQS 전송.
    기본 경로: s3_key 없이 전송 → 워커가 user_vocal_profiles에서 프로필 로드.
    폴백: s3_key 포함 → 워커의 FIRST_REC_FORCE_PIPELINE 로직.
    """
    job = Recommendation(
        user_id=current_user.id,
        status="QUEUED",
        base_report_id=body.base_report_id,
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)

    payload: dict = {"job_id": str(job.id), "user_id": str(current_user.id)}
    if body.s3_key:
        payload["s3_key"] = body.s3_key

    msg_id = send_sqs_message(json.dumps(payload))
    if not msg_id:
        logger.error("Recommendation SQS 전송 실패 — job_id=%s", job.id)

    await db.commit()
    await db.refresh(job)
    return _to_response(job)


@router.get("/{job_id}", response_model=RecommendationStatusResponse)
async def get_recommendation(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """추천 Job 상태 및 결과 조회. 프론트엔드 폴링용."""
    job = await _get_job_or_404(job_id, current_user.id, db)
    return _to_response(job)


@router.post("/{job_id}/feedback", response_model=RecommendationStatusResponse)
async def submit_feedback(
    job_id: UUID,
    body: RecommendationFeedback,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    2차 추천 피드백 저장.
    워커가 WAITING_FEEDBACK 상태에서 input_preferences.reranking_top3를 읽어 2차 추천 수행.
    """
    job = await _get_job_or_404(job_id, current_user.id, db)

    if job.status != "WAITING_FEEDBACK":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "INVALID_STATUS",
                "message": f"피드백은 WAITING_FEEDBACK 상태일 때만 가능합니다. 현재: {job.status}",
            },
        )

    job.input_preferences = {"reranking_top3": body.reranking_top3}
    if body.selected_genre is not None:
        job.selected_genre = body.selected_genre
    if body.selected_keyword is not None:
        job.selected_keyword = body.selected_keyword

    await db.commit()
    await db.refresh(job)
    return _to_response(job)


@router.get("/{job_id}/songs", response_model=RecommendationStatusResponse)
async def get_recommendation_songs(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """2차 추천 완료 결과(recommended_songs) 조회."""
    job = await _get_job_or_404(job_id, current_user.id, db)

    if job.status != "DONE":
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail={"code": "NOT_READY", "message": f"추천이 아직 완료되지 않았습니다. 현재: {job.status}"},
        )

    return _to_response(job)


# ── 헬퍼 ─────────────────────────────────────────────────

async def _get_job_or_404(job_id: UUID, user_id, db: AsyncSession) -> Recommendation:
    result = await db.execute(
        select(Recommendation).where(
            Recommendation.id == job_id,
            Recommendation.user_id == user_id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "JOB_NOT_FOUND", "message": "추천 작업을 찾을 수 없습니다."},
        )
    return job


def _to_response(job: Recommendation) -> RecommendationStatusResponse:
    return RecommendationStatusResponse(
        job_id=job.id,
        status=job.status,
        first_recommended_songs=job.first_recommended_songs,
        recommended_songs=job.recommended_songs,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )
