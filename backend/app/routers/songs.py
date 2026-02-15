from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
import logging  # 에러 추적을 위해 추가

from app.database import get_db
from app.models.song import Song
from app.schemas.song import SongResponse

# 로거 설정
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/songs", tags=["Songs"])

@router.get("/search", response_model=SongResponse)
async def search_songs(
    q: str = Query(..., min_length=1, description="검색어 (제목 또는 가수)"),
    db: AsyncSession = Depends(get_db),
):
    try:
        # 1. 쿼리 생성
        query = (
            select(Song)
            .where(
                or_(
                    Song.title.ilike(f"%{q}%"),
                    Song.artist.ilike(f"%{q}%"),
                )
            )
            .order_by(Song.created_at.desc())
            .limit(20)
        )

        # 2. 실행 및 결과 페칭
        result = await db.execute(query)
        songs = result.scalars().all()
        
        # 3. 로그 찍기 (성공 확인용)
        logger.info(f"🔍 검색어 '{q}' 검색 성공: {len(songs)}건 발견")

        # 4. 결과 반환 (Response 모델 형식에 맞춤)
        return SongResponse(songs=list(songs))

    except Exception as e:
        # 🚨 여기서 터미널에 진짜 에러 이유를 찍어줍니다!
        logger.error(f"❌ 검색 중 에러 발생: {str(e)}")
        
        # 브라우저에서도 에러 내용을 확인할 수 있게 던져줍니다.
        raise HTTPException(
            status_code=500, 
            detail=f"데이터베이스 연결 에러: {str(e)}"
        )