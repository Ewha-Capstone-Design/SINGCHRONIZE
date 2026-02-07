"""카카오 OAuth 제공자 - 실제 API 호출 구현"""
import httpx
from typing import Dict, Any
import logging

from app.services.oauth.base import OAuthProvider, OAuthUserInfo
from app.config import settings

logger = logging.getLogger(__name__)


class KakaoOAuthError(Exception):
    """카카오 OAuth 관련 에러"""
    def __init__(self, message: str, details: Dict[str, Any] | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class KakaoOAuthProvider(OAuthProvider):
    """
    카카오 OAuth 2.0 구현

    참고: https://developers.kakao.com/docs/latest/ko/kakaologin/rest-api
    """

    async def get_access_token(
        self,
        authorization_code: str,
        redirect_uri: str
    ) -> str:
        """
        카카오 인가 코드로 액세스 토큰 획득

        POST https://kauth.kakao.com/oauth/token
        Content-Type: application/x-www-form-urlencoded;charset=utf-8

        Args:
            authorization_code: 카카오 인가 코드
            redirect_uri: 리다이렉트 URI (프론트엔드에서 전달받은 값)

        Returns:
            카카오 액세스 토큰

        Raises:
            KakaoOAuthError: 토큰 발급 실패
        """
        if not settings.KAKAO_REST_API_KEY:
            raise KakaoOAuthError(
                "카카오 REST API 키가 설정되지 않았습니다.",
                {"hint": "환경변수 KAKAO_REST_API_KEY를 설정해주세요."}
            )

        # 요청 데이터 구성
        data = {
            "grant_type": "authorization_code",
            "client_id": settings.KAKAO_REST_API_KEY,
            "redirect_uri": redirect_uri,
            "code": authorization_code,
        }

        # Client Secret이 있으면 추가 (보안 강화 옵션)
        if settings.KAKAO_CLIENT_SECRET:
            data["client_secret"] = settings.KAKAO_CLIENT_SECRET

        try:
            async with httpx.AsyncClient(timeout=settings.OAUTH_API_TIMEOUT) as client:
                response = await client.post(
                    settings.KAKAO_TOKEN_URL,
                    data=data,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"
                    }
                )

                # 카카오 API 에러 처리
                if response.status_code != 200:
                    error_data = response.json() if response.text else {}
                    logger.error(f"카카오 토큰 발급 실패: {response.status_code} - {error_data}")
                    raise KakaoOAuthError(
                        "카카오 토큰 발급에 실패했습니다.",
                        {
                            "status_code": response.status_code,
                            "error": error_data.get("error"),
                            "error_description": error_data.get("error_description")
                        }
                    )

                token_data = response.json()
                access_token = token_data.get("access_token")

                if not access_token:
                    raise KakaoOAuthError(
                        "카카오 응답에 access_token이 없습니다.",
                        {"response": token_data}
                    )

                logger.info("카카오 액세스 토큰 발급 성공")
                return access_token

        except httpx.TimeoutException:
            logger.error("카카오 토큰 API 타임아웃")
            raise KakaoOAuthError(
                "카카오 서버 응답 시간이 초과되었습니다.",
                {"timeout": settings.OAUTH_API_TIMEOUT}
            )
        except httpx.RequestError as e:
            logger.error(f"카카오 토큰 API 네트워크 오류: {str(e)}")
            raise KakaoOAuthError(
                "카카오 서버와의 통신에 실패했습니다.",
                {"error": str(e)}
            )

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """
        카카오 액세스 토큰으로 사용자 정보 조회

        GET/POST https://kapi.kakao.com/v2/user/me
        Authorization: Bearer {access_token}

        Args:
            access_token: 카카오 액세스 토큰

        Returns:
            OAuthUserInfo: 표준화된 사용자 정보

        Raises:
            KakaoOAuthError: 사용자 정보 조회 실패
        """
        try:
            async with httpx.AsyncClient(timeout=settings.OAUTH_API_TIMEOUT) as client:
                response = await client.get(
                    settings.KAKAO_USER_INFO_URL,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"
                    }
                )

                # 카카오 API 에러 처리
                if response.status_code != 200:
                    error_data = response.json() if response.text else {}
                    logger.error(f"카카오 사용자 정보 조회 실패: {response.status_code} - {error_data}")
                    raise KakaoOAuthError(
                        "카카오 사용자 정보 조회에 실패했습니다.",
                        {
                            "status_code": response.status_code,
                            "error": error_data.get("msg"),
                            "code": error_data.get("code")
                        }
                    )

                user_data = response.json()

                # 필수 필드 추출
                kakao_user_id = user_data.get("id")
                if not kakao_user_id:
                    raise KakaoOAuthError(
                        "카카오 응답에 사용자 ID가 없습니다.",
                        {"response": user_data}
                    )

                # 선택 필드 추출 (동의 항목에 따라 없을 수 있음)
                kakao_account = user_data.get("kakao_account", {})
                profile = kakao_account.get("profile", {})

                email = kakao_account.get("email")
                nickname = profile.get("nickname")
                profile_image_url = profile.get("profile_image_url") or profile.get("thumbnail_image_url")

                logger.info(f"카카오 사용자 정보 조회 성공: user_id={kakao_user_id}")

                return OAuthUserInfo(
                    oauth_id=str(kakao_user_id),
                    email=email,
                    nickname=nickname,
                    profile_image_url=profile_image_url,
                )

        except httpx.TimeoutException:
            logger.error("카카오 사용자 정보 API 타임아웃")
            raise KakaoOAuthError(
                "카카오 서버 응답 시간이 초과되었습니다.",
                {"timeout": settings.OAUTH_API_TIMEOUT}
            )
        except httpx.RequestError as e:
            logger.error(f"카카오 사용자 정보 API 네트워크 오류: {str(e)}")
            raise KakaoOAuthError(
                "카카오 서버와의 통신에 실패했습니다.",
                {"error": str(e)}
            )