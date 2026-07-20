from fastapi import APIRouter

from app.api.routes import graphics, health, match, stream

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(stream.router, tags=["stream"])
api_router.include_router(graphics.router, tags=["graphics"])
api_router.include_router(match.router, tags=["match"])
