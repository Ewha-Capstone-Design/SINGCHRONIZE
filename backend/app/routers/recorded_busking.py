"""녹음 버스킹 라우터"""
import uuid as uuid_lib
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies.auth import get_current_user, get_optional_user
from app.models.recorded_busking import RecordedBusking, RecordedBuskingComment, RecordedBuskingReaction
from app.models.user import User
from app.schemas.recorded_busking import (
    CommentCreate, CommentResponse,
    HostProfile, ReactionRequest,
    RecordedBuskingCreate, RecordedBuskingPreview, RecordedBuskingResponse,
    RecordingUploadUrlResponse, VoteRemaining,
)
from app.utils.aws import generate_presigned_url

router = APIRouter(prefix="/api/v1/busking/recordings", tags=["RecordedBusking"])


# ── 유틸 ──────────────────────────────────────────────────────

def _vote_remaining(vote_ends_at: datetime) -> VoteRemaining:
    now = datetime.now(timezone.utc)
    if vote_ends_at.tzinfo is None:
        vote_ends_at = vote_ends_at.replace(tzinfo=timezone.utc)
    delta = vote_ends_at - now
    if delta.total_seconds() <= 0:
        return VoteRemaining(days=0, hours=0, minutes=0, is_ended=True)
    total = int(delta.total_seconds())
    return VoteRemaining(
        days=total // 86400,
        hours=(total % 86400) // 3600,
        minutes=(total % 3600) // 60,
        is_ended=False,
    )


async def _fetch_counts(db: AsyncSession, busking_ids: list):
    """busking_ids 전체의 match/mismatch/comment 수를 한 번에 집계."""
    reaction_rows = (await db.execute(
        select(
            RecordedBuskingReaction.busking_id,
            RecordedBuskingReaction.value,
            func.count().label("cnt"),
        )
        .where(RecordedBuskingReaction.busking_id.in_(busking_ids))
        .group_by(RecordedBuskingReaction.busking_id, RecordedBuskingReaction.value)
    )).all()

    match_map: dict = {}
    mismatch_map: dict = {}
    for row in reaction_rows:
        if row.value == "match":
            match_map[row.busking_id] = row.cnt
        else:
            mismatch_map[row.busking_id] = row.cnt

    comment_rows = (await db.execute(
        select(RecordedBuskingComment.busking_id, func.count().label("cnt"))
        .where(RecordedBuskingComment.busking_id.in_(busking_ids))
        .group_by(RecordedBuskingComment.busking_id)
    )).all()
    comment_map = {r.busking_id: r.cnt for r in comment_rows}

    return match_map, mismatch_map, comment_map


# ── 1. 녹음 파일 presigned URL 발급 ───────────────────────────

@router.post("/upload-url", response_model=RecordingUploadUrlResponse)
async def get_recording_upload_url(
    current_user: User = Depends(get_current_user),
):
    s3_key = f"busking/recordings/{current_user.id}/{uuid_lib.uuid4()}.m4a"
    upload_url = generate_presigned_url(s3_key, content_type="audio/m4a")
    if not upload_url:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "S3_URL_FAILED", "message": "업로드 URL 생성에 실패했습니다."},
        )
    public_url = f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
    return RecordingUploadUrlResponse(upload_url=upload_url, s3_key=s3_key, public_url=public_url)


# ── 2. 녹음 버스킹 생성 ───────────────────────────────────────

@router.post("", response_model=RecordedBuskingResponse, status_code=status.HTTP_201_CREATED)
async def create_recorded_busking(
    body: RecordedBuskingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    public_url = f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{body.s3_key}"
    item = RecordedBusking(
        host_id=current_user.id,
        title=body.title,
        thumbnail=body.thumbnail_url,
        recording_url=public_url,
        s3_key=body.s3_key,
        song_data=body.song_data,
        vote_ends_at=body.vote_ends_at,
    )
    db.add(item)
    await db.flush()
    await db.refresh(item)

    return RecordedBuskingResponse(
        id=item.id,
        host_profile=HostProfile(id=current_user.id, nickname=current_user.nickname, profile_img=current_user.profile_img),
        title=item.title,
        thumbnail=item.thumbnail,
        recording_url=item.recording_url,
        song_data=item.song_data,
        vote_ends_at=item.vote_ends_at,
        vote_remaining=_vote_remaining(item.vote_ends_at),
        match_count=0,
        mismatch_count=0,
        comment_count=0,
        my_reaction=None,
        created_at=item.created_at,
    )


# ── 3. 목록 조회 ──────────────────────────────────────────────

@router.get("", response_model=List[RecordedBuskingResponse])
async def list_recorded_buskings(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    items = (await db.execute(
        select(RecordedBusking)
        .order_by(RecordedBusking.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )).scalars().all()

    if not items:
        return []

    busking_ids = [i.id for i in items]

    hosts = {
        u.id: u for u in (await db.execute(
            select(User).where(User.id.in_([i.host_id for i in items]))
        )).scalars().all()
    }

    match_map, mismatch_map, comment_map = await _fetch_counts(db, busking_ids)

    my_reaction_map: dict = {}
    if current_user:
        rows = (await db.execute(
            select(RecordedBuskingReaction.busking_id, RecordedBuskingReaction.value)
            .where(
                RecordedBuskingReaction.busking_id.in_(busking_ids),
                RecordedBuskingReaction.user_id == current_user.id,
            )
        )).all()
        my_reaction_map = {r.busking_id: r.value for r in rows}

    result = []
    for item in items:
        host = hosts.get(item.host_id)
        if not host:
            continue
        result.append(RecordedBuskingResponse(
            id=item.id,
            host_profile=HostProfile(id=host.id, nickname=host.nickname, profile_img=host.profile_img),
            title=item.title,
            thumbnail=item.thumbnail,
            recording_url=item.recording_url,
            song_data=item.song_data,
            vote_ends_at=item.vote_ends_at,
            vote_remaining=_vote_remaining(item.vote_ends_at),
            match_count=match_map.get(item.id, 0),
            mismatch_count=mismatch_map.get(item.id, 0),
            comment_count=comment_map.get(item.id, 0),
            my_reaction=my_reaction_map.get(item.id),
            created_at=item.created_at,
        ))
    return result


# ── 4. 단건 조회 ──────────────────────────────────────────────

@router.get("/{busking_id}", response_model=RecordedBuskingResponse)
async def get_recorded_busking(
    busking_id: UUID,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    item = (await db.execute(
        select(RecordedBusking).where(RecordedBusking.id == busking_id)
    )).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "녹음 버스킹을 찾을 수 없습니다."})

    host = (await db.execute(select(User).where(User.id == item.host_id))).scalar_one_or_none()
    if not host:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "호스트 정보를 찾을 수 없습니다."})

    match_map, mismatch_map, comment_map = await _fetch_counts(db, [busking_id])

    my_reaction = None
    if current_user:
        my_reaction = (await db.execute(
            select(RecordedBuskingReaction.value).where(
                RecordedBuskingReaction.busking_id == busking_id,
                RecordedBuskingReaction.user_id == current_user.id,
            )
        )).scalar_one_or_none()

    return RecordedBuskingResponse(
        id=item.id,
        host_profile=HostProfile(id=host.id, nickname=host.nickname, profile_img=host.profile_img),
        title=item.title,
        thumbnail=item.thumbnail,
        recording_url=item.recording_url,
        song_data=item.song_data,
        vote_ends_at=item.vote_ends_at,
        vote_remaining=_vote_remaining(item.vote_ends_at),
        match_count=match_map.get(busking_id, 0),
        mismatch_count=mismatch_map.get(busking_id, 0),
        comment_count=comment_map.get(busking_id, 0),
        my_reaction=my_reaction,
        created_at=item.created_at,
    )


# ── 5. 투표 (어울려요 / 안어울려요) ──────────────────────────

@router.post("/{busking_id}/reactions", status_code=status.HTTP_204_NO_CONTENT)
async def react(
    busking_id: UUID,
    body: ReactionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.value not in ("match", "mismatch"):
        raise HTTPException(status_code=400, detail={"code": "INVALID_VALUE", "message": "value는 match 또는 mismatch여야 합니다."})

    item = (await db.execute(
        select(RecordedBusking.vote_ends_at).where(RecordedBusking.id == busking_id)
    )).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "녹음 버스킹을 찾을 수 없습니다."})
    if _vote_remaining(item).is_ended:
        raise HTTPException(status_code=400, detail={"code": "VOTE_ENDED", "message": "투표가 종료되었습니다."})

    existing = (await db.execute(
        select(RecordedBuskingReaction).where(
            RecordedBuskingReaction.busking_id == busking_id,
            RecordedBuskingReaction.user_id == current_user.id,
        )
    )).scalar_one_or_none()

    if existing:
        existing.value = body.value
    else:
        db.add(RecordedBuskingReaction(busking_id=busking_id, user_id=current_user.id, value=body.value))


@router.delete("/{busking_id}/reactions", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reaction(
    busking_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    reaction = (await db.execute(
        select(RecordedBuskingReaction).where(
            RecordedBuskingReaction.busking_id == busking_id,
            RecordedBuskingReaction.user_id == current_user.id,
        )
    )).scalar_one_or_none()
    if reaction:
        await db.delete(reaction)


# ── 6. 댓글 ──────────────────────────────────────────────────

@router.get("/{busking_id}/comments", response_model=List[CommentResponse])
async def get_comments(
    busking_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(
        select(RecordedBuskingComment, User)
        .join(User, User.id == RecordedBuskingComment.user_id)
        .where(RecordedBuskingComment.busking_id == busking_id)
        .order_by(RecordedBuskingComment.created_at.asc())
    )).all()
    return [
        CommentResponse(
            id=c.id,
            user_id=c.user_id,
            nickname=u.nickname,
            profile_img=u.profile_img,
            content=c.content,
            created_at=c.created_at,
        )
        for c, u in rows
    ]


@router.post("/{busking_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
    busking_id: UUID,
    body: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not (await db.execute(
        select(RecordedBusking.id).where(RecordedBusking.id == busking_id)
    )).scalar_one_or_none():
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "녹음 버스킹을 찾을 수 없습니다."})

    comment = RecordedBuskingComment(busking_id=busking_id, user_id=current_user.id, content=body.content)
    db.add(comment)
    await db.flush()
    await db.refresh(comment)
    return CommentResponse(
        id=comment.id,
        user_id=comment.user_id,
        nickname=current_user.nickname,
        profile_img=current_user.profile_img,
        content=comment.content,
        created_at=comment.created_at,
    )


@router.delete("/{busking_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    busking_id: UUID,
    comment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    comment = (await db.execute(
        select(RecordedBuskingComment).where(
            RecordedBuskingComment.id == comment_id,
            RecordedBuskingComment.busking_id == busking_id,
            RecordedBuskingComment.user_id == current_user.id,
        )
    )).scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "댓글을 찾을 수 없습니다."})
    await db.delete(comment)
