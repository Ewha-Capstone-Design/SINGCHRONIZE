"""OAuth 테스트용 라우터 — 카카오/네이버 로그인 리다이렉트 플로우 (어드민 페이지 전용)"""
import json
import logging

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.services.auth_service import AuthService
from app.services.oauth.kakao import KakaoOAuthProvider, KakaoOAuthError
from app.services.oauth.naver import NaverOAuthProvider, NaverOAuthError

router = APIRouter(prefix="/auth/test", tags=["OAuth Test"])
logger = logging.getLogger(__name__)


def _base(request: Request) -> str:
    """localhost ↔ Render 배포 모두 동작하는 base URL 반환.
    Render는 reverse proxy를 쓰므로 X-Forwarded-Proto 헤더로 scheme을 보정한다."""
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.url.netloc)
    return f"{scheme}://{host}"


def _success_html(token_json: str, provider: str) -> str:
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>로그인 성공</title></head>
<body style="background:#0d1117;color:#e6edf3;font-family:sans-serif;display:flex;
             justify-content:center;align-items:center;height:100vh;">
<div style="text-align:center">
  <h2 style="color:#3fb950">로그인 성공!</h2>
  <p id="msg">잠시 후 이동합니다...</p>
</div>
<script>
  const token = {token_json};
  localStorage.setItem('singchronize_jwt', token);

  if (window.opener && !window.opener.closed) {{
    // 팝업으로 열린 경우: 부모 창에 토큰 전달 후 닫기
    try {{
      window.opener.postMessage({{ type: '{provider.upper()}_LOGIN', token }}, '*');
    }} catch(e) {{}}
    setTimeout(() => window.close(), 300);
  }} else {{
    // 현재 창에서 직접 OAuth 진행한 경우 (팝업 차단 등): admin.html 로 이동
    window.location.replace('/admin.html');
  }}
</script>
</body></html>"""


def _error_html(message: str) -> str:
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>로그인 실패</title></head>
<body style="background:#0d1117;color:#e6edf3;font-family:sans-serif;display:flex;
             justify-content:center;align-items:center;height:100vh;">
<div style="text-align:center">
  <h2 style="color:#f85149">로그인 실패</h2>
  <p>{message}</p>
  <button onclick="window.close()"
    style="padding:10px 20px;border:none;border-radius:6px;
           background:#7c3aed;color:#fff;cursor:pointer;margin-top:16px;">닫기</button>
</div>
</body></html>"""


# ── 카카오 ────────────────────────────────────────────────────────

@router.get("/kakao/login", summary="카카오 로그인 (어드민)")
async def kakao_login(request: Request):
    redirect_uri = f"{_base(request)}/auth/test/kakao/callback"
    url = (
        f"https://kauth.kakao.com/oauth/authorize"
        f"?client_id={settings.KAKAO_REST_API_KEY}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
    )
    return RedirectResponse(url=url)


@router.get("/kakao/callback", summary="카카오 콜백 (어드민)")
async def kakao_callback(
    request: Request,
    code: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    redirect_uri = f"{_base(request)}/auth/test/kakao/callback"
    try:
        kakao = KakaoOAuthProvider()
        kakao_token = await kakao.get_access_token(code, redirect_uri)
        auth = AuthService(db)
        user, access_token, _, is_new = await auth.social_login(
            provider="kakao", access_token=kakao_token
        )
        logger.info("어드민 카카오 로그인: user=%s new=%s", user.id, is_new)
        return HTMLResponse(_success_html(json.dumps(access_token), "kakao"))
    except KakaoOAuthError as e:
        logger.error("카카오 OAuth 에러: %s", e.message)
        return HTMLResponse(_error_html(e.message), status_code=401)


# ── 네이버 ────────────────────────────────────────────────────────

@router.get("/naver/login", summary="네이버 로그인 (어드민)")
async def naver_login(request: Request):
    redirect_uri = f"{_base(request)}/auth/test/naver/callback"
    url = (
        f"https://nid.naver.com/oauth2.0/authorize"
        f"?client_id={settings.NAVER_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&state=singchronize_admin"
    )
    return RedirectResponse(url=url)


@router.get("/naver/callback", summary="네이버 콜백 (어드민)")
async def naver_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(default=""),
    db: AsyncSession = Depends(get_db),
):
    redirect_uri = f"{_base(request)}/auth/test/naver/callback"
    try:
        naver = NaverOAuthProvider()
        naver_token = await naver.get_access_token(code, redirect_uri)
        auth = AuthService(db)
        user, access_token, _, is_new = await auth.social_login(
            provider="naver", access_token=naver_token
        )
        logger.info("어드민 네이버 로그인: user=%s new=%s", user.id, is_new)
        return HTMLResponse(_success_html(json.dumps(access_token), "naver"))
    except NaverOAuthError as e:
        logger.error("네이버 OAuth 에러: %s", e.message)
        return HTMLResponse(_error_html(e.message), status_code=401)
