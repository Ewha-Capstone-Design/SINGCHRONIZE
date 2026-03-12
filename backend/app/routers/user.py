"""유저 라우터"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdateRequest, SettingsUpdateRequest
from app.services.user_service import UserService

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


# ─────────────────────────────────────
# GET /api/v1/users/me
# ─────────────────────────────────────
@router.get(
    "/me",
    response_model=UserResponse,
    summary="내 정보 조회",
    description="현재 로그인된 사용자의 정보를 반환합니다. "
    "캐시된 보컬 분석 정보(vocal_summary)도 포함됩니다.",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return UserResponse.model_validate(current_user)


# ─────────────────────────────────────
# PATCH /api/v1/users/me
# ─────────────────────────────────────
@router.patch(
    "/me",
    response_model=UserResponse,
    summary="프로필 수정",
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
            detail="수정할 항목이 없습니다.",
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
            detail="수정할 항목이 없습니다.",
        )

    service = UserService(db)
    return await service.update_settings(
        user_id=current_user.id,
        update_data=update_data,
    )
