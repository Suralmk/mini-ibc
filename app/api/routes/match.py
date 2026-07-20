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
    )
    return _response()


@router.post("/goal", response_model=MatchStateResponse)
def add_goal(req: GoalRequest):
    try:
        state = match_store.add_goal(req.side)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if req.announce:
        team = state.home_team if req.side == "home" else state.away_team
        graphics_store.set(
            GraphicRequest(text=f"GOAL {team}", duration=3.5, style="pulse")
        )

    return _response()
