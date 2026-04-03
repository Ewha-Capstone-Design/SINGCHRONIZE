"""온보딩 라우터 - 회원가입 후 초기 프로필 설정"""
import time
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.singer import FavoriteSingersSelectRequest, FavoriteSingersSelectResponse, SingerInfo
from app.schemas.user import UserResponse
from app.services.singer_service import SingerService
from app.services.user_service import UserService
from app.utils.aws import upload_image_to_s3

router = APIRouter(prefix="/api/v1/users/me/onboarding", tags=["Onboarding"])

_ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
_MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB
_MAX_NICKNAME_LEN = 20


@router.post(
    "/step1",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="프로필 설정 1단계",
    description=(
        "회원가입 직후 온보딩 1단계. "
        "닉네임(필수)과 프로필 사진(선택)을 설정합니다. "
        "`multipart/form-data`로 전송하세요."
    ),
)
async def onboarding_step1(
    nickname: str = Form(..., description="닉네임 (1~20자, 공백만 불가)"),
    profile_image: Optional[UploadFile] = File(None, description="프로필 사진 (jpeg/png/webp, 최대 5MB)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    # ── 닉네임 검증 ──────────────────────────────────────
    stripped = nickname.strip()
    if not stripped:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "INVALID_NICKNAME", "message": "닉네임은 공백만으로 구성될 수 없습니다."},
        )
    if len(stripped) > _MAX_NICKNAME_LEN:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "NICKNAME_TOO_LONG", "message": f"닉네임은 최대 {_MAX_NICKNAME_LEN}자입니다."},
        )

    # ── 프로필 사진 업로드 ────────────────────────────────
    profile_img_url: Optional[str] = None
    if profile_image and profile_image.filename:
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

    # ── 서비스 레이어 ─────────────────────────────────────
    service = UserService(db)
    updated = await service.setup_onboarding_step1(
        user_id=current_user.id,
        nickname=stripped,
        profile_img_url=profile_img_url,
    )

    await db.commit()
    await db.refresh(updated)

    return UserResponse.model_validate(updated, from_attributes=True)


@router.post(
    "/step2",
    response_model=FavoriteSingersSelectResponse,
    status_code=status.HTTP_200_OK,
    summary="즐겨부르는 가수 선택 (온보딩 2단계)",
    description=(
        "가수 ID 목록을 받아 즐겨부르는 가수로 저장합니다. "
        "기존 선택을 전부 교체하므로 마이페이지 수정 시에도 동일하게 호출할 수 있습니다. "
        "가수 목록은 `GET /api/v1/singers/random` API로 조회하세요."
    ),
)
async def onboarding_step2(
    body: FavoriteSingersSelectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FavoriteSingersSelectResponse:
    service = SingerService(db)
    singers = await service.select_favorite_singers(
        user_id=current_user.id,
        singer_ids=body.singer_ids,
    )

    # 온보딩 2단계 완료 상태 반영
    user_service = UserService(db)
    await user_service.update_settings(
        user_id=current_user.id,
        update_data={"onboarding_step": 2},
    )

    return FavoriteSingersSelectResponse(
        singers=[
            SingerInfo(singer_id=s.singer_id, name=s.name, gender=s.gender, photo_url=s.photo_url)
            for s in singers
        ]
    )
