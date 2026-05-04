"""버스킹 라우터 — 라이브 세션 전체 생명주기 + WebSocket"""
import asyncio
import json
import logging
import uuid as uuid_lib
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import AsyncSessionLocal, get_db
from app.dependencies.auth import get_current_user
from app.models.busking import (
    BuskingChatMessage,
    BuskingReaction,
    BuskingResult,
    BuskingRoom,
    BuskingSetlistItem,
)
from app.models.user import User
from app.schemas.busking import (
    BuskingRoomCreate,
    BuskingRoomCreateResponse,
    BuskingRoomDetailResponse,
    BuskingRoomResponse,
    BuskingResultResponse,
    HostProfile,
    LiveKitJoinResponse,
    SetlistItemResponse,
    ThumbnailPresignedResponse,
)
from app.services.auth_service import AuthService
from app.utils.aws import generate_presigned_url
from app.utils.livekit import (
    create_host_token,
    create_livekit_room,
    create_viewer_token,
    delete_livekit_room,
)

router = APIRouter(prefix="/api/v1/busking", tags=["Busking"])
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# ConnectionManager (In-memory)
#
# NOTE: 멀티 서버 확장 시 Redis Pub/Sub으로 교체 필요.
# 현재는 단일 프로세스 내 연결만 관리하므로 서버를 여러 대 띄우면
# 서버 A의 클라이언트와 서버 B의 클라이언트 간 broadcast가 불가능함.
# 교체 포인트: broadcast() → Redis PUBLISH, connect() 후 SUBSCRIBE.
# ═══════════════════════════════════════════════════════════════
class ConnectionManager:
    def __init__(self):
        # room_id -> [(websocket, user_id)]
        self._connections: dict[str, list[tuple[WebSocket, str]]] = {}
        # room_id -> host user_id
        self._hosts: dict[str, str] = {}
        # room_id -> set of user_ids (누적 unique 뷰어)
        self._unique_viewers: dict[str, set[str]] = {}
        # room_id -> {"match": int, "mismatch": int}
        self._reactions: dict[str, dict[str, int]] = {}
        # room_id -> peak viewer count
        self._peak_counts: dict[str, int] = {}
        # room_id -> {user_id -> {nickname, profile_img, bio}}
        self._profiles: dict[str, dict[str, dict]] = {}

    async def connect(self, websocket: WebSocket, room_id: str, user_id: str, is_host: bool):
        await websocket.accept()
        rid = str(room_id)
        if rid not in self._connections:
            self._connections[rid] = []
            self._unique_viewers[rid] = set()
            self._reactions[rid] = {"match": 0, "mismatch": 0}
            self._peak_counts[rid] = 0

        self._connections[rid].append((websocket, user_id))
        self._unique_viewers[rid].add(user_id)

        if is_host:
            self._hosts[rid] = user_id

        current = self.viewer_count(rid)
        if current > self._peak_counts[rid]:
            self._peak_counts[rid] = current

    def disconnect(self, websocket: WebSocket, room_id: str):
        rid = str(room_id)
        if rid in self._connections:
            self._connections[rid] = [
                (ws, uid) for ws, uid in self._connections[rid] if ws != websocket
            ]
            if not self._connections[rid]:
                del self._connections[rid]

    def viewer_count(self, room_id) -> int:
        return len(self._connections.get(str(room_id), []))

    def is_host(self, room_id, user_id: str) -> bool:
        return self._hosts.get(str(room_id)) == str(user_id)

    def peak_count(self, room_id) -> int:
        return self._peak_counts.get(str(room_id), 0)

    def unique_viewer_count(self, room_id) -> int:
        return len(self._unique_viewers.get(str(room_id), set()))

    def add_reaction(self, room_id, value: str):
        rid = str(room_id)
        self._reactions.setdefault(rid, {"match": 0, "mismatch": 0})
        if value in self._reactions[rid]:
            self._reactions[rid][value] += 1

    def get_reactions(self, room_id) -> dict:
        return dict(self._reactions.get(str(room_id), {"match": 0, "mismatch": 0}))

    async def broadcast(self, room_id, message: dict):
        rid = str(room_id)
        if rid not in self._connections:
            return
        data = json.dumps(message, ensure_ascii=False)
        dead: list[WebSocket] = []
        for ws, _ in list(self._connections[rid]):
            try:
                await ws.send_text(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, rid)

    def set_profile(self, room_id: str, user_id: str, profile: dict):
        self._profiles.setdefault(str(room_id), {})[str(user_id)] = profile

    def get_profile(self, room_id: str, user_id: str) -> dict:
        return self._profiles.get(str(room_id), {}).get(str(user_id), {})

    def cleanup(self, room_id):
        rid = str(room_id)
        self._connections.pop(rid, None)
        self._hosts.pop(rid, None)
        self._unique_viewers.pop(rid, None)
        self._reactions.pop(rid, None)
        self._peak_counts.pop(rid, None)
        self._profiles.pop(rid, None)


manager = ConnectionManager()


# ═══════════════════════════════════════════════════════════════
# REST Endpoints
# ═══════════════════════════════════════════════════════════════

# ── 1. 썸네일 Presigned URL ────────────────────────────────────

@router.post("/thumbnail/presigned-url", response_model=ThumbnailPresignedResponse)
async def get_thumbnail_presigned_url(
    current_user: User = Depends(get_current_user),
):
    """S3 썸네일 직접 업로드용 presigned PUT URL 반환. 클라이언트가 이 URL로 PUT 요청."""
    key = f"busking/thumbnails/{current_user.id}/{uuid_lib.uuid4()}.jpg"
    upload_url = generate_presigned_url(key, content_type="image/jpeg")
    if not upload_url:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "S3_URL_FAILED", "message": "썸네일 업로드 URL 생성에 실패했습니다. 잠시 후 다시 시도해 주세요."},
        )
    s3_url = f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
    return ThumbnailPresignedResponse(upload_url=upload_url, s3_url=s3_url, key=key)


# ── 2. 방 생성 ────────────────────────────────────────────────

@router.post("/rooms", response_model=BuskingRoomCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    room_data: BuskingRoomCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """버스킹 방 생성. 응답에 LiveKit 호스트 토큰 포함 — 클라이언트가 이 토큰으로 오디오 publish."""
    room = BuskingRoom(
        host_id=current_user.id,
        title=room_data.title,
        thumbnail=room_data.thumbnail_url,
        status="PREPARING",
    )
    db.add(room)
    await db.flush()

    items = [
        BuskingSetlistItem(
            room_id=room.id,
            song_id=item.song_id or None,   # Spotify URI 또는 내부 UUID — 없으면 NULL
            title=item.title,
            artist=item.artist,
            album_art_url=item.album_art_url,
            order_index=item.order_index,
        )
        for item in room_data.setlist
    ]
    db.add_all(items)
    await db.flush()

    # LiveKit Room 생성 + 호스트 토큰 발급
    await create_livekit_room(room.id)
    host_token = create_host_token(room.id, str(current_user.id))

    setlist = await _get_setlist(db, room.id)
    detail = _build_room_detail(room, setlist, viewer_count=0, host=current_user)
    return BuskingRoomCreateResponse(
        **detail.model_dump(),
        livekit_token=host_token,
        livekit_url=settings.LIVEKIT_URL,
    )


# ── 3. 방 목록 ────────────────────────────────────────────────

@router.get("/rooms", response_model=List[BuskingRoomResponse])
async def get_rooms(db: AsyncSession = Depends(get_db)):
    """PREPARING / LIVE 방 목록."""
    result = await db.execute(
        select(BuskingRoom)
        .where(BuskingRoom.status.in_(["PREPARING", "LIVE"]))
        .order_by(BuskingRoom.created_at.desc())
    )
    rooms = result.scalars().all()

    host_ids = list({r.host_id for r in rooms})
    host_rows = await db.execute(select(User).where(User.id.in_(host_ids)))
    host_map: dict[str, User] = {str(u.id): u for u in host_rows.scalars().all()}

    return [
        _build_room_response(r, manager.viewer_count(r.id), host=host_map.get(str(r.host_id)))
        for r in rooms
    ]


# ── 4. 방 상세 ────────────────────────────────────────────────

@router.get("/rooms/{room_id}", response_model=BuskingRoomDetailResponse)
async def get_room(room_id: UUID, db: AsyncSession = Depends(get_db)):
    """방 상세 정보 (셋리스트 포함, 실시간 뷰어 수 반영)."""
    room = await _get_room_or_404(db, room_id)
    setlist = await _get_setlist(db, room_id)
    host = await _fetch_user(db, room.host_id)
    return _build_room_detail(room, setlist, viewer_count=manager.viewer_count(room_id), host=host)


# ── 5. 라이브 시작 ────────────────────────────────────────────

@router.post("/rooms/{room_id}/start", response_model=BuskingRoomResponse)
async def start_room(
    room_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """PREPARING → LIVE. 호스트 전용."""
    room = await _get_room_or_404(db, room_id)
    _require_host(room, current_user)

    if room.status != "PREPARING":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "INVALID_STATUS", "message": f"PREPARING 상태인 방만 라이브를 시작할 수 있습니다. (현재: {room.status})"},
        )

    room.status = "LIVE"
    room.started_at = datetime.now(timezone.utc)
    await db.flush()

    await manager.broadcast(room_id, {
        "type": "state_update",
        "status": "LIVE",
        "current_song_index": room.current_song_index,
        "viewer_count": manager.viewer_count(room_id),
    })
    return _build_room_response(room, manager.viewer_count(room_id), host=current_user)


# ── 6. 라이브 종료 ────────────────────────────────────────────

@router.post("/rooms/{room_id}/end", response_model=BuskingRoomResponse)
async def end_room(
    room_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """LIVE → ENDED + 결과 집계. 호스트 전용."""
    room = await _get_room_or_404(db, room_id)
    _require_host(room, current_user)

    if room.status != "LIVE":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "INVALID_STATUS", "message": f"LIVE 상태인 방만 종료할 수 있습니다. (현재: {room.status})"},
        )

    now = datetime.now(timezone.utc)
    room.status = "ENDED"
    room.ended_at = now
    room.peak_viewer_count = manager.peak_count(room_id)
    room.total_unique_viewers = manager.unique_viewer_count(room_id)
    await db.flush()

    # 결과 집계
    reactions = manager.get_reactions(room_id)
    chat_count = (await db.execute(
        select(func.count()).where(BuskingChatMessage.room_id == room_id)
    )).scalar() or 0
    duration = int((now - room.started_at).total_seconds()) if room.started_at else None

    existing = (await db.execute(
        select(BuskingResult).where(BuskingResult.room_id == room_id)
    )).scalar_one_or_none()
    if not existing:
        db.add(BuskingResult(
            room_id=room_id,
            duration_seconds=duration,
            match_count=reactions.get("match", 0),
            mismatch_count=reactions.get("mismatch", 0),
            chat_count=chat_count,
        ))
    await db.flush()

    await manager.broadcast(room_id, {"type": "session_ended"})
    manager.cleanup(room_id)
    await delete_livekit_room(room_id)

    return _build_room_response(room, viewer_count=0, host=current_user)


# ── 7. 뷰어 LiveKit 토큰 발급 ────────────────────────────────

@router.post("/rooms/{room_id}/join", response_model=LiveKitJoinResponse)
async def join_room(
    room_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """뷰어 입장용 LiveKit 토큰 발급. LIVE 상태인 방만 허용."""
    room = await _get_room_or_404(db, room_id)
    if room.status != "LIVE":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "ROOM_NOT_LIVE", "message": "라이브 중인 방에만 입장할 수 있습니다."},
        )

    viewer_token = create_viewer_token(room_id, str(current_user.id))
    return LiveKitJoinResponse(
        livekit_token=viewer_token,
        livekit_url=settings.LIVEKIT_URL,
        room_id=room_id,
    )


# ── 8. 셋리스트 다음 곡 ─────────────────────────────────────

@router.patch("/rooms/{room_id}/setlist/current", response_model=BuskingRoomResponse)
async def advance_setlist(
    room_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """다음 곡으로 이동 (호스트 전용). WebSocket state_update 자동 broadcast."""
    room = await _get_room_or_404(db, room_id)
    _require_host(room, current_user)

    if room.status != "LIVE":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "ROOM_NOT_LIVE", "message": "라이브 중에만 곡을 변경할 수 있습니다."},
        )

    setlist = await _get_setlist(db, room_id)
    if room.current_song_index >= len(setlist) - 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "ALREADY_LAST_SONG", "message": "이미 마지막 곡입니다."},
        )

    room.current_song_index += 1
    await db.flush()

    await manager.broadcast(room_id, {
        "type": "state_update",
        "current_song_index": room.current_song_index,
        "viewer_count": manager.viewer_count(room_id),
    })
    return _build_room_response(room, manager.viewer_count(room_id), host=current_user)


# ── 9. 결과 조회 ─────────────────────────────────────────────

@router.get("/rooms/{room_id}/result", response_model=BuskingResultResponse)
async def get_result(room_id: UUID, db: AsyncSession = Depends(get_db)):
    """라이브 종료 후 결과 조회."""
    room = await _get_room_or_404(db, room_id)
    if room.status != "ENDED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "ROOM_NOT_ENDED", "message": f"종료된 방만 결과를 조회할 수 있습니다. (현재: {room.status})"},
        )

    result_row = (await db.execute(
        select(BuskingResult).where(BuskingResult.room_id == room_id)
    )).scalar_one_or_none()
    if not result_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "RESULT_NOT_FOUND", "message": "결과 데이터가 없습니다."},
        )

    setlist = await _get_setlist(db, room_id)

    # 곡별 match/mismatch 집계
    per_song_rows = (await db.execute(
        select(
            BuskingReaction.song_index,
            func.sum(case((BuskingReaction.value == "match", 1), else_=0)).label("match_count"),
            func.sum(case((BuskingReaction.value == "mismatch", 1), else_=0)).label("mismatch_count"),
        )
        .where(
            BuskingReaction.room_id == room_id,
            BuskingReaction.song_index.isnot(None),
        )
        .group_by(BuskingReaction.song_index)
        .order_by(BuskingReaction.song_index)
    )).all()

    per_song_map = {
        row.song_index: {"match": int(row.match_count), "mismatch": int(row.mismatch_count)}
        for row in per_song_rows
    }
    per_song = [
        {
            "song_index": s.order_index,
            "title": s.title,
            "artist": s.artist,
            **per_song_map.get(s.order_index, {"match": 0, "mismatch": 0}),
        }
        for s in setlist
    ]

    return BuskingResultResponse(
        live_id=room.id,
        title=room.title,
        duration_seconds=result_row.duration_seconds,
        peak_viewer_count=room.peak_viewer_count,
        total_unique_viewers=room.total_unique_viewers,
        setlist=[SetlistItemResponse.model_validate(s) for s in setlist],
        reactions={
            "total": {"match": result_row.match_count, "mismatch": result_row.mismatch_count},
            "per_song": per_song,
        },
        chat_count=result_row.chat_count,
        started_at=room.started_at,
        ended_at=room.ended_at,
    )


# ═══════════════════════════════════════════════════════════════
# WebSocket
# ═══════════════════════════════════════════════════════════════

@router.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    token: str = Query(..., description="JWT 액세스 토큰"),
):
    """
    실시간 WebSocket.  ws://.../api/v1/busking/ws/{room_id}?token=<JWT>

    클라이언트 → 서버:
      {"type": "chat",     "message": "..."}
      {"type": "reaction", "value": "match"|"mismatch"}
      {"type": "next_song"}  (호스트 전용 — REST PATCH 사용 권장)

    서버 → 클라이언트:
      {"type": "state_update",    "current_song_index": N, "viewer_count": N}
      {"type": "reaction_update", "match": N, "mismatch": N}
      {"type": "chat",            "user_id": "...", "message": "..."}
      {"type": "session_ended"}
      {"type": "error",           "detail": "..."}
    """
    # ── 인증 ──────────────────────────────────────────────────
    try:
        user_id = AuthService.verify_access_token(token)
    except Exception:
        await websocket.close(code=4001)
        return

    # ── 방 + 유저 조회 ────────────────────────────────────────
    async with AsyncSessionLocal() as db:
        row = await db.execute(select(BuskingRoom).where(BuskingRoom.id == room_id))
        room = row.scalar_one_or_none()
        user_row = await db.execute(select(User).where(User.id == user_id))
        ws_user = user_row.scalar_one_or_none()

    if not room:
        await websocket.close(code=4004)
        return
    if room.status == "ENDED":
        await websocket.close(code=4000, reason="이미 종료된 방입니다.")
        return

    is_host = str(room.host_id) == str(user_id)
    await manager.connect(websocket, room_id, user_id, is_host)
    if ws_user:
        manager.set_profile(room_id, user_id, {
            "id": str(ws_user.id),
            "nickname": ws_user.nickname,
            "profile_img": ws_user.profile_img,
        })
    logger.info("WS 연결: room=%s user=%s host=%s", room_id, user_id, is_host)

    # ── 입장 시 현재 상태 전송 ──────────────────────────────
    await manager.broadcast(room_id, {
        "type": "state_update",
        "current_song_index": room.current_song_index,
        "viewer_count": manager.viewer_count(room_id),
    })

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type")

            if msg_type == "chat":
                text = str(msg.get("message", "")).strip()
                if not text:
                    continue
                profile = manager.get_profile(room_id, user_id)
                await manager.broadcast(room_id, {
                    "type": "chat",
                    "user_id": user_id,
                    "nickname": profile.get("nickname", ""),
                    "profile_img": profile.get("profile_img"),
                    "message": text,
                })
                asyncio.create_task(_save_chat(room_id, user_id, text))

            elif msg_type == "reaction":
                value = msg.get("value")
                if value not in ("match", "mismatch"):
                    continue
                manager.add_reaction(room_id, value)
                await manager.broadcast(room_id, {
                    "type": "reaction_update",
                    **manager.get_reactions(room_id),
                })
                asyncio.create_task(_save_reaction(room_id, user_id, value))

            elif msg_type == "next_song":
                if not manager.is_host(room_id, user_id):
                    await websocket.send_text(json.dumps(
                        {"type": "error", "detail": "호스트만 곡을 변경할 수 있습니다."},
                        ensure_ascii=False,
                    ))
                    continue
                asyncio.create_task(_advance_song_ws(room_id))

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        await manager.broadcast(room_id, {
            "type": "state_update",
            "current_song_index": room.current_song_index,
            "viewer_count": manager.viewer_count(room_id),
        })
        logger.info("WS 해제: room=%s user=%s 남은연결=%d", room_id, user_id, manager.viewer_count(room_id))


# ═══════════════════════════════════════════════════════════════
# Background task helpers (WebSocket에서 DB 저장 시 별도 세션 사용)
# ═══════════════════════════════════════════════════════════════

async def _save_chat(room_id: str, user_id: str, message: str):
    async with AsyncSessionLocal() as db:
        db.add(BuskingChatMessage(room_id=room_id, user_id=user_id, message=message))
        await db.commit()


async def _save_reaction(room_id: str, user_id: str, value: str):
    async with AsyncSessionLocal() as db:
        song_idx = (await db.execute(
            select(BuskingRoom.current_song_index).where(BuskingRoom.id == room_id)
        )).scalar_one_or_none()
        db.add(BuskingReaction(
            room_id=room_id, user_id=user_id, value=value, song_index=song_idx
        ))
        await db.commit()


async def _advance_song_ws(room_id: str):
    """WebSocket next_song 처리 — DB 업데이트 후 broadcast."""
    async with AsyncSessionLocal() as db:
        row = await db.execute(select(BuskingRoom).where(BuskingRoom.id == room_id))
        room = row.scalar_one_or_none()
        if not room or room.status != "LIVE":
            return

        setlist_row = await db.execute(
            select(BuskingSetlistItem).where(BuskingSetlistItem.room_id == room_id)
        )
        setlist = setlist_row.scalars().all()
        if room.current_song_index >= len(setlist) - 1:
            return

        room.current_song_index += 1
        await db.commit()

    await manager.broadcast(room_id, {
        "type": "state_update",
        "current_song_index": room.current_song_index,
        "viewer_count": manager.viewer_count(room_id),
    })


# ═══════════════════════════════════════════════════════════════
# Private helpers
# ═══════════════════════════════════════════════════════════════

async def _fetch_user(db: AsyncSession, user_id) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def _get_room_or_404(db: AsyncSession, room_id) -> BuskingRoom:
    result = await db.execute(select(BuskingRoom).where(BuskingRoom.id == room_id))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ROOM_NOT_FOUND", "message": "버스킹 방을 찾을 수 없습니다."},
        )
    return room


async def _get_setlist(db: AsyncSession, room_id) -> list[BuskingSetlistItem]:
    result = await db.execute(
        select(BuskingSetlistItem)
        .where(BuskingSetlistItem.room_id == room_id)
        .order_by(BuskingSetlistItem.order_index)
    )
    return result.scalars().all()


def _require_host(room: BuskingRoom, user: User):
    if str(room.host_id) != str(user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "호스트만 수행할 수 있는 작업입니다."},
        )


def _make_host_profile(user: Optional[User]) -> Optional[HostProfile]:
    if not user:
        return None
    return HostProfile(id=user.id, nickname=user.nickname, profile_img=user.profile_img, bio=user.bio)


def _build_room_response(room: BuskingRoom, viewer_count: int, host: Optional[User] = None) -> BuskingRoomResponse:
    return BuskingRoomResponse(
        id=room.id,
        host_id=room.host_id,
        host_profile=_make_host_profile(host),
        title=room.title,
        thumbnail=room.thumbnail,
        status=room.status,
        current_song_index=room.current_song_index,
        total_viewers=viewer_count,
        peak_viewer_count=room.peak_viewer_count,
        started_at=room.started_at,
        ended_at=room.ended_at,
    )


def _build_room_detail(
    room: BuskingRoom,
    setlist: list[BuskingSetlistItem],
    viewer_count: int,
    host: Optional[User] = None,
) -> BuskingRoomDetailResponse:
    return BuskingRoomDetailResponse(
        id=room.id,
        host_id=room.host_id,
        host_profile=_make_host_profile(host),
        title=room.title,
        thumbnail=room.thumbnail,
        status=room.status,
        current_song_index=room.current_song_index,
        total_viewers=viewer_count,
        peak_viewer_count=room.peak_viewer_count,
        started_at=room.started_at,
        ended_at=room.ended_at,
        setlist=[SetlistItemResponse.model_validate(s) for s in setlist],
    )
