"""Singers 라우터 - 가수 관련 엔드포인트"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.singer_service import SingerService
from app.schemas.singer import RandomSingersResponse, SingerInfo, SingerSearchResponse

router = APIRouter(prefix="/api/v1/singers", tags=["Singers"])


@router.get("/search", response_model=SingerSearchResponse)
async def search_singers(
    q: str = Query(..., min_length=1, description="검색할 가수 이름"),
    limit: int = Query(10, ge=1, le=30),
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """가수 이름 또는 별칭으로 검색 (부분 일치)"""
    service = SingerService(db)
    singers = await service.search_singers(query=q, limit=limit)
    return SingerSearchResponse(
        singers=[
            SingerInfo(singer_id=s.singer_id, name=s.name, gender=s.gender, photo_url=s.photo_url)
            for s in singers
        ]
    )


@router.get("/random", response_model=RandomSingersResponse)
async def get_random_singers(
    gender: Optional[str] = Query(None, description="성별 필터 (male | female). 미입력 시 남자 6명 + 여자 6명"),
    limit: int = Query(6, ge=1, le=50, description="성별 지정 시 반환할 가수 수"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """성별 필터 후 차단 제외 랜덤 가수 목록 반환. gender 미입력 시 남자 6 + 여자 6"""
    service = SingerService(db)
    if gender is None:
        male = await service.get_random_singers(user_id=current_user.id, gender="male", limit=6)
        female = await service.get_random_singers(user_id=current_user.id, gender="female", limit=6)
        singers = male + female
    else:
        singers = await service.get_random_singers(user_id=current_user.id, gender=gender, limit=limit)
    return RandomSingersResponse(
        singers=[
            SingerInfo(
                singer_id=s.singer_id,
                name=s.name,
                gender=s.gender,
                photo_url=s.photo_url,
            )
            for s in singers
        ]
    )
