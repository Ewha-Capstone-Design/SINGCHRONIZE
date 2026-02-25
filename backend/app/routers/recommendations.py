from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db  
from app.models import Recommendation 
from app.utils.aws import generate_presigned_url, send_sqs_message
import json
import uuid

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])

@router.post("/upload-url")
async def get_upload_url(user_id: str):
    """1단계: S3 업로드 URL 발급"""
    # 파일명을 중복되지 않게 생성 (예: user1_uuid.wav)
    file_name = f"voices/{user_id}_{uuid.uuid4()}.wav"
    
    url = generate_presigned_url(file_name)
    if not url:
        raise HTTPException(status_code=500, detail="URL 생성 실패")
    
    return {"upload_url": url, "s3_key": file_name}

@router.post("/start")
async def start_recommendation(
    user_id: str, 
    s3_key: str, 
    db: AsyncSession = Depends(get_db)
):
    """
    [1차 추천 프로세스 시작]
    1. DB에 추천 작업 생성 (상태: QUEUED)
    2. SQS에 메시지 발행 (AI Worker에게 알림)
    3. job_id(DB ID) 즉시 반환
    """
    try:
        # 1. DB에 작업 생성 (이력 관리 및 상태 저장용)
        new_job = Recommendation(
            user_id=user_id,
            # base_report_id나 다른 필요한 값들 초기화
            recommended_songs=None,  # 아직 결과 없음
            # 만약 status 컬럼이 있다면 'QUEUED' 추가
        )
        db.add(new_job)
        await db.commit()
        await db.refresh(new_job)

        # 2. SQS에 넣을 메시지 구성 (AI Worker가 필요한 모든 정보)
        message_payload = {
            "job_id": str(new_job.id),  # 생성된 DB PK
            "user_id": str(user_id),
            "s3_key": s3_key,      # S3에 올라간 목소리 파일 경로
            "task_type": "FIRST_RECOMMENDATION",
            "status": "QUEUED"
        }

        # 3. SQS로 메시지 쏘기
        sqs_res = send_sqs_message(json.dumps(message_payload))
        
        if not sqs_res:
            # SQS 전송 실패 시 DB 상태도 바꿔주거나 예외 처리
            raise Exception("SQS Message 전송 실패")

        # 4. 프론트엔드에 job_id(신규 생성된 ID) 바로 응답
        return {
            "job_id": new_job.id,
            "status": "QUEUED",
            "message": "추천 분석이 시작되었습니다."
        }

    except Exception as e:
        await db.rollback()
        print(f"❌ 추천 시작 중 에러 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    
@router.get("/{job_id}")
async def get_recommendation_status(
    job_id: str, 
    db: AsyncSession = Depends(get_db)
):
    """
    [추천 작업 상태 조회]
    프론트엔드에서 결과가 나올 때까지 주기적으로 호출할 API
    """
    try:
        # DB에서 해당 job_id 찾기
        job_uuid = uuid.UUID(job_id)
        result = await db.execute(
            select(Recommendation).where(Recommendation.id == job_uuid)
        )
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=404, detail="해당 작업을 찾을 수 없습니다.")

        # 상태와 결과를 함께 반환
        return {
            "job_id": str(job.id),
            "status": job.status,
            "result": job.recommended_songs, # AI가 채워넣기 전까진 None일 거예요
            "created_at": job.created_at
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))