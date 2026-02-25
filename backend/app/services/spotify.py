import base64
import requests

class SpotifyService:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None

    def get_token(self):
        """스포티파이로부터 1시간짜리 Access Token을 받아옵니다."""
        # Client ID와 Secret을 결합하여 Base64로 인코딩 (OAuth2 규격)
        auth_str = f"{self.client_id}:{self.client_secret}"
        auth_base64 = base64.b64encode(auth_str.encode()).decode()

        url = "https://accounts.spotify.com/api/token"
        headers = {
            "Authorization": f"Basic {auth_base64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "client_credentials"}
        
        try:
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status() # 에러 발생 시 예외 처리
            
            self.access_token = response.json()["access_token"]
            return self.access_token
        except Exception as e:
            print(f"❌ 토큰 발급 실패: {e}")
            return None

    def search_tracks(self, query: str):
        """노래 제목으로 검색하여 결과를 반환합니다."""
        # 토큰이 없으면 새로 받아오기
        if not self.access_token:
            self.get_token()

        url = "https://api.spotify.com/v1/search"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        # q: 검색어, type: 트랙(노래), limit: 10개, market: 한국 기준
        params = {"q": query, "type": "track", "limit": 10, "market": "KR"}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            
            # 만약 토큰이 만료되어 401 에러가 나면 갱신 후 재시도
            if response.status_code == 401:
                self.get_token()
                headers["Authorization"] = f"Bearer {self.access_token}"
                response = requests.get(url, headers=headers, params=params)
                
            return response.json()
        except Exception as e:
            print(f"❌ 검색 실패: {e}")
            return {"error": str(e)}