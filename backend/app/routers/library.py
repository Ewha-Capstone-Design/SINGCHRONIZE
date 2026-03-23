"""Library & Archive 라우터 - 폴더, 위시리스트, 부른 노래 기록, 차단"""
from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status  # noqa: F401
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.library import Folder, WishlistItem
from app.models.archive import Archive
from app.schemas.library import (
    FolderCreate, FolderResponse,
    WishlistItemCreate, WishlistItemResponse,
)
from app.schemas.archive import ArchiveCreate, ArchiveUpdate, ArchiveResponse

router = APIRouter(prefix="/api/v1/library", tags=["Library"])


# ═══════════════════════════════════════════════════
# Folder endpoints
# ═══════════════════════════════════════════════════

@router.get("/folders", response_model=List[FolderResponse])
async def get_folders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """사용자의 모든 폴더 조회 (아이템 개수 포함)"""
    stmt = (
        select(
            Folder,
            func.count(WishlistItem.id).label("item_count"),
        )
        .outerjoin(WishlistItem, WishlistItem.folder_id == Folder.id)
        .where(Folder.user_id == current_user.id)
        .group_by(Folder.id)
        .order_by(Folder.created_at)
    )
    result = await db.execute(stmt)
    rows = result.all()

    return [
        FolderResponse(
            id=folder.id,
            user_id=folder.user_id,
            name=folder.name,
            is_system=folder.is_system,
            created_at=folder.created_at,
            item_count=item_count,
        )
        for folder, item_count in rows
    ]


@router.post("/folders", response_model=FolderResponse, status_code=status.HTTP_201_CREATED)
async def create_folder(
    body: FolderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """새 폴더 생성"""
    folder = Folder(
        user_id=current_user.id,
        name=body.name,
        is_system=False,
    )
    db.add(folder)
    await db.flush()
    await db.refresh(folder)

    return FolderResponse(
        id=folder.id,
        user_id=folder.user_id,
        name=folder.name,
        is_system=folder.is_system,
        created_at=folder.created_at,
        item_count=0,
    )


@router.delete("/folders/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder(
    folder_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """폴더 삭제 (시스템 폴더는 삭제 불가)"""
    stmt = select(Folder).where(Folder.id == folder_id, Folder.user_id == current_user.id)
    result = await db.execute(stmt)
    folder = result.scalar_one_or_none()

    if not folder:
        raise HTTPException(status_code=404, detail="폴더를 찾을 수 없습니다.")
    if folder.is_system:
        raise HTTPException(status_code=400, detail="시스템 폴더는 삭제할 수 없습니다.")

    await db.delete(folder)


# ═══════════════════════════════════════════════════
# Wishlist endpoints
# ═══════════════════════════════════════════════════

@router.get("/wishlist", response_model=List[WishlistItemResponse])
async def get_wishlist(
    folder_id: Optional[UUID] = Query(None, description="폴더 ID (없으면 전체)"),
    sort: str = Query("LATEST", description="정렬 기준 (LATEST)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """위시리스트 아이템 조회"""
    stmt = (
        select(WishlistItem)
        .options(selectinload(WishlistItem.song))
        .where(WishlistItem.user_id == current_user.id)
    )

    if folder_id is not None:
        stmt = stmt.where(WishlistItem.folder_id == folder_id)

    if sort == "LATEST":
        stmt = stmt.order_by(WishlistItem.created_at.desc())

    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/wishlist", response_model=WishlistItemResponse, status_code=status.HTTP_201_CREATED)
async def add_wishlist_item(
    body: WishlistItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """위시리스트에 곡 추가"""
    # 폴더 존재 확인 (folder_id가 있는 경우)
    if body.folder_id is not None:
        folder_check = await db.execute(
            select(Folder.id).where(Folder.id == body.folder_id, Folder.user_id == current_user.id)
        )
        if not folder_check.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="폴더를 찾을 수 없습니다.")

    # 중복 체크
    dup_stmt = select(WishlistItem).where(
        WishlistItem.user_id == current_user.id,
        WishlistItem.folder_id == body.folder_id,
        WishlistItem.song_id == body.song_id,
    )
    dup_result = await db.execute(dup_stmt)
    if dup_result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="이미 위시리스트에 추가된 곡입니다.")

    item = WishlistItem(
        user_id=current_user.id,
        folder_id=body.folder_id,
        song_id=body.song_id,
    )
    db.add(item)
    await db.flush()

    # song relationship을 로드하기 위해 재조회
    stmt = (
        select(WishlistItem)
        .options(selectinload(WishlistItem.song))
        .where(WishlistItem.id == item.id)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


@router.delete("/wishlist/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wishlist_item(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """위시리스트 아이템 삭제"""
    stmt = select(WishlistItem).where(WishlistItem.id == item_id, WishlistItem.user_id == current_user.id)
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="위시리스트 아이템을 찾을 수 없습니다.")

    await db.delete(item)


# ═══════════════════════════════════════════════════
# Archive / History endpoints
# ═══════════════════════════════════════════════════

@router.get("/history", response_model=List[ArchiveResponse])
async def get_history(
    tag: Optional[str] = Query(None, description="태그 필터 (예: AGAIN, HIGH_PITCH)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """부른 노래 기록 조회"""
    stmt = (
        select(Archive)
        .options(selectinload(Archive.song))
        .where(Archive.user_id == current_user.id)
    )

    if tag is not None:
        stmt = stmt.where(Archive.tags.any(tag))

    stmt = stmt.order_by(Archive.recorded_date.desc())

    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/history", response_model=ArchiveResponse, status_code=status.HTTP_201_CREATED)
async def create_history(
    body: ArchiveCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """부른 노래 기록 저장"""
    archive = Archive(
        user_id=current_user.id,
        song_id=body.song_id,
        tags=body.tags,
        memo=body.memo,
    )
    db.add(archive)
    await db.flush()

    stmt = (
        select(Archive)
        .options(selectinload(Archive.song))
        .where(Archive.id == archive.id)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


@router.patch("/history/{archive_id}", response_model=ArchiveResponse)
async def update_history(
    archive_id: UUID,
    body: ArchiveUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """부른 노래 기록 수정 (태그, 메모)"""
    stmt = select(Archive).where(Archive.id == archive_id, Archive.user_id == current_user.id)
    result = await db.execute(stmt)
    archive = result.scalar_one_or_none()

    if not archive:
        raise HTTPException(status_code=404, detail="기록을 찾을 수 없습니다.")

    if body.tags is not None:
        archive.tags = body.tags
    if body.memo is not None:
        archive.memo = body.memo

    await db.flush()

    stmt = (
        select(Archive)
        .options(selectinload(Archive.song))
        .where(Archive.id == archive.id)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


@router.delete("/history/{archive_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_history(
    archive_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """부른 노래 기록 삭제"""
    stmt = select(Archive).where(Archive.id == archive_id, Archive.user_id == current_user.id)
    result = await db.execute(stmt)
    archive = result.scalar_one_or_none()

    if not archive:
        raise HTTPException(status_code=404, detail="기록을 찾을 수 없습니다.")

    await db.delete(archive)


