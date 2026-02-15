"""OAuth 테스트용 라우터 - 카카오 로그인 리다이렉트 플로우"""
import logging
from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.services.auth_service import AuthService
from app.services.oauth.kakao import KakaoOAuthProvider, KakaoOAuthError

router = APIRouter(prefix="/auth/test", tags=["OAuth Test"])
logger = logging.getLogger(__name__)

REDIRECT_URI = "http://localhost:8000/auth/test/kakao/callback"


@router.get("/kakao/login")
async def kakao_login():
    """카카오 로그인 페이지로 리다이렉트"""
    kakao_auth_url = (
        f"https://kauth.kakao.com/oauth/authorize"
        f"?client_id={settings.KAKAO_REST_API_KEY}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
    )
    return RedirectResponse(url=kakao_auth_url)


@router.get("/kakao/callback")
async def kakao_callback(
    code: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """카카오 콜백 → 인가코드로 토큰 교환 → JWT 발급 → 테스트 페이지로 리다이렉트"""
    try:
        # 1. 인가코드 → 카카오 access_token
        kakao = KakaoOAuthProvider()
        kakao_access_token = await kakao.get_access_token(code, REDIRECT_URI)

        # 2. 카카오 토큰 → 우리 서비스 JWT
        auth = AuthService(db)
        user, access_token, refresh_token, is_new = await auth.social_login(
            provider="kakao",
            access_token=kakao_access_token,
        )

        logger.info(f"테스트 로그인 성공: user={user.id}, new={is_new}")

        # 3. 토큰을 가지고 테스트 페이지로 돌아가기
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html><head><meta charset="UTF-8"><title>로그인 성공</title></head>
        <body style="background:#0f0f0f;color:#e0e0e0;font-family:sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;">
        <div style="text-align:center">
            <h2 style="color:#4caf50">로그인 성공!</h2>
            <p>자동으로 테스트 페이지로 이동합니다...</p>
        </div>
        <script>
            // opener(팝업) 또는 부모 창에 토큰 전달
            const token = "{access_token}";
            if (window.opener) {{
                window.opener.postMessage({{ type: 'KAKAO_LOGIN', token }}, '*');
                window.close();
            }} else {{
                // 직접 리다이렉트된 경우 localStorage에 저장 후 테스트 페이지로
                localStorage.setItem('singchronize_jwt', token);
                window.location.href = '/test_page.html';
            }}
        </script>
        </body></html>
        """)

    except KakaoOAuthError as e:
        logger.error(f"카카오 OAuth 에러: {e.message}")
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html><head><meta charset="UTF-8"><title>로그인 실패</title></head>
        <body style="background:#0f0f0f;color:#e0e0e0;font-family:sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;">
        <div style="text-align:center">
            <h2 style="color:#f44336">로그인 실패</h2>
            <p>{e.message}</p>
            <button onclick="window.close()" style="padding:10px 20px;border:none;border-radius:6px;background:#bb86fc;color:#000;cursor:pointer;margin-top:16px;">닫기</button>
        </div>
        </body></html>
        """, status_code=401)
