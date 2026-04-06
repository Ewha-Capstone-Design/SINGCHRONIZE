"""유저 라우터"""
import time
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.busking import BuskingRoom, BuskingSetlistItem, BuskingResult
from app.models.user import User
from app.schemas.singer import (
    BlockSingerRequest, BlockedSingerItem, BlockedSingersListResponse,
    BlockSongRequest, BlockedSongItem, BlockedSongsListResponse,
    SingerInfo,
)
from app.schemas.user import UserMeResponse, UserResponse, UserUpdateRequest, SettingsUpdateRequest
from app.services.user_service import UserService
from app.utils.aws import upload_image_to_s3

_ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
_MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB
_MAX_NICKNAME_LEN = 20
_MAX_BIO_LEN = 200

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


# ─────────────────────────────────────
# GET /api/v1/users/me
# ─────────────────────────────────────
@router.get(
    "/me",
    response_model=UserMeResponse,
    summary="내 정보 조회 (마이페이지)",
    description="선호 가수, 차단 가수, 연동된 SNS 계정 목록을 포함한 전체 프로필을 반환합니다.",
)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserMeResponse:
    service = UserService(db)
    profile = await service.get_full_profile(current_user.id)
    return UserMeResponse(
        **UserResponse.model_validate(profile.user).model_dump(),
        favorite_singers=[
            SingerInfo(singer_id=s.singer_id, name=s.name, gender=s.gender, photo_url=s.photo_url)
            for s in profile.favorite_singers
        ],
        blocked_singers=[
            SingerInfo(singer_id=s.singer_id, name=s.name, gender=s.gender, photo_url=s.photo_url)
            for s in profile.blocked_singers
        ],
        blocked_songs=[BlockedSongItem(**item) for item in profile.blocked_songs],
        linked_providers=service.get_linked_providers(profile.user),
    )


# ─────────────────────────────────────
# PATCH /api/v1/users/me/profile
# ─────────────────────────────────────
@router.patch(
    "/me/profile",
    response_model=UserResponse,
    summary="마이페이지 프로필 수정",
    description=(
        "`multipart/form-data`로 전송. "
        "`nickname`, `bio`, `profile_image` 중 하나 이상 포함해야 합니다. "
        "`bio`를 빈 문자열로 보내면 소개글이 삭제됩니다."
    ),
)
async def update_mypage_profile(
    nickname: Optional[str] = Form(None, description="닉네임 (1~20자)"),
    bio: Optional[str] = Form(None, description="소개글 (최대 200자, 빈 문자열 = 삭제)"),
    profile_image: Optional[UploadFile] = File(None, description="프로필 사진 (jpeg/png/webp, 최대 5MB)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    nickname_provided = nickname is not None
    bio_provided = bio is not None
    image_provided = profile_image is not None and bool(profile_image.filename)

    if not nickname_provided and not bio_provided and not image_provided:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "NOTHING_TO_UPDATE", "message": "수정할 항목이 없습니다."},
        )

    # ── 닉네임 검증 ──────────────────────────────────
    if nickname_provided:
        stripped_nickname = nickname.strip() if nickname else ""
        if not stripped_nickname:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "INVALID_NICKNAME", "message": "닉네임은 공백만으로 구성될 수 없습니다."},
            )
        if len(stripped_nickname) > _MAX_NICKNAME_LEN:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "NICKNAME_TOO_LONG", "message": f"닉네임은 최대 {_MAX_NICKNAME_LEN}자입니다."},
            )

    # ── 소개글 검증 ───────────────────────────────────
    if bio_provided and bio and len(bio) > _MAX_BIO_LEN:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "BIO_TOO_LONG", "message": f"소개글은 최대 {_MAX_BIO_LEN}자입니다."},
        )

    # ── 프로필 사진 업로드 ────────────────────────────
    profile_img_url: Optional[str] = None
    if image_provided:
        content_type = profile_image.content_type or ""
        if content_type not in _ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail={"code": "INVALID_IMAGE_TYPE", "message": "jpeg, png, webp 이미지만 업로드 가능합니다."},
            )
        file_bytes = await profile_image.read()
        if len(file_bytes) > _MAX_IMAGE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={"code": "IMAGE_TOO_LARGE", "message": "이미지 크기는 5MB 이하여야 합니다."},
            )
        ext = content_type.split("/")[-1]
        key = f"profiles/{current_user.id}/{int(time.time())}.{ext}"
        url = upload_image_to_s3(file_bytes, key, content_type)
        if url is None:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"code": "S3_UPLOAD_FAILED", "message": "프로필 사진 업로드에 실패했습니다."},
            )
        profile_img_url = url

    # ── 서비스 레이어 ─────────────────────────────────
    service = UserService(db)
    updated = await service.update_mypage_profile(
        user_id=current_user.id,
        nickname=nickname,
        bio=bio,
        profile_img_url=profile_img_url,
        _nickname_provided=nickname_provided,
        _bio_provided=bio_provided,
    )
    return UserResponse.model_validate(updated)


# ─────────────────────────────────────
# DELETE /api/v1/users/me/linked-accounts/{provider}
# ─────────────────────────────────────
@router.delete(
    "/me/linked-accounts/{provider}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="SNS 계정 연동 해제",
    description="연동된 카카오 또는 네이버 계정을 해제합니다. 기본 로그인 계정은 해제할 수 없습니다.",
)
async def unlink_account(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    if provider not in {"kakao", "naver"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_PROVIDER", "message": "provider는 kakao 또는 naver이어야 합니다."},
        )
    if current_user.provider == provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "PRIMARY_PROVIDER", "message": "기본 로그인 계정은 연동 해제할 수 없습니다."},
        )
    service = UserService(db)
    await service.unlink_account(user_id=current_user.id, provider=provider)


# ─────────────────────────────────────
# GET /api/v1/users/me/blocked-singers
# ─────────────────────────────────────
@router.get(
    "/me/blocked-singers",
    response_model=BlockedSingersListResponse,
    summary="차단한 가수 목록 조회",
)
async def get_blocked_singers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BlockedSingersListResponse:
    service = UserService(db)
    items = await service.get_blocked_singers(current_user.id)
    return BlockedSingersListResponse(
        blocked_singers=[BlockedSingerItem(**item) for item in items]
    )


# ─────────────────────────────────────
# POST /api/v1/users/me/blocked-singers
# ─────────────────────────────────────
@router.post(
    "/me/blocked-singers",
    response_model=BlockedSingerItem,
    status_code=status.HTTP_201_CREATED,
    summary="가수 차단",
)
async def block_singer(
    body: BlockSingerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BlockedSingerItem:
    service = UserService(db)
    item = await service.block_singer(current_user.id, body.singer_id)
    await db.commit()
    return BlockedSingerItem(**item)


# ─────────────────────────────────────
# DELETE /api/v1/users/me/blocked-singers/{singer_id}
# ─────────────────────────────────────
@router.delete(
    "/me/blocked-singers/{singer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="가수 차단 해제",
)
async def unblock_singer(
    singer_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = UserService(db)
    await service.unblock_singer(current_user.id, singer_id)
    await db.commit()


# ─────────────────────────────────────
# GET /api/v1/users/me/blocked-songs
# ─────────────────────────────────────
@router.get(
    "/me/blocked-songs",
    response_model=BlockedSongsListResponse,
    summary="차단한 곡 목록 조회",
)
async def get_blocked_songs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BlockedSongsListResponse:
    service = UserService(db)
    items = await service.get_blocked_songs(current_user.id)
    return BlockedSongsListResponse(
        blocked_songs=[BlockedSongItem(**item) for item in items]
    )


# ─────────────────────────────────────
# POST /api/v1/users/me/blocked-songs
# ─────────────────────────────────────
@router.post(
    "/me/blocked-songs",
    response_model=BlockedSongItem,
    status_code=status.HTTP_201_CREATED,
    summary="곡 차단",
)
async def block_song(
    body: BlockSongRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BlockedSongItem:
    service = UserService(db)
    item = await service.block_song(current_user.id, body.song_id)
    await db.commit()
    return BlockedSongItem(**item)


# ─────────────────────────────────────
# DELETE /api/v1/users/me/blocked-songs/{song_id}
# ─────────────────────────────────────
@router.delete(
    "/me/blocked-songs/{song_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="곡 차단 해제",
)
async def unblock_song(
    song_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = UserService(db)
    await service.unblock_song(current_user.id, song_id)
    await db.commit()


# ─────────────────────────────────────
# PATCH /api/v1/users/me  (기존 유지 - 닉네임 JSON 전용)
# ─────────────────────────────────────
@router.patch(
    "/me",
    response_model=UserResponse,
    summary="닉네임 수정 (JSON)",
    description="닉네임만 JSON으로 빠르게 수정할 때 사용합니다. 사진/소개글은 `/me/profile`을 사용하세요.",
)
async def update_profile(
    body: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "NOTHING_TO_UPDATE", "message": "수정할 항목이 없습니다."},
        )
    service = UserService(db)
    updated = await service.update_profile(
        user_id=current_user.id,
        nickname=update_data.get("nickname"),
    )
    return UserResponse.model_validate(updated)


# ─────────────────────────────────────
# PATCH /api/v1/users/me/settings
# ─────────────────────────────────────
@router.patch(
    "/me/settings",
    summary="설정 변경 (JSONB 부분 업데이트)",
    description="전달된 키만 기존 settings에 머지합니다. "
    "예: `{\"push_enabled\": false}` → push_enabled만 변경.",
)
async def update_settings(
    body: SettingsUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "NOTHING_TO_UPDATE", "message": "수정할 항목이 없습니다."},
        )
    service = UserService(db)
    return await service.update_settings(
        user_id=current_user.id,
        update_data=update_data,
    )


# ─────────────────────────────────────
# GET /api/v1/users/me/busking-history
# ─────────────────────────────────────
class _SetlistItem(BaseModel):
    title: str
    artist: str
    album_art_url: Optional[str] = None
    order_index: int

class _BuskingHistoryItem(BaseModel):
    room_id: str
    title: str
    thumbnail: Optional[str] = None
    status: str
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    peak_viewer_count: int
    total_unique_viewers: int
    setlist: List[_SetlistItem]

class _BuskingHistoryResponse(BaseModel):
    stats: dict
    history: List[_BuskingHistoryItem]

@router.get(
    "/me/busking-history",
    response_model=_BuskingHistoryResponse,
    summary="내 버스킹 목록 조회",
)
async def get_my_busking_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rooms_result = await db.execute(
        select(BuskingRoom)
        .where(BuskingRoom.host_id == current_user.id)
        .order_by(BuskingRoom.created_at.desc())
    )
    rooms = rooms_result.scalars().all()

    history = []
    for room in rooms:
        setlist_result = await db.execute(
            select(BuskingSetlistItem)
            .where(BuskingSetlistItem.room_id == room.id)
            .order_by(BuskingSetlistItem.order_index)
        )
        setlist = setlist_result.scalars().all()

        history.append(_BuskingHistoryItem(
            room_id=str(room.id),
            title=room.title,
            thumbnail=room.thumbnail,
            status=room.status,
            started_at=room.started_at.isoformat() if room.started_at else None,
            ended_at=room.ended_at.isoformat() if room.ended_at else None,
            peak_viewer_count=room.peak_viewer_count or 0,
            total_unique_viewers=room.total_unique_viewers or 0,
            setlist=[
                _SetlistItem(
                    title=s.title,
                    artist=s.artist,
                    album_art_url=s.album_art_url,
                    order_index=s.order_index,
                )
                for s in setlist
            ],
        ))

    return _BuskingHistoryResponse(
        stats={"total_lives": len(rooms)},
        history=history,
    )
