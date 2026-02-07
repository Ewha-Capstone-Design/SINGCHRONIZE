"""애플리케이션 설정 관리"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """환경 변수 기반 설정"""

    # Database (PostgreSQL)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/singchronize"

    # JWT
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
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

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


settings = Settings()
