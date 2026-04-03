"""아티스트 선호/차단 라우터"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.artist_action import ArtistUserAction
from app.schemas.artist_action import (
    ArtistActionRequest,
    ArtistActionResponse,
    ArtistActionsListResponse,
)

router = APIRouter(prefix="/api/v1/artist-actions", tags=["Artist Actions"])


@router.post("", response_model=ArtistActionResponse, status_code=status.HTTP_201_CREATED)
async def set_artist_action(
    body: ArtistActionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    아티스트 PREFER / BLOCK 설정.
    동일 아티스트에 이미 액션이 있으면 덮어씁니다 (upsert).
    """
    result = await db.execute(
        select(ArtistUserAction).where(
            ArtistUserAction.user_id == current_user.id,
            ArtistUserAction.artist_name == body.artist_name,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.action = body.action
        action = existing
    else:
        action = ArtistUserAction(
            user_id=current_user.id,
            artist_name=body.artist_name,
            action=body.action,
        )
        db.add(action)

    await db.commit()
    await db.refresh(action)
    return ArtistActionResponse.model_validate(action)


@router.get("", response_model=ArtistActionsListResponse)
async def get_artist_actions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """현재 유저의 아티스트 액션 목록 조회."""
    result = await db.execute(
        select(ArtistUserAction)
        .where(ArtistUserAction.user_id == current_user.id)
        .order_by(ArtistUserAction.created_at.desc())
    )
    actions = result.scalars().all()
    return ArtistActionsListResponse(
        actions=[ArtistActionResponse.model_validate(a) for a in actions]
    )


@router.delete("/{artist_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_artist_action(
    artist_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """아티스트 액션(선호/차단) 취소."""
    result = await db.execute(
        select(ArtistUserAction).where(
            ArtistUserAction.user_id == current_user.id,
            ArtistUserAction.artist_name == artist_name,
        )
    )
    action = result.scalar_one_or_none()
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ACTION_NOT_FOUND", "message": "해당 아티스트 액션을 찾을 수 없습니다."},
        )
    await db.delete(action)
    await db.commit()
