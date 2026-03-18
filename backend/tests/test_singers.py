"""SingerService 단위 테스트

실행:
    pip install pytest pytest-asyncio
    pytest backend/tests/test_singers.py -v
"""
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from app.services.singer_service import SingerService
from app.models.singer import Singer, BlockedSinger


# ─── Fixtures ────────────────────────────────────────────────────────────────

def make_singer(singer_id: int, name: str, gender: str = "female") -> Singer:
    s = Singer()
    s.singer_id = singer_id
    s.name = name
    s.gender = gender
    s.photo_url = f"https://example.com/{singer_id}.jpg"
    return s


def make_blocked(block_id: int, user_id: UUID, singer: Singer) -> BlockedSinger:
    b = BlockedSinger()
    b.block_id = block_id
    b.user_id = user_id
    b.singer_id = singer.singer_id
    b.singer = singer
    b.created_at = datetime(2026, 1, 1, 0, 0, 0)
    return b


def mock_db() -> AsyncMock:
    db = AsyncMock()
    db.add = MagicMock()
    db.delete = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    return db


# ─── [1] get_random_singers ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_random_singers_returns_singers():
    """정상 요청 시 Singer 목록 반환"""
    user_id = uuid.uuid4()
    db = mock_db()
    singers = [make_singer(1, "아이유"), make_singer(2, "태연")]

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = singers
    db.execute = AsyncMock(return_value=mock_result)

    service = SingerService(db)
    result = await service.get_random_singers(user_id, "female", 6)

    assert result == singers
    db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_random_singers_invalid_gender_raises_400():
    """gender가 male/female이 아니면 400"""
    from fastapi import HTTPException

    user_id = uuid.uuid4()
    db = mock_db()
    service = SingerService(db)

    with pytest.raises(HTTPException) as exc_info:
        await service.get_random_singers(user_id, "unknown", 6)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["code"] == "INVALID_GENDER"


@pytest.mark.asyncio
async def test_get_random_singers_empty_result():
    """결과가 없을 때 빈 리스트 반환"""
    user_id = uuid.uuid4()
    db = mock_db()

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=mock_result)

    service = SingerService(db)
    result = await service.get_random_singers(user_id, "male", 6)

    assert result == []


# ─── [2] block_singer ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_block_singer_success():
    """정상 차단 등록"""
    user_id = uuid.uuid4()
    singer = make_singer(3, "박효신", "male")
    blocked = make_blocked(10, user_id, singer)

    db = mock_db()
    # 첫 번째 execute: 가수 존재 확인 → 반환
    singer_result = MagicMock()
    singer_result.scalar_one_or_none.return_value = singer
    # 두 번째 execute: 중복 차단 확인 → None (차단 없음)
    dup_result = MagicMock()
    dup_result.scalar_one_or_none.return_value = None

    db.execute = AsyncMock(side_effect=[singer_result, dup_result])
    db.refresh = AsyncMock(side_effect=lambda obj: setattr(obj, "block_id", 10) or setattr(obj, "created_at", datetime(2026, 1, 1)))

    service = SingerService(db)
    result = await service.block_singer(user_id, 3)

    db.add.assert_called_once()
    db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_block_singer_not_found_raises_404():
    """존재하지 않는 가수 차단 시 404"""
    from fastapi import HTTPException

    user_id = uuid.uuid4()
    db = mock_db()

    singer_result = MagicMock()
    singer_result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=singer_result)

    service = SingerService(db)

    with pytest.raises(HTTPException) as exc_info:
        await service.block_singer(user_id, 999)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail["code"] == "SINGER_NOT_FOUND"


@pytest.mark.asyncio
async def test_block_singer_duplicate_raises_409():
    """이미 차단된 가수 재차단 시 409"""
    from fastapi import HTTPException

    user_id = uuid.uuid4()
    singer = make_singer(3, "박효신", "male")
    existing_block = make_blocked(5, user_id, singer)

    db = mock_db()
    singer_result = MagicMock()
    singer_result.scalar_one_or_none.return_value = singer
    dup_result = MagicMock()
    dup_result.scalar_one_or_none.return_value = existing_block
    db.execute = AsyncMock(side_effect=[singer_result, dup_result])

    service = SingerService(db)

    with pytest.raises(HTTPException) as exc_info:
        await service.block_singer(user_id, 3)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["code"] == "ALREADY_BLOCKED"


# ─── [3] get_blocked_singers ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_blocked_singers_returns_list():
    """차단 가수 목록 반환"""
    user_id = uuid.uuid4()
    singer = make_singer(3, "아이유")
    blocked = make_blocked(1, user_id, singer)

    db = mock_db()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [blocked]
    db.execute = AsyncMock(return_value=mock_result)

    service = SingerService(db)
    result = await service.get_blocked_singers(user_id)

    assert len(result) == 1
    assert result[0].singer.name == "아이유"


# ─── [4] unblock_singer ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_unblock_singer_success():
    """본인 차단 해제 성공"""
    user_id = uuid.uuid4()
    singer = make_singer(3, "아이유")
    blocked = make_blocked(1, user_id, singer)

    db = mock_db()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = blocked
    db.execute = AsyncMock(return_value=mock_result)

    service = SingerService(db)
    await service.unblock_singer(user_id, 1)

    db.delete.assert_called_once_with(blocked)


@pytest.mark.asyncio
async def test_unblock_singer_not_found_raises_404():
    """존재하지 않는 차단 해제 시 404"""
    from fastapi import HTTPException

    user_id = uuid.uuid4()
    db = mock_db()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=mock_result)

    service = SingerService(db)

    with pytest.raises(HTTPException) as exc_info:
        await service.unblock_singer(user_id, 999)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail["code"] == "BLOCK_NOT_FOUND"


@pytest.mark.asyncio
async def test_unblock_singer_other_user_raises_403():
    """타인의 차단 기록 삭제 시 403"""
    from fastapi import HTTPException

    user_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    singer = make_singer(3, "아이유")
    blocked = make_blocked(1, other_user_id, singer)  # 다른 유저의 차단

    db = mock_db()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = blocked
    db.execute = AsyncMock(return_value=mock_result)

    service = SingerService(db)

    with pytest.raises(HTTPException) as exc_info:
        await service.unblock_singer(user_id, 1)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["code"] == "FORBIDDEN"
