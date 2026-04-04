"""애플리케이션 설정 관리"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """환경 변수 기반 설정"""

    # Database (PostgreSQL)
    # .env의 DATABASE_URL을 읽어옵니다. (postgresql+asyncpg://... 형태)
    DATABASE_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # API Timeout (초)
    OAUTH_API_TIMEOUT: int = 10

    # OAuth Kakao
    KAKAO_REST_API_KEY: str = ""
    KAKAO_CLIENT_SECRET: str = ""
    KAKAO_TOKEN_URL: str = "https://kauth.kakao.com/oauth/token"
    KAKAO_USER_INFO_URL: str = "https://kapi.kakao.com/v2/user/me"

    # OAuth Naver
    NAVER_CLIENT_ID: str = ""
    NAVER_CLIENT_SECRET: str = ""
    NAVER_TOKEN_URL: str = "https://nid.naver.com/oauth2.0/token"
    NAVER_USER_INFO_URL: str = "https://openapi.naver.com/v1/nid/me"

    # Spotify
    SPOTIFY_CLIENT_ID: str = ""
    SPOTIFY_CLIENT_SECRET: str = ""

    # Last.fm
    LASTFM_API_KEY: str = ""

    # OpenAI
    OPENAI_API_KEY: str = ""

    # Gemini
    GEMINI_API_KEY: str = ""
    
    # AWS
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = ""
    SQS_QUEUE_URL: str = ""
    S3_BUCKET_NAME: str = ""
    
    
    # 추가 설정 (필요시)
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    YOUTUBE_API_KEY: str = ""

    # LiveKit Cloud
    LIVEKIT_URL: str = ""          # wss://your-project.livekit.cloud
    LIVEKIT_API_KEY: str = ""
    LIVEKIT_API_SECRET: str = ""

    # SQS — 보컬 분석 전용 큐 (AI 워커: vocal_analysis_worker)
    VOCAL_ANALYSIS_SQS_QUEUE_URL: str = ""

    # 3차 협업 필터링 (ECS stage3-api, ALB URL 등 — 비우면 API에서 unconfigured)
    STAGE3_API_BASE_URL: str = ""
    STAGE3_API_TIMEOUT_SECONDS: float = 2.0

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


settings = Settings()