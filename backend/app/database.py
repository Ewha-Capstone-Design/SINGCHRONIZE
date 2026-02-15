"""비동기 데이터베이스 설정 (Supabase/PostgreSQL 최적화)"""
import ssl
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator

from app.config import settings

Base = declarative_base()

# 1. DB URL 가져오기 및 가공
_db_url = settings.DATABASE_URL

# postgresql:// -> postgresql+asyncpg:// 변환
if _db_url and _db_url.startswith("postgresql://"):
    _db_url = _db_url.replace("postgresql://", "postgresql+asyncpg://")

# URL 뒤에 붙은 잡다한 파라미터제거 (connect_args로 제어하기 위함)
if "?" in _db_url:
    _db_url = _db_url.split("?")[0]

print(f"🔥 [DB 연결 설정] URL: {_db_url}")

# 2. SSL 컨텍스트 생성 (Supabase 필수)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# 3. 엔진 생성 (변수 쓰지 않고 직접 주입)
# 이렇게 하면 설정이 무시될 수가 없습니다.
engine = create_async_engine(
    _db_url,
    echo=True,           # 쿼리 로그 출력
    pool_size=10,        # 커넥션 풀 크기
    max_overflow=20,     # 최대 허용 오버플로우
    pool_pre_ping=True,  # 연결 끊김 자동 복구
    connect_args={
        "ssl": ssl_context,
        "server_settings": {
            "jit": "off",  # JIT 컴파일 끄기 (성능 최적화)
        },
        # ⭐ 여기가 핵심입니다. 캐시를 0으로 설정해서 에러 원천 차단 ⭐
        "statement_cache_size": 0,
        "command_timeout": 60,
    }
)

# 4. 세션 생성기
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# 5. 의존성 주입 (Dependency)
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