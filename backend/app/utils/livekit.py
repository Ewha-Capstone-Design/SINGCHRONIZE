"""LiveKit Cloud 유틸 — 토큰 발급 및 Room 관리"""
import logging
from uuid import UUID

from livekit import api
from livekit.api import CreateRoomRequest, DeleteRoomRequest

from app.config import settings

logger = logging.getLogger(__name__)


def _room_name(room_id: UUID | str) -> str:
    """BuskingRoom UUID → LiveKit room name"""
    return f"busking-{room_id}"


def create_host_token(room_id: UUID | str, user_id: str) -> str:
    """방 생성자(스트리머)용 토큰 — 오디오 publish 가능."""
    token = (
        api.AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
        .with_identity(str(user_id))
        .with_name(str(user_id))
        .with_grants(api.VideoGrants(
            room_join=True,
            room=_room_name(room_id),
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True,
        ))
    )
    return token.to_jwt()


def create_viewer_token(room_id: UUID | str, user_id: str) -> str:
    """뷰어용 토큰 — subscribe 전용(오디오 수신만 가능)."""
    token = (
        api.AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
        .with_identity(str(user_id))
        .with_name(str(user_id))
        .with_grants(api.VideoGrants(
            room_join=True,
            room=_room_name(room_id),
            can_publish=False,
            can_subscribe=True,
            can_publish_data=False,
        ))
    )
    return token.to_jwt()


async def create_livekit_room(room_id: UUID | str) -> None:
    """LiveKit Cloud에 Room 생성. 방 생성 시 호출."""
    name = _room_name(room_id)
    try:
        async with api.LiveKitAPI(
            url=settings.LIVEKIT_URL,
            api_key=settings.LIVEKIT_API_KEY,
            api_secret=settings.LIVEKIT_API_SECRET,
        ) as lk:
            await lk.room.create_room(CreateRoomRequest(name=name))
        logger.info("LiveKit room 생성: %s", name)
    except Exception as e:
        # LiveKit room 생성 실패가 방 생성 전체를 막으면 안 됨 — 로깅 후 계속
        logger.error("LiveKit room 생성 실패 (%s): %s", name, e)


async def delete_livekit_room(room_id: UUID | str) -> None:
    """LiveKit Cloud Room 삭제. 라이브 종료 시 호출."""
    name = _room_name(room_id)
    try:
        async with api.LiveKitAPI(
            url=settings.LIVEKIT_URL,
            api_key=settings.LIVEKIT_API_KEY,
            api_secret=settings.LIVEKIT_API_SECRET,
        ) as lk:
            await lk.room.delete_room(DeleteRoomRequest(room=name))
        logger.info("LiveKit room 삭제: %s", name)
    except Exception as e:
        logger.error("LiveKit room 삭제 실패 (%s): %s", name, e)
