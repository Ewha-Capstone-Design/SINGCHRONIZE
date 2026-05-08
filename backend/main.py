"""SINGCHRONIZE API 서버"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import auth, user, songs, library, busking, recommendations, singers
from app.utils.aws import configure_s3_cors
from app.routers.analysis import router as analysis_router
from app.routers.home import router as home_router
from app.routers.oauth_test import router as oauth_test_router
from app.routers.onboarding import router as onboarding_router
from app.routers.artist_actions import router as artist_actions_router
from app.routers.recorded_busking import router as recorded_busking_router
from fastapi.staticfiles import StaticFiles



@asynccontextmanager
async def lifespan(app: FastAPI):
    # await init_db()
    configure_s3_cors(settings.allowed_origins_list)
    yield


app = FastAPI(
    title="SINGCHRONIZE",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(user.router)
app.include_router(songs.router)
app.include_router(library.router)
app.include_router(busking.router)
app.include_router(recommendations.router)
app.include_router(singers.router)
app.include_router(analysis_router)
app.include_router(home_router)
app.include_router(onboarding_router)
app.include_router(oauth_test_router)
app.include_router(artist_actions_router)
app.include_router(recorded_busking_router)

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "ok"}


# 테스트용 HTML 파일만 서빙 (루트 디렉토리 노출 방지)
app.mount("/", StaticFiles(directory="static", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
