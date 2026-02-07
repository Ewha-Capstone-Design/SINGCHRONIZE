"""네이버 OAuth 제공자 - 실제 API 호출 구현"""
import httpx
from typing import Dict, Any
import logging

from app.services.oauth.base import OAuthProvider, OAuthUserInfo
from app.config import settings

logger = logging.getLogger(__name__)


class NaverOAuthError(Exception):
    """네이버 OAuth 관련 에러"""
    def __init__(self, message: str, details: Dict[str, Any] | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class NaverOAuthProvider(OAuthProvider):
    """
    네이버 OAuth 2.0 구현

    참고: https://developers.naver.com/docs/login/api/
    """

    async def get_access_token(
        self,
        authorization_code: str,
        redirect_uri: str
    ) -> str:
        """
        네이버 인가 코드로 액세스 토큰 획득

        GET/POST https://nid.naver.com/oauth2.0/token

        Args:
            authorization_code: 네이버 인가 코드
            redirect_uri: 리다이렉트 URI (프론트엔드에서 전달받은 값)

        Returns:
            네이버 액세스 토큰

        Raises:
            NaverOAuthError: 토큰 발급 실패
        """
        if not settings.NAVER_CLIENT_ID or not settings.NAVER_CLIENT_SECRET:
            raise NaverOAuthError(
                "네이버 Client ID 또는 Client Secret이 설정되지 않았습니다.",
                {"hint": "환경변수 NAVER_CLIENT_ID, NAVER_CLIENT_SECRET을 설정해주세요."}
            )

        # 네이버는 state 파라미터가 필수이지만, 여기서는 간단히 "STATE" 사용
        # 프로덕션에서는 CSRF 방지를 위해 랜덤 state 생성 및 검증 필요
        params = {
            "grant_type": "authorization_code",
            "client_id": settings.NAVER_CLIENT_ID,
            "client_secret": settings.NAVER_CLIENT_SECRET,
            "code": authorization_code,
            "state": "STATE",  # 프로덕션에서는 세션에 저장한 값과 비교
        }

        try:
            async with httpx.AsyncClient(timeout=settings.OAUTH_API_TIMEOUT) as client:
                # 네이버는 GET 또는 POST 모두 지원
                response = await client.get(
                    settings.NAVER_TOKEN_URL,
                    params=params
                )

                # 네이버 API 에러 처리
                if response.status_code != 200:
                    error_data = response.json() if response.text else {}
                    logger.error(f"네이버 토큰 발급 실패: {response.status_code} - {error_data}")
                    raise NaverOAuthError(
                        "네이버 토큰 발급에 실패했습니다.",
                        {
                            "status_code": response.status_code,
                            "error": error_data.get("error"),
                            "error_description": error_data.get("error_description")
                        }
                    )

                token_data = response.json()

                # 네이버는 에러가 있어도 200을 반환할 수 있음
                if "error" in token_data:
                    logger.error(f"네이버 토큰 발급 실패: {token_data}")
                    raise NaverOAuthError(
                        "네이버 토큰 발급에 실패했습니다.",
                        {
                            "error": token_data.get("error"),
                            "error_description": token_data.get("error_description")
                        }
                    )

                access_token = token_data.get("access_token")

                if not access_token:
                    raise NaverOAuthError(
                        "네이버 응답에 access_token이 없습니다.",
                        {"response": token_data}
                    )

                logger.info("네이버 액세스 토큰 발급 성공")
                return access_token

        except httpx.TimeoutException:
            logger.error("네이버 토큰 API 타임아웃")
            raise NaverOAuthError(
                "네이버 서버 응답 시간이 초과되었습니다.",
                {"timeout": settings.OAUTH_API_TIMEOUT}
            )
        except httpx.RequestError as e:
            logger.error(f"네이버 토큰 API 네트워크 오류: {str(e)}")
            raise NaverOAuthError(
                "네이버 서버와의 통신에 실패했습니다.",
                {"error": str(e)}
            )

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """
        네이버 액세스 토큰으로 사용자 정보 조회

        GET https://openapi.naver.com/v1/nid/me
        Authorization: Bearer {access_token}

        Args:
            access_token: 네이버 액세스 토큰

        Returns:
            OAuthUserInfo: 표준화된 사용자 정보

        Raises:
            NaverOAuthError: 사용자 정보 조회 실패
        """
        try:
            async with httpx.AsyncClient(timeout=settings.OAUTH_API_TIMEOUT) as client:
                response = await client.get(
                    settings.NAVER_USER_INFO_URL,
                    headers={
                        "Authorization": f"Bearer {access_token}"
                    }
                )

                # 네이버 API 에러 처리
                if response.status_code != 200:
                    error_data = response.json() if response.text else {}
                    logger.error(f"네이버 사용자 정보 조회 실패: {response.status_code} - {error_data}")
                    raise NaverOAuthError(
                        "네이버 사용자 정보 조회에 실패했습니다.",
                        {
                            "status_code": response.status_code,
                            "error": error_data.get("message")
                        }
                    )

                user_data = response.json()

                # 네이버 API 응답 구조: { "resultcode": "00", "message": "success", "response": {...} }
                resultcode = user_data.get("resultcode")
                if resultcode != "00":
                    logger.error(f"네이버 사용자 정보 조회 실패: {user_data}")
                    raise NaverOAuthError(
                        "네이버 사용자 정보 조회에 실패했습니다.",
                        {
                            "resultcode": resultcode,
                            "message": user_data.get("message")
                        }
                    )

                response_data = user_data.get("response", {})

                # 필수 필드 추출
                naver_user_id = response_data.get("id")
                if not naver_user_id:
                    raise NaverOAuthError(
                        "네이버 응답에 사용자 ID가 없습니다.",
                        {"response": user_data}
                    )

                # 선택 필드 추출
                email = response_data.get("email")
                nickname = response_data.get("nickname") or response_data.get("name")
                profile_image_url = response_data.get("profile_image")

                logger.info(f"네이버 사용자 정보 조회 성공: user_id={naver_user_id}")

                return OAuthUserInfo(
                    oauth_id=str(naver_user_id),
                    email=email,
                    nickname=nickname,
                    profile_image_url=profile_image_url,
                )

        except httpx.TimeoutException:
            logger.error("네이버 사용자 정보 API 타임아웃")
            raise NaverOAuthError(
                "네이버 서버 응답 시간이 초과되었습니다.",
                {"timeout": settings.OAUTH_API_TIMEOUT}
            )
        except httpx.RequestError as e:
            logger.error(f"네이버 사용자 정보 API 네트워크 오류: {str(e)}")
            raise NaverOAuthError(
                "네이버 서버와의 통신에 실패했습니다.",
                {"error": str(e)}
            )
