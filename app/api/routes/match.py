from fastapi import APIRouter, HTTPException

from app.schemas.graphics import GraphicRequest
from app.schemas.match import GoalRequest, MatchStateResponse, MatchUpdateRequest
from app.services.graphics_store import graphics_store
from app.services.match_store import match_store

router = APIRouter(prefix="/match")


def _response() -> MatchStateResponse:
    s = match_store.get()
    return MatchStateResponse(
        home_team=s.home_team,
        away_team=s.away_team,
        home_score=s.home_score,
        away_score=s.away_score,
        score=s.score_line(),
        period=s.period,
        clock_minute=s.clock_minute,
        stoppage=s.stoppage,
        clock=s.clock_display(),
        clock_running=s.clock_running,
    )


@router.get("", response_model=MatchStateResponse)
def get_match():
    return _response()


@router.patch("", response_model=MatchStateResponse)
def update_match(req: MatchUpdateRequest):
    match_store.update(
        home_team=req.home_team,
        away_team=req.away_team,
        home_score=req.home_score,
        away_score=req.away_score,
        period=req.period,
        clock_minute=req.clock_minute,
        stoppage=req.stoppage,
    )
    return _response()


@router.post("/start", response_model=MatchStateResponse)
def start_match():
    """Start / resume the live scorebug clock from 0:00 (or current elapsed)."""
    match_store.start_clock()
    return _response()


@router.post("/pause", response_model=MatchStateResponse)
def pause_match():
    match_store.pause_clock()
    return _response()


@router.post("/reset-clock", response_model=MatchStateResponse)
def reset_match_clock():
    match_store.reset_clock()
    return _response()


@router.post("/goal", response_model=MatchStateResponse)
def add_goal(req: GoalRequest):
    try:
        match_store.add_goal(req.side)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if req.announce:
        graphics_store.set(
            GraphicRequest(kind="title", text="GOAL", duration=3.5, style="pulse")
        )

    return _response()
