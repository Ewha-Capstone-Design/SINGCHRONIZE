"""버스킹 라우터 - 방 생성/조회"""
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import logging

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.busking import BuskingRoom
from app.schemas.busking import BuskingRoomCreate, BuskingRoomResponse

router = APIRouter(prefix="/api/v1/busking", tags=["Busking"])
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1. 연결 관리자 (누가 들어왔는지 관리하고, 채팅/노래를 뿌려주는 역할)
class ConnectionManager:
    def __init__(self):
        # 방 ID별로 유저들을 저장함: { "room_1": [user1, user2], "room_2": [user3] }
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast(self, message: str, room_id: str):
        # 같은 방에 있는 사람들에게만 메시지 전송
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                await connection.send_text(message)

manager = ConnectionManager()

@router.post("/rooms", response_model=BuskingRoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    room_data: BuskingRoomCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    print(">>> create_room entered")
    """버스킹 방 생성 (로그인 필수)"""
    logger.info(f"방 생성 요청: user={current_user.id}, title={room_data.title}")

    try:
        new_room = BuskingRoom(
            host_id=current_user.id,
            title=room_data.title,
            thumbnail=room_data.thumbnail,
            status="PREPARING",
        )

        db.add(new_room)
        await db.flush()
        await db.refresh(new_room)

        logger.info(f"방 생성 완료: room={new_room.id}")
        return new_room

    except Exception as e:
        logger.error(f"방 생성 실패: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"방 생성 실패: {str(e)}")


@router.get("/rooms", response_model=List[BuskingRoomResponse])
async def get_rooms(db: AsyncSession = Depends(get_db)):
    """현재 라이브 중이거나 준비 중인 방 목록 조회"""
    logger.info("방 목록 조회 요청")

    try:
        result = await db.execute(
            select(BuskingRoom)
            .where(BuskingRoom.status.in_(["PREPARING", "LIVE"]))
            .order_by(BuskingRoom.created_at.desc())
        )
        rooms = result.scalars().all()

        logger.info(f"방 목록 조회 완료: {len(rooms)}개")
        return rooms

    except Exception as e:
        logger.error(f"방 목록 조회 실패: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"방 목록 조회 실패: {str(e)}")

# 웹소켓 엔드포인트 (ws://localhost:8000/api/v1/busking/ws/{room_id})
@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await manager.connect(websocket, room_id)
    try:
        while True:
            # 클라이언트(프론트)에서 보낸 메시지 받기
            data = await websocket.receive_text()
            
            # 같은 방 사람들에게 뿌리기 (채팅 or 노래 데이터)
            await manager.broadcast(f"유저: {data}", room_id)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        await manager.broadcast("누군가 나갔습니다.", room_id)
        
# 🎵 노래 데이터 전송용 매니저 (바이너리 처리)
class AudioManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast(self, data: bytes, room_id: str, sender: WebSocket):
        # 보낸 사람(가수)을 제외한 나머지(관객)에게만 소리 전송
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                if connection != sender: # 내 목소리가 나한테 다시 들리면 안 되니까!
                    await connection.send_bytes(data)

audio_manager = AudioManager()

# 🎤 오디오 스트리밍 엔드포인트
@router.websocket("/ws/audio/{room_id}")
async def audio_endpoint(websocket: WebSocket, room_id: str):
    await audio_manager.connect(websocket, room_id)
    try:
        while True:
            # 1. 가수한테서 노래 데이터(bytes)를 받음
            data = await websocket.receive_bytes()
            
            # 2. 관객들에게 뿌림
            await audio_manager.broadcast(data, room_id, websocket)
            
    except WebSocketDisconnect:
        audio_manager.disconnect(websocket, room_id)