"""유저 서비스 - 프로필 조회/수정, 설정 JSONB 머지, SNS 연동"""
import uuid
from dataclasses import dataclass, field
from typing import List

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.exc import IntegrityError

from app.models.singer import BlockedSinger, BlockedSong, FavoriteSinger, Singer
from app.models.song import Song
from app.models.user import User


@dataclass
class FullProfile:
    user: User
    favorite_singers: List[Singer] = field(default_factory=list)
    blocked_singers: List[Singer] = field(default_factory=list)
    blocked_songs: List[dict] = field(default_factory=list)


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user(self, user_id: uuid.UUID) -> User:
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다.")
        return user

    async def get_full_profile(self, user_id: uuid.UUID) -> FullProfile:
        """마이페이지 전용: 유저 정보 + 선호 가수 + 차단 가수 한 번에 조회"""
        user = await self.get_user(user_id)

        fav_result = await self.db.execute(
            select(Singer)
            .join(FavoriteSinger, FavoriteSinger.singer_id == Singer.singer_id)
            .where(FavoriteSinger.user_id == user_id)
            .order_by(Singer.name)
        )
        blocked_result = await self.db.execute(
            select(Singer)
            .join(BlockedSinger, BlockedSinger.singer_id == Singer.singer_id)
            .where(BlockedSinger.user_id == user_id)
            .order_by(Singer.name)
        )
        blocked_songs_result = await self.db.execute(
            select(BlockedSong, Song)
            .join(Song, Song.id == BlockedSong.song_id)
            .where(BlockedSong.user_id == user_id)
            .order_by(BlockedSong.created_at.desc())
        )
        blocked_songs = [
            {
                "block_id": bs.block_id,
                "song_id": song.id,
                "title": song.title,
                "artist": song.artist,
                "album_cover": song.album_cover,
                "created_at": bs.created_at,
            }
            for bs, song in blocked_songs_result.all()
        ]

        return FullProfile(
            user=user,
            favorite_singers=list(fav_result.scalars().all()),
            blocked_singers=list(blocked_result.scalars().all()),
            blocked_songs=blocked_songs,
        )

    def get_linked_providers(self, user: User) -> List[str]:
        """연동된 SNS 프로바이더 목록 반환 (primary 포함)"""
        providers = [user.provider]
        if user.provider != "kakao" and user.kakao_id:
            providers.append("kakao")
        if user.provider != "naver" and user.naver_id:
            providers.append("naver")
        return providers

    async def update_profile(
        self,
        user_id: uuid.UUID,
        nickname: str | None = None,
    ) -> User:
        user = await self.get_user(user_id)
        if nickname is not None:
            user.nickname = nickname
        await self.db.flush()
        return user

    async def setup_onboarding_step1(
        self,
        user_id: uuid.UUID,
        nickname: str,
        profile_img_url: str | None = None,
    ) -> User:
        """온보딩 1단계: 닉네임 + 프로필 사진 저장 후 완료 상태 반영"""
        user = await self.get_user(user_id)
        user.nickname = nickname
        if profile_img_url is not None:
            user.profile_img = profile_img_url
        settings_data = dict(user.settings or {})
        settings_data["onboarding_step"] = 1
        user.settings = settings_data
        await self.db.flush()
        return user

    async def update_mypage_profile(
        self,
        user_id: uuid.UUID,
        nickname: str | None,
        bio: str | None,
        profile_img_url: str | None = None,
        _nickname_provided: bool = False,
        _bio_provided: bool = False,
    ) -> User:
        """마이페이지 프로필 수정: 닉네임 + 소개글 + 프로필 사진 부분 업데이트"""
        user = await self.get_user(user_id)
        if _nickname_provided:
            stripped = nickname.strip() if nickname else ""
            if not stripped:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={"code": "INVALID_NICKNAME", "message": "닉네임은 공백만으로 구성될 수 없습니다."},
                )
            user.nickname = stripped
        if profile_img_url is not None:
            user.profile_img = profile_img_url
        if _bio_provided:
            user.bio = bio.strip() if bio and bio.strip() else None
        await self.db.flush()
        return user

    # ─── SNS 연동 관리 ────────────────────────────────

    async def link_account(
        self, user_id: uuid.UUID, provider: str, provider_id: str
    ) -> User:
        """SNS 계정 추가 연동 - users 테이블 kakao_id / naver_id 업데이트"""
        user = await self.get_user(user_id)

        if user.provider == provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "PRIMARY_PROVIDER", "message": f"{provider}는 이미 기본 로그인 계정입니다."},
            )

        id_col = f"{provider}_id"
        if getattr(user, id_col) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "ALREADY_LINKED", "message": f"이미 {provider} 계정이 연동되어 있습니다."},
            )

        # 해당 provider_id가 다른 유저에게 사용 중인지 확인
        conflict = await self.db.execute(
            select(User).where(getattr(User, id_col) == provider_id)
        )
        if conflict.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "PROVIDER_ID_TAKEN", "message": "해당 SNS 계정은 이미 다른 유저에게 연동되어 있습니다."},
            )

        setattr(user, id_col, provider_id)
        await self.db.flush()
        return user

    async def unlink_account(self, user_id: uuid.UUID, provider: str) -> User:
        """SNS 계정 연동 해제"""
        user = await self.get_user(user_id)
        id_col = f"{provider}_id"

        if getattr(user, id_col) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "LINKED_ACCOUNT_NOT_FOUND", "message": f"연동된 {provider} 계정이 없습니다."},
            )

        setattr(user, id_col, None)
        await self.db.flush()
        return user

    # ─── 가수 차단 관리 ───────────────────────────────

    async def get_blocked_singers(self, user_id: uuid.UUID) -> list[dict]:
        """차단한 가수 목록 조회 (block_id, singer_id, name, photo_url, created_at)"""
        result = await self.db.execute(
            select(BlockedSinger, Singer)
            .join(Singer, Singer.singer_id == BlockedSinger.singer_id)
            .where(BlockedSinger.user_id == user_id)
            .order_by(BlockedSinger.created_at.desc())
        )
        return [
            {
                "block_id": blocked.block_id,
                "singer_id": singer.singer_id,
                "name": singer.name,
                "photo_url": singer.photo_url,
                "created_at": blocked.created_at,
            }
            for blocked, singer in result.all()
        ]

    async def block_singer(self, user_id: uuid.UUID, singer_id: int) -> dict:
        """가수 차단. 이미 차단된 경우 409, 없는 가수 404."""
        singer = await self.db.get(Singer, singer_id)
        if not singer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "SINGER_NOT_FOUND", "message": "존재하지 않는 가수입니다."},
            )

        record = BlockedSinger(user_id=user_id, singer_id=singer_id)
        self.db.add(record)
        try:
            await self.db.flush()
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "ALREADY_BLOCKED", "message": "이미 차단한 가수입니다."},
            )
        return {
            "block_id": record.block_id,
            "singer_id": singer.singer_id,
            "name": singer.name,
            "photo_url": singer.photo_url,
            "created_at": record.created_at,
        }

    async def unblock_singer(self, user_id: uuid.UUID, singer_id: int) -> None:
        """가수 차단 해제. 차단 내역이 없으면 404."""
        result = await self.db.execute(
            select(BlockedSinger).where(
                BlockedSinger.user_id == user_id,
                BlockedSinger.singer_id == singer_id,
            )
        )
        record = result.scalar_one_or_none()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BLOCK_NOT_FOUND", "message": "차단 내역이 없습니다."},
            )
        await self.db.delete(record)
        await self.db.flush()

    # ─── 곡 차단 관리 ─────────────────────────────────

    async def get_blocked_songs(self, user_id: uuid.UUID) -> list[dict]:
        """차단한 곡 목록 조회 (block_id, song_id, title, artist, album_cover, created_at)"""
        result = await self.db.execute(
            select(BlockedSong, Song)
            .join(Song, Song.id == BlockedSong.song_id)
            .where(BlockedSong.user_id == user_id)
            .order_by(BlockedSong.created_at.desc())
        )
        return [
            {
                "block_id": blocked.block_id,
                "song_id": song.id,
                "title": song.title,
                "artist": song.artist,
                "album_cover": song.album_cover,
                "created_at": blocked.created_at,
            }
            for blocked, song in result.all()
        ]

    async def block_song(self, user_id: uuid.UUID, song_id: uuid.UUID) -> dict:
        """곡 차단. 없는 곡이면 404, 이미 차단이면 409."""
        song = await self.db.get(Song, song_id)
        if not song:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "SONG_NOT_FOUND", "message": "존재하지 않는 곡입니다."},
            )

        record = BlockedSong(user_id=user_id, song_id=song_id)
        self.db.add(record)
        try:
            await self.db.flush()
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "ALREADY_BLOCKED", "message": "이미 차단한 곡입니다."},
            )
        return {
            "block_id": record.block_id,
            "song_id": song.id,
            "title": song.title,
            "artist": song.artist,
            "album_cover": song.album_cover,
            "created_at": record.created_at,
        }

    async def unblock_song(self, user_id: uuid.UUID, song_id: uuid.UUID) -> None:
        """곡 차단 해제. 차단 내역이 없으면 404."""
        result = await self.db.execute(
            select(BlockedSong).where(
                BlockedSong.user_id == user_id,
                BlockedSong.song_id == song_id,
            )
        )
        record = result.scalar_one_or_none()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BLOCK_NOT_FOUND", "message": "차단 내역이 없습니다."},
            )
        await self.db.delete(record)
        await self.db.flush()

    async def update_settings(
        self,
        user_id: uuid.UUID,
        update_data: dict,
    ) -> dict:
        """JSONB 부분 업데이트: 전달된 키만 머지."""
        user = await self.get_user(user_id)
        current = dict(user.settings or {})
        current.update(update_data)
        user.settings = current
        await self.db.flush()
        return user.settings
