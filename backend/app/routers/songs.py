import logging
from fastapi import APIRouter, HTTPException, status
from app.services.spotify import SpotifyService
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/music", tags=["music"])

spotify = SpotifyService(settings.SPOTIFY_CLIENT_ID, settings.SPOTIFY_CLIENT_SECRET)


@router.get("/search")
async def search_music(q: str):
    if not q or not q.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "EMPTY_QUERY", "message": "검색어를 입력해 주세요."},
        )
    try:
        results = await spotify.search_tracks(q)
    except Exception as e:
        logger.error("Spotify 검색 실패: q=%s error=%s", q, e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "SPOTIFY_ERROR", "message": "음악 검색에 실패했습니다. 잠시 후 다시 시도해 주세요."},
        )

    tracks = []
    for item in results.get("tracks", {}).get("items", []):
        images = item["album"].get("images", [])
        artists = item.get("artists", [])
        tracks.append({
            "name": item["name"],
            "artist": artists[0]["name"] if artists else "",
            "album_image": images[0]["url"] if images else None,
            "uri": item["uri"],
        })
    return tracks
