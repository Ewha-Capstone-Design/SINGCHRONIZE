"""Library & Archive 라우터 - 폴더, 위시리스트, 부른 노래 기록"""
from collections import defaultdict
from datetime import date
from uuid import UUID
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.library import Folder, WishlistItem
from app.models.archive import Archive
from app.models.recommendation import Recommendation
from app.models.song import Song as SongModel
from app.schemas.library import (
    FolderCreate, FolderUpdate, FolderResponse,
    WishlistItemCreate, WishlistItemResponse,
)
from app.schemas.archive import ArchiveCreate, ArchiveUpdate, ArchiveResponse, RecordingUploadUrlResponse
from app.utils.aws import generate_presigned_url
from app.config import settings

router = APIRouter(prefix="/api/v1/library", tags=["Library"])


# ═══════════════════════════════════════════════════
# Folder
# ═══════════════════════════════════════════════════

@router.get("/folders", response_model=List[FolderResponse])
async def get_folders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 폴더 목록 + item_count
    folder_rows = (await db.execute(
        select(Folder, func.count(WishlistItem.id).label("item_count"))
        .outerjoin(WishlistItem, WishlistItem.folder_id == Folder.id)
        .where(Folder.user_id == current_user.id)
        .group_by(Folder.id)
        .order_by(Folder.created_at)
    )).all()

    # 폴더별 썸네일: 최신 순 최대 4개 album_image (ROW_NUMBER 윈도우 단일 쿼리)
    wi_ranked = (
        select(
            WishlistItem.folder_id,
            WishlistItem.song_data["album_image"].astext.label("album_image"),
            func.row_number().over(
                partition_by=WishlistItem.folder_id,
                order_by=WishlistItem.created_at.desc(),
            ).label("rn"),
        )
        .where(
            WishlistItem.user_id == current_user.id,
            WishlistItem.folder_id.isnot(None),
        )
        .subquery()
    )
    thumb_rows = (await db.execute(
        select(wi_ranked.c.folder_id, wi_ranked.c.album_image)
        .where(wi_ranked.c.rn <= 4)
        .order_by(wi_ranked.c.folder_id, wi_ranked.c.rn)
    )).all()

    thumbnails_by_folder: dict[str, list[str]] = defaultdict(list)
    for row in thumb_rows:
        if row.album_image:
            thumbnails_by_folder[str(row.folder_id)].append(row.album_image)

    return [
        FolderResponse(
            id=f.id, user_id=f.user_id, name=f.name,
            is_system=f.is_system, created_at=f.created_at,
            item_count=cnt,
            thumbnails=thumbnails_by_folder.get(str(f.id), []),
        )
        for f, cnt in folder_rows
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


@router.patch("/folders/{folder_id}", response_model=FolderResponse)
async def rename_folder(
    folder_id: UUID,
    body: FolderUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    folder = (await db.execute(
        select(Folder).where(Folder.id == folder_id, Folder.user_id == current_user.id)
    )).scalar_one_or_none()
    if not folder:
        raise HTTPException(status_code=404, detail="폴더를 찾을 수 없습니다.")
    if folder.is_system:
        raise HTTPException(status_code=400, detail="시스템 폴더는 이름을 변경할 수 없습니다.")
    folder.name = body.name.strip()
    await db.commit()
    await db.refresh(folder)
    cnt = (await db.execute(
        select(func.count(WishlistItem.id)).where(WishlistItem.folder_id == folder.id)
    )).scalar_one()
    return FolderResponse(
        id=folder.id, user_id=folder.user_id, name=folder.name,
        is_system=folder.is_system, created_at=folder.created_at, item_count=cnt,
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

@router.get("/wishlist/uris", response_model=List[str])
async def get_wishlist_uris(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """찜 목록에 있는 Spotify URI 목록 반환"""
    rows = (await db.execute(
        select(WishlistItem.song_data).where(WishlistItem.user_id == current_user.id)
    )).scalars().all()
    return [r.get("uri") for r in rows if isinstance(r, dict) and r.get("uri")]


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
    archives = (await db.execute(stmt)).scalars().all()

    liked_rows = (await db.execute(
        select(WishlistItem.song_data).where(WishlistItem.user_id == current_user.id)
    )).scalars().all()
    liked_uris = {r.get("uri") for r in liked_rows if isinstance(r, dict) and r.get("uri")}

    return [
        ArchiveResponse.model_validate(a).model_copy(update={"is_liked": a.song_data.get("uri") in liked_uris})
        for a in archives
    ]


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


# ──────────────────────────────────────────────────────────────
# GET /api/v1/library/history/recommendations — 추천 아카이브
# ──────────────────────────────────────────────────────────────

class ArchiveSong(BaseModel):
    song_id: str
    title: str
    artist: str
    album_cover: Optional[str] = None
    score: Optional[float] = None

class ArchiveRecItem(BaseModel):
    rec_id: str
    date: str                          # "2026.04.06"
    selected_genre: Optional[List[str]] = None
    selected_keyword: Optional[List[str]] = None
    songs: List[ArchiveSong]

class ArchiveDateGroup(BaseModel):
    date: str                          # "2026.04.06"
    items: List[ArchiveRecItem]

class RecommendationArchiveResponse(BaseModel):
    groups: List[ArchiveDateGroup]     # 날짜별 그룹, 최신순
    total: int


def _extract_songs(rec: Recommendation, genre: Optional[str], keyword: Optional[str]) -> List[ArchiveSong]:
    """recommended_songs JSONB에서 필터 조건에 맞는 곡 목록 추출"""
    data: Dict[str, Any] = rec.recommended_songs or {}
    genre_recs: Dict = data.get("genre_recommendations", {})
    situation_recs: Dict = data.get("situation_recommendations", {})

    raw: List[Dict] = []

    if keyword and keyword in situation_recs:
        raw = situation_recs[keyword]
    elif genre:
        raw = genre_recs.get(genre, [])
    else:
        # 기본: 전체
        raw = genre_recs.get("전체", [])
        if not raw and genre_recs:
            raw = next(iter(genre_recs.values()), [])

    return [
        ArchiveSong(
            song_id=s.get("song_id", ""),
            title=s.get("title", ""),
            artist=s.get("artist", ""),
            album_cover=s.get("album_cover"),
            score=s.get("score"),
        )
        for s in raw if s.get("song_id")
    ]


@router.get("/history/recommendations", response_model=RecommendationArchiveResponse)
async def get_recommendation_archive(
    genre: Optional[str] = Query(None, description="장르 필터 (발라드, POP, DANCE 등)"),
    keyword: Optional[str] = Query(None, description="상황 필터 (회식하며 즐길 때 등)"),
    date_str: Optional[str] = Query(None, alias="date", description="날짜 필터 YYYY-MM-DD"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Recommendation)
        .where(
            Recommendation.user_id == current_user.id,
            Recommendation.status == "DONE",
            Recommendation.recommended_songs.isnot(None),
        )
        .order_by(Recommendation.created_at.desc())
    )

    # 날짜 필터: 해당 날짜 하루치만
    if date_str:
        try:
            target = date.fromisoformat(date_str)
        except ValueError:
            raise HTTPException(status_code=400, detail={"code": "INVALID_DATE", "message": "날짜 형식은 YYYY-MM-DD 입니다."})
        stmt = stmt.where(
            func.date(Recommendation.created_at) == target
        )

    result = await db.execute(stmt)
    recs: List[Recommendation] = result.scalars().all()

    # 1차 추출 — rec별 곡 목록
    grouped: Dict[str, List[ArchiveRecItem]] = defaultdict(list)
    rec_song_map: Dict[str, List[ArchiveSong]] = {}  # rec_id → songs
    for rec in recs:
        songs = _extract_songs(rec, genre, keyword)
        if not songs:
            continue
        rec_song_map[str(rec.id)] = songs

    # 2차: title/artist 비어있는 song_id 일괄 조회 (songs 테이블 fallback)
    missing_ids = {
        UUID(s.song_id)
        for songs in rec_song_map.values()
        for s in songs
        if not s.title and s.song_id
    }
    song_db_map: Dict[str, Any] = {}
    if missing_ids:
        rows = (await db.execute(
            select(SongModel).where(SongModel.id.in_(list(missing_ids)))
        )).scalars().all()
        song_db_map = {str(r.id): r for r in rows}

    # 빈 필드 보완 후 그룹핑
    for rec in recs:
        rec_id = str(rec.id)
        if rec_id not in rec_song_map:
            continue
        songs = rec_song_map[rec_id]
        filled = []
        for s in songs:
            if not s.title and s.song_id in song_db_map:
                db_song = song_db_map[s.song_id]
                s = ArchiveSong(
                    song_id=s.song_id,
                    title=db_song.title or "",
                    artist=db_song.artist or "",
                    album_cover=db_song.album_cover or s.album_cover,
                    score=s.score,
                )
            filled.append(s)
        dt_str = rec.created_at.strftime("%Y.%m.%d")
        grouped[dt_str].append(
            ArchiveRecItem(
                rec_id=rec_id,
                date=dt_str,
                selected_genre=rec.selected_genre if isinstance(rec.selected_genre, list) else None,
                selected_keyword=rec.selected_keyword if isinstance(rec.selected_keyword, list) else None,
                songs=filled,
            )
        )

    # 날짜 내림차순 정렬 후 페이지네이션
    sorted_dates = sorted(grouped.keys(), reverse=True)
    total = len(sorted_dates)
    paged_dates = sorted_dates[(page - 1) * size: page * size]

    return RecommendationArchiveResponse(
        groups=[ArchiveDateGroup(date=d, items=grouped[d]) for d in paged_dates],
        total=total,
    )
