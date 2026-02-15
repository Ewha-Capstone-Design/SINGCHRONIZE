"""SINGCHRONIZE API 서버"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import auth, user, songs, library, busking
from app.routers.oauth_test import router as oauth_test_router
from fastapi.staticfiles import StaticFiles



@asynccontextmanager
async def lifespan(app: FastAPI):
    # await init_db()
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
app.include_router(oauth_test_router)
app.mount("/", StaticFiles(directory=".", html=True), name="static")


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
