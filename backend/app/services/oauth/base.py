"""OAuth 제공자 기본 인터페이스"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class OAuthUserInfo:
    """OAuth 사용자 정보 표준 포맷"""

    def __init__(
        self,
        oauth_id: str,
        email: str | None = None,
        nickname: str | None = None,
        profile_image_url: str | None = None,
    ):
        self.oauth_id = oauth_id
        self.email = email
        self.nickname = nickname
        self.profile_image_url = profile_image_url


class OAuthProvider(ABC):
    """OAuth 제공자 추상 클래스"""

    @abstractmethod
    async def get_access_token(
        self,
        authorization_code: str,
        redirect_uri: str
    ) -> str:
        """인가 코드로 액세스 토큰 획득"""
        pass

    @abstractmethod
    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """액세스 토큰으로 사용자 정보 조회"""
        pass

    async def login(
        self,
        authorization_code: str,
        redirect_uri: str
    ) -> OAuthUserInfo:
        """OAuth 로그인 플로우 (코드 → 토큰 → 사용자 정보)"""
        access_token = await self.get_access_token(authorization_code, redirect_uri)
        user_info = await self.get_user_info(access_token)
        return user_info
