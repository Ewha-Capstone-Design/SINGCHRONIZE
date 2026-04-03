"""Library & Archive 라우터 - 폴더, 위시리스트, 부른 노래 기록"""
from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

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
# Folder
# ═══════════════════════════════════════════════════

@router.get("/folders", response_model=List[FolderResponse])
async def get_folders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(
        select(Folder, func.count(WishlistItem.id).label("item_count"))
        .outerjoin(WishlistItem, WishlistItem.folder_id == Folder.id)
        .where(Folder.user_id == current_user.id)
        .group_by(Folder.id)
        .order_by(Folder.created_at)
    )).all()
    return [
        FolderResponse(
            id=f.id, user_id=f.user_id, name=f.name,
            is_system=f.is_system, created_at=f.created_at, item_count=cnt,
        )
        for f, cnt in rows
    ]


@router.post("/folders", response_model=FolderResponse, status_code=status.HTTP_201_CREATED)
async def create_folder(
    body: FolderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    folder = Folder(user_id=current_user.id, name=body.name, is_system=False)
    db.add(folder)
    await db.flush()
    await db.refresh(folder)
    return FolderResponse(
        id=folder.id, user_id=folder.user_id, name=folder.name,
        is_system=folder.is_system, created_at=folder.created_at, item_count=0,
    )


@router.delete("/folders/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder(
    folder_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    folder = (await db.execute(
        select(Folder).where(Folder.id == folder_id, Folder.user_id == current_user.id)
    )).scalar_one_or_none()
    if not folder:
        raise HTTPException(status_code=404, detail="폴더를 찾을 수 없습니다.")
    if folder.is_system:
        raise HTTPException(status_code=400, detail="시스템 폴더는 삭제할 수 없습니다.")
    await db.delete(folder)


# ═══════════════════════════════════════════════════
# Wishlist
# ═══════════════════════════════════════════════════

@router.get("/wishlist", response_model=List[WishlistItemResponse])
async def get_wishlist(
    folder_id: Optional[UUID] = Query(None),
    sort: str = Query("LATEST"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(WishlistItem).where(WishlistItem.user_id == current_user.id)
    if folder_id is not None:
        stmt = stmt.where(WishlistItem.folder_id == folder_id)
    if sort == "LATEST":
        stmt = stmt.order_by(WishlistItem.created_at.desc())
    return (await db.execute(stmt)).scalars().all()


@router.post("/wishlist", response_model=WishlistItemResponse, status_code=status.HTTP_201_CREATED)
async def add_wishlist_item(
    body: WishlistItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Spotify 검색 결과를 찜 목록에 추가. song_data = { name, artist, album_image, uri }"""
    if body.folder_id is not None:
        if not (await db.execute(
            select(Folder.id).where(Folder.id == body.folder_id, Folder.user_id == current_user.id)
        )).scalar_one_or_none():
            raise HTTPException(status_code=404, detail="폴더를 찾을 수 없습니다.")

    item = WishlistItem(
        user_id=current_user.id,
        folder_id=body.folder_id,
        song_data=body.song_data,
    )
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


@router.delete("/wishlist/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wishlist_item(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = (await db.execute(
        select(WishlistItem).where(WishlistItem.id == item_id, WishlistItem.user_id == current_user.id)
    )).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="찜 아이템을 찾을 수 없습니다.")
    await db.delete(item)


# ═══════════════════════════════════════════════════
# Archive / History
# ═══════════════════════════════════════════════════

@router.get("/history", response_model=List[ArchiveResponse])
async def get_history(
    tag: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Archive).where(Archive.user_id == current_user.id)
    if tag is not None:
        stmt = stmt.where(Archive.tags.any(tag))
    stmt = stmt.order_by(Archive.recorded_date.desc())
    return (await db.execute(stmt)).scalars().all()


@router.post("/history", response_model=ArchiveResponse, status_code=status.HTTP_201_CREATED)
async def create_history(
    body: ArchiveCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Spotify 검색 결과를 가창 기록에 저장. song_data = { name, artist, album_image, uri }"""
    archive = Archive(
        user_id=current_user.id,
        song_data=body.song_data,
        tags=body.tags,
        memo=body.memo,
    )
    db.add(archive)
    await db.flush()
    await db.refresh(archive)
    return archive


@router.patch("/history/{archive_id}", response_model=ArchiveResponse)
async def update_history(
    archive_id: UUID,
    body: ArchiveUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    archive = (await db.execute(
        select(Archive).where(Archive.id == archive_id, Archive.user_id == current_user.id)
    )).scalar_one_or_none()
    if not archive:
        raise HTTPException(status_code=404, detail="기록을 찾을 수 없습니다.")
    if body.tags is not None:
        archive.tags = body.tags
    if body.memo is not None:
        archive.memo = body.memo
    await db.flush()
    await db.refresh(archive)
    return archive


@router.delete("/history/{archive_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_history(
    archive_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    archive = (await db.execute(
        select(Archive).where(Archive.id == archive_id, Archive.user_id == current_user.id)
    )).scalar_one_or_none()
    if not archive:
        raise HTTPException(status_code=404, detail="기록을 찾을 수 없습니다.")
    await db.delete(archive)
