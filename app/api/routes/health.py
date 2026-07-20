from fastapi import APIRouter

from app.services.graphics_store import graphics_store
from app.services.match_store import match_store

router = APIRouter()


@router.get("/health")
def health():
    g = graphics_store.get()
    m = match_store.get()
    return {
        "status": "ok",
        "role": "mini-ipc",
        "home": m.home_team,
        "away": m.away_team,
        "score": m.score_line(),
        "home_score": m.home_score,
        "away_score": m.away_score,
        "graphic_active": g is not None,
    }
