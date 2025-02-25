from app.api.routes import login, summaries, users, videos
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(summaries.router)
api_router.include_router(videos.router)
