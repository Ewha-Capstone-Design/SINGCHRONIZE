"""OAuth 제공자 팩토리"""
from app.services.oauth.base import OAuthProvider
from app.services.oauth.kakao import KakaoOAuthProvider
from app.services.oauth.naver import NaverOAuthProvider


def get_oauth_provider(provider: str) -> OAuthProvider:
    """OAuth 제공자 팩토리"""
    providers = {
        "kakao": KakaoOAuthProvider(),
        "naver": NaverOAuthProvider(),
    }

    if provider not in providers:
        raise ValueError(f"지원하지 않는 OAuth 제공자입니다: {provider}")

    return providers[provider]


__all__ = ["get_oauth_provider", "OAuthProvider"]
