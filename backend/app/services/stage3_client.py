"""ECS stage3-api HTTP 호출 + 실패 시 2차 추천 결과 폴백."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def flatten_stage2_recommended_songs(data: Any, limit: int) -> List[Tuple[str, float]]:
    """recommended_songs JSON에서 (song_id, score) 추출 — 중복은 최고 점수 유지."""
    if not isinstance(data, dict):
        return []
    best: Dict[str, float] = {}
    for key in ("genre_recommendations", "situation_recommendations"):
        block = data.get(key)
        if not isinstance(block, dict):
            continue
        for _label, songs in block.items():
            if not isinstance(songs, list):
                continue
            for s in songs:
                if not isinstance(s, dict):
                    continue
                sid = s.get("id") or s.get("song_id")
                if sid is None:
                    continue
                raw = s.get("score2", s.get("score", 0.0))
                try:
                    sc = float(raw)
                except (TypeError, ValueError):
                    sc = 0.0
                k = str(sid)
                if k not in best or sc > best[k]:
                    best[k] = sc
    ranked = sorted(best.items(), key=lambda x: x[1], reverse=True)
    return ranked[:limit]


async def fetch_stage3_similar_voice_picks(
    *,
    user_id: str,
    period: str,
    limit: int,
    interaction_since: Optional[datetime] = None,
    interaction_until: Optional[datetime] = None,
) -> Optional[List[Dict[str, Any]]]:
    """
    stage3-api 성공 시 [{"song_id", "score"}, ...] 반환.
    URL 미설정·HTTP 실패·타임아웃 → None.
    """
    base = (settings.STAGE3_API_BASE_URL or "").strip().rstrip("/")
    if not base:
        return None
    url = f"{base}/stage3/similar-voice-picks"
    timeout = httpx.Timeout(settings.STAGE3_API_TIMEOUT_SECONDS)
    payload: Dict[str, Any] = {
        "user_id": user_id,
        "period": period,
        "limit": limit,
    }
    if interaction_since is not None:
        payload["interaction_since"] = interaction_since.isoformat()
    if interaction_until is not None:
        payload["interaction_until"] = interaction_until.isoformat()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            body = r.json()
    except httpx.TimeoutException:
        logger.warning("stage3-api timeout user_id=%s url=%s", user_id, url)
        return None
    except httpx.HTTPError as e:
        logger.warning("stage3-api HTTP error user_id=%s: %s", user_id, e)
        return None
    except (ValueError, KeyError, TypeError) as e:
        logger.warning("stage3-api bad response user_id=%s: %s", user_id, e)
        return None

    results = body.get("results")
    if not isinstance(results, list):
        return None
    out: List[Dict[str, Any]] = []
    for row in results:
        if not isinstance(row, dict):
            continue
        sid = row.get("song_id")
        if sid is None:
            continue
        try:
            score = float(row.get("score", 0.0))
        except (TypeError, ValueError):
            score = 0.0
        out.append({"song_id": str(sid), "score": score})
    return out
