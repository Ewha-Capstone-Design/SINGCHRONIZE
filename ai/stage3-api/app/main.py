import logging
import os

from fastapi import FastAPI, HTTPException

from app.models import RecommendRequest, RecommendResponse
from app.service.recommender import recommend_similar_voice

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("stage3-api")

app = FastAPI(title="stage3-api", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/stage3/similar-voice-picks", response_model=RecommendResponse)
def stage3_recommend(req: RecommendRequest):
    try:
        result = recommend_similar_voice(
            user_id=req.user_id,
            period=req.period,
            limit=req.limit,
            interaction_since=req.interaction_since,
            interaction_until=req.interaction_until,
        )
    except RuntimeError as e:
        logger.exception("config/db error")
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        logger.exception("recommendation failed")
        raise HTTPException(status_code=500, detail="internal error") from e

    return RecommendResponse(results=result)
