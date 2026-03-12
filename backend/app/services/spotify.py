import base64
import logging
import httpx

logger = logging.getLogger(__name__)


class SpotifyService:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token: str | None = None

    async def _get_token(self, client: httpx.AsyncClient) -> None:
        """스포티파이로부터 1시간짜리 Access Token을 받아옵니다."""
        auth_str = f"{self.client_id}:{self.client_secret}"
        auth_base64 = base64.b64encode(auth_str.encode()).decode()

        response = await client.post(
            "https://accounts.spotify.com/api/token",
            headers={
                "Authorization": f"Basic {auth_base64}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "client_credentials"},
        )
        response.raise_for_status()
        self.access_token = response.json()["access_token"]

    async def search_tracks(self, query: str) -> dict:
        """노래 제목으로 검색하여 결과를 반환합니다."""
        async with httpx.AsyncClient() as client:
            if not self.access_token:
                await self._get_token(client)

            params = {"q": query, "type": "track", "limit": 10, "market": "KR"}
            headers = {"Authorization": f"Bearer {self.access_token}"}

            response = await client.get(
                "https://api.spotify.com/v1/search",
                headers=headers,
                params=params,
            )

            # 토큰 만료 시 갱신 후 재시도
            if response.status_code == 401:
                await self._get_token(client)
                headers["Authorization"] = f"Bearer {self.access_token}"
                response = await client.get(
                    "https://api.spotify.com/v1/search",
                    headers=headers,
                    params=params,
                )

            response.raise_for_status()
            return response.json()
