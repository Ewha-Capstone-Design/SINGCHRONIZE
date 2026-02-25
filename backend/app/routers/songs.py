from fastapi import APIRouter, Depends
from app.services.spotify import SpotifyService
from app.config import settings # .env에 저장한 키 가져오기

router = APIRouter(prefix="/api/v1/music", tags=["music"])

spotify = SpotifyService(settings.SPOTIFY_CLIENT_ID, settings.SPOTIFY_CLIENT_SECRET)

@router.get("/search")
async def search_music(q: str):
    results = spotify.search_tracks(q)
    
    # 필요한 정보(제목, 가수, 앨범커버, URI)만 추려서 프론트에 전달
    tracks = []
    for item in results.get("tracks", {}).get("items", []):
        tracks.append({
            "name": item["name"],
            "artist": item["artists"][0]["name"],
            "album_image": item["album"]["images"][0]["url"],
            "uri": item["uri"] # 나중에 재생할 때 필수!
        })
    return tracks