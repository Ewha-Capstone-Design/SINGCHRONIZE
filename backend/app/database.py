"""비동기 데이터베이스 설정 (SQLite / PostgreSQL 자동 감지 + Supabase 최적화)"""
import ssl as _ssl_module
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator

from app.config import settings

Base = declarative_base()

# 1. DB URL 가져오기
_db_url = settings.DATABASE_URL

# 2. PostgreSQL인 경우, 비동기 드라이버(asyncpg)가 명시되어야 함
# .env에 "postgresql://"로 적혀있어도 자동으로 변환해주는 안전장치입니다.
if _db_url and _db_url.startswith("postgresql://"):
    _db_url = _db_url.replace("postgresql://", "postgresql+asyncpg://")

# asyncpg는 sslmode 파라미터를 인식하지 못하므로 URL에서 제거
if "sslmode=" in _db_url:
    _db_url = _db_url.split("?sslmode=")[0] if "?sslmode=" in _db_url else _db_url.replace("&sslmode=require", "")

_is_sqlite = _db_url.startswith("sqlite")

_engine_kwargs = {
    "echo": True,  # 개발 중에는 SQL 로그를 보는 게 좋습니다 (배포 시 False)
}

if _is_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Supabase 등 클라우드 DB 사용 시 필수 설정
    _engine_kwargs["pool_size"] = 10
    _engine_kwargs["max_overflow"] = 20
    _engine_kwargs["pool_pre_ping"] = True  # 연결이 끊겼을 때 자동으로 재연결 (중요!)
    # asyncpg SSL 설정: Supabase는 SSL 필수
    _ssl_ctx = _ssl_module.create_default_context()
    _ssl_ctx.check_hostname = False
    _ssl_ctx.verify_mode = _ssl_module.CERT_NONE
    _engine_kwargs["connect_args"] = {
        "ssl": _ssl_ctx,
        "command_timeout": 60,
        "prepared_statement_cache_size": 0, # 드라이버 직접 설정
    }

# 3. 엔진 생성
engine = create_async_engine(_db_url, **_engine_kwargs)

# 4. 세션 생성기
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 5. 의존성 주입용 함수 (FastAPI에서 Depends로 사용)
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

# 6. 테이블 초기화 (테스트용)
async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)